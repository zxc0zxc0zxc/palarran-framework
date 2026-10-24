"""Optional authenticated sharing gateway; importing this does not load the SDK."""
from __future__ import annotations

import copy
from datetime import timedelta
import hashlib
import time

from .share import (CONSENT, TERMINAL, ShareError, apply, canonical, create, digest, fields,
                    ident, require, usage)
from .service import CoordinationStore

WORKFLOW_NAME = 'palarran.share.v1'
TASK_QUEUE = 'palarran-sharing'


def workflow_id(project, share_id):
    ident(project); ident(share_id)
    # No task prose or project identity is needed in the externally visible ID.
    return 'palarran-share-' + hashlib.sha256(canonical([project, share_id])).hexdigest()


def _usage_snapshot(value):
    require(type(value) is dict and len(value) <= 33)
    for actor, counters in value.items():
        ident(actor); usage(counters)


def predecessor_snapshot(project, prior, prior_envelope):
    """Compact immutable evidence from the same project's terminal authority."""
    require(prior_envelope['project'] == project, 'forbidden')
    require(prior['offer'] == prior_envelope['offer'], 'lineage_mismatch')
    return dict(share_id=prior['offer']['share_id'], sender=prior['sender'],
                status=prior['status'], repository=prior['offer']['repository'],
                task_id=prior['offer']['task_id'], run_id=prior['offer']['run_id'],
                usage=copy.deepcopy(prior['usage']), prior_usage=copy.deepcopy(prior.get('prior_usage', {})),
                state_sha256=hashlib.sha256(canonical(prior)).hexdigest())


def _inherited_usage(offer, actor, predecessor):
    previous = offer.get('previous_share_id')
    if previous is None:
        require(predecessor is None, 'lineage_mismatch')
        return None
    require(previous != offer['share_id'], 'lineage_mismatch')
    fields(predecessor, {'share_id', 'sender', 'status', 'repository', 'task_id', 'run_id',
                         'usage', 'prior_usage', 'state_sha256'})
    require(predecessor['share_id'] == previous, 'lineage_mismatch')
    require(predecessor['sender'] == actor and isinstance(predecessor['status'], str)
            and predecessor['status'] in TERMINAL,
            'previous_share_active')
    require(all(offer[key] == predecessor[key] for key in ('repository', 'task_id', 'run_id')),
            'lineage_mismatch')
    digest(predecessor['state_sha256'])
    _usage_snapshot(predecessor['usage'])
    inherited = copy.deepcopy(predecessor['prior_usage'])
    require(type(inherited) is dict and len(inherited) <= 7, 'capacity_exhausted')
    for share_id, counters in inherited.items():
        ident(share_id); _usage_snapshot(counters)
    require(previous not in inherited and offer['share_id'] not in inherited, 'lineage_mismatch')
    inherited[previous] = copy.deepcopy(predecessor['usage'])
    return inherited


def creation(project, offer, actor, confirmed, predecessor=None):
    ident(project); ident(actor)
    require(confirmed is True, 'confirmation_required')
    require(type(offer) is dict and offer.get('backend') == 'temporal', 'backend_mismatch')
    result = dict(project=project, offer=copy.deepcopy(offer), actor=actor, confirmed=True)
    _inherited_usage(offer, actor, predecessor)
    if predecessor is not None:
        result['predecessor'] = copy.deepcopy(predecessor)
    canonical(result)
    return result


def validate_creation(value, now):
    fields(value, {'project', 'offer', 'actor', 'confirmed'}, {'predecessor'})
    state = create(value['offer'], value['actor'], now)
    result = creation(value['project'], value['offer'], value['actor'], value['confirmed'],
                      value.get('predecessor'))
    inherited = _inherited_usage(result['offer'], result['actor'], result.get('predecessor'))
    if inherited is not None:
        state['prior_usage'] = inherited
        canonical(state)
    return result, state


def command(project, share_id, event, actor, confirmed):
    ident(project); ident(share_id); ident(actor)
    require(type(event) is dict)
    if event.get('kind') in CONSENT:
        require(confirmed is True, 'confirmation_required')
    require(type(confirmed) is bool)
    result = dict(project=project, share_id=share_id, event=copy.deepcopy(event), actor=actor,
                  confirmed=confirmed)
    canonical(result)
    return result


def transition(state, envelope, value, now):
    fields(value, {'project', 'share_id', 'event', 'actor', 'confirmed'})
    value = command(**value)
    require(value['project'] == envelope['project'], 'forbidden')
    require(value['share_id'] == envelope['offer']['share_id'], 'share_mismatch')
    return apply(state, value['event'], value['actor'], now)


def fingerprint(event, actor):
    return hashlib.sha256(canonical(dict(event=event, actor=actor))).hexdigest()


class ShareTemporalGateway:
    """Trusted host interface. Namespace access belongs only to this gateway/worker.

    `confirmed` is an explicit host assertion, never technical human attestation.
    Do not expose this object as a generic agent auto-approval tool.
    """
    def __init__(self, client, credentials, *, already_started=None, reject_duplicate=3,
                 clock=time.time):
        self.client = client
        self.credentials = CoordinationStore._credentials(credentials)
        self.already_started = already_started
        self.reject_duplicate = reject_duplicate
        self.clock = clock

    @classmethod
    async def connect(cls, target, credentials, *, home=None):
        from ..setup.temporal_config import resolve
        from ..parallelism.temporal import TemporalBackend
        profile = resolve(target, home=home)
        require(profile.enabled, 'backend_mismatch')
        backend = await TemporalBackend.connect(profile.connection_mapping())
        return cls(backend.client, credentials, already_started=backend.already_started,
                   reject_duplicate=backend.reject_duplicate)

    def _actor(self, token, project):
        ident(project)
        require(isinstance(token, str) and len(token) <= 512, 'unauthorized')
        principal = self.credentials.get(token)
        require(principal is not None, 'unauthorized')
        require(project in principal['projects'], 'forbidden')
        return principal['actor']

    def _handle(self, project, share_id):
        return self.client.get_workflow_handle(workflow_id(project, share_id))

    async def _query(self, handle, name):
        try:
            value = await handle.query(name, rpc_timeout=timedelta(seconds=10))
            # JSON round-trip is not needed: canonical validation bounds the result.
            canonical(value)
            return copy.deepcopy(value)
        except ShareError:
            raise
        except Exception:
            raise ShareError('temporal_query_unknown') from None

    async def create(self, token, project, offer, *, confirmed=False):
        actor = self._actor(token, project)
        require(confirmed is True, 'confirmation_required')
        create(offer, actor, int(self.clock()))  # local admission; Workflow validates again.
        predecessor = None
        if 'previous_share_id' in offer:
            require(offer['previous_share_id'] != offer['share_id'], 'lineage_mismatch')
            prior_handle = self._handle(project, offer['previous_share_id'])
            prior_envelope = await self._query(prior_handle, 'envelope')
            prior_status = await self._query(prior_handle, 'status')
            predecessor = predecessor_snapshot(project, prior_status['state'], prior_envelope)
        request = creation(project, offer, actor, confirmed, predecessor)
        wid = workflow_id(project, offer['share_id'])
        try:
            handle = await self.client.start_workflow(
                WORKFLOW_NAME, request, id=wid, task_queue=TASK_QUEUE,
                id_reuse_policy=self.reject_duplicate, rpc_timeout=timedelta(seconds=10))
        except Exception as exc:
            if self.already_started and isinstance(exc, self.already_started):
                handle = self._handle(project, offer['share_id'])
            else:
                raise ShareError('temporal_start_unknown') from None
        require(await self._query(handle, 'envelope') == request, 'share_conflict')
        return await self._query(handle, 'status')

    async def status(self, token, project, share_id):
        self._actor(token, project)
        handle = self._handle(project, share_id)
        envelope = await self._query(handle, 'envelope')
        require(envelope['project'] == project and envelope['offer']['share_id'] == share_id,
                'share_mismatch')
        return await self._query(handle, 'status')

    async def event(self, token, project, share_id, event, *, confirmed=False):
        actor = self._actor(token, project)
        request = command(project, share_id, event, actor, confirmed)
        handle = self._handle(project, share_id)
        envelope = await self._query(handle, 'envelope')
        status = await self._query(handle, 'status')
        # Local prediction only, never a second lifecycle authority.
        expected = transition(status['state'], envelope, request, int(self.clock()))
        prior = status['state']['events'].get(event['event_id'])
        if prior is not None:
            return status
        try:
            # execute_update waits for completion, not only accepted/enqueued delivery.
            result = await handle.execute_update('transition', request, id=event['event_id'],
                                                 rpc_timeout=timedelta(seconds=10))
        except Exception:
            raise ShareError('temporal_update_unknown') from None
        canonical(result)
        # SDK update-ID dedup may return an earlier result for a conflicting payload.
        require(result['state']['events'].get(event['event_id']) ==
                expected['events'][event['event_id']], 'idempotency_conflict')
        return copy.deepcopy(result)
