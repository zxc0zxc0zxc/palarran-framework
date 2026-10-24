"""Offline gateway/reducer checks; SDK sandbox checks do not prove server replay."""
import asyncio
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

from packages.core.coordination.share import ShareError, create
from packages.core.coordination.share_temporal import (
    ShareTemporalGateway, TASK_QUEUE, WORKFLOW_NAME, creation, fingerprint,
    transition, validate_creation, workflow_id,
)

NOW = 1000
TOKEN_A, TOKEN_B, TOKEN_C = 'alice-token-' * 4, 'bob-token-' * 4, 'carol-token-' * 4
CREDENTIALS = {TOKEN_A: dict(actor='alice', projects=['repo'], role='operator'),
               TOKEN_B: dict(actor='bob', projects=['repo'], role='agent'),
               TOKEN_C: dict(actor='carol', projects=['other'], role='agent')}


def offer():
    return dict(share_id='share1', task_id='task1', run_id='run1', repository='repo',
                room='feature1', mode='new', plan_hash='a' * 64, base_commit='b' * 40,
                expires_at=NOW + 100, backend='temporal',
                card=dict(goal='Implement endpoint', outcome='Verified change', estimate='Small',
                          uncertainties=[], tools=['git'], data_categories=['source'], checks=['unit']),
                scope=dict(files=['app.py'], resources=[], actions=['edit'], contracts=['api-v1']),
                limits=dict(tokens=1000, cost_micros=1000, seconds=60))


def event(kind, data=None, generation=0, event_id=None):
    return dict(event_id=event_id or kind, kind=kind, assignment_generation=generation,
                plan_hash='a' * 64, data=data or {})


def sequence():
    return [
        ('bob', event('offered', dict(offer_id='bob-offer', limits=offer()['limits']))),
        ('alice', event('assigned', dict(offer_id='bob-offer'))),
        ('alice', event('plan_proposed')),
        ('bob', event('plan_accepted')),
        ('bob', event('receiver_ready', dict(commit='b' * 40, evidence_sha256='c' * 64,
                                           session_id='session2', local_run_id='run2'))),
        ('alice', event('ownership_transferred', dict(stopped=True, unknown_operations=False,
            usage_known=True, tokens=20, cost_micros=20, evidence_sha256='c' * 64))),
        ('bob', event('started', dict(session_id='session2', local_run_id='run2'), 1)),
        ('bob', event('result_submitted', dict(subject='d' * 40, evidence_sha256='e' * 64,
            checks={'unit': 'PASS'}, usage_known=True, tokens=50, cost_micros=50, stopped=True), 1)),
        ('alice', event('accepted', dict(subject='d' * 40, evidence_sha256='f' * 64,
                                        independent=True), 1)),
    ]


class AlreadyStarted(Exception):
    pass


class FakeHandle:
    def __init__(self, request):
        self.request = copy.deepcopy(request)
        self.state = validate_creation(request, NOW)[1]
        self.updates = []
        self.fail_query = False
        self.fail_update_after_commit = False
        self.result_override = None

    async def query(self, name, **kwargs):
        if self.fail_query:
            raise RuntimeError('password must not leak')
        return copy.deepcopy(self.request if name == 'envelope' else
                             dict(state=self.state, deadline_elapsed=False))

    async def execute_update(self, name, command, **kwargs):
        self.updates.append((name, copy.deepcopy(command), kwargs))
        self.state = transition(self.state, self.request, command, NOW + 1)
        if self.fail_update_after_commit:
            raise RuntimeError('secret unknown response')
        return self.result_override or dict(state=copy.deepcopy(self.state), deadline_elapsed=False)


class FakeClient:
    def __init__(self):
        self.handles = {}
        self.starts = []
        self.fail_start = False

    async def start_workflow(self, name, request, **kwargs):
        self.starts.append((name, copy.deepcopy(request), kwargs))
        if kwargs['id'] in self.handles:
            raise AlreadyStarted()
        self.handles[kwargs['id']] = FakeHandle(request)
        if self.fail_start:
            raise RuntimeError('unknown with secret')
        return self.handles[kwargs['id']]

    def get_workflow_handle(self, wid):
        return self.handles[wid]


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = FakeClient()
        self.gateway = ShareTemporalGateway(self.client, CREDENTIALS,
                                             already_started=AlreadyStarted, clock=lambda: NOW)

    async def start(self):
        return await self.gateway.create(TOKEN_A, 'repo', offer(), confirmed=True)

    async def test_inherits_profile_without_per_share_backend_override(self):
        from types import SimpleNamespace
        from packages.core.parallelism.temporal import TemporalBackend
        profile = SimpleNamespace(enabled=True, connection_mapping=lambda: {'address': '127.0.0.1:7233'})
        backend = SimpleNamespace(client=self.client, already_started=AlreadyStarted, reject_duplicate=3)
        with patch('packages.core.setup.temporal_config.resolve', return_value=profile) as resolve, \
             patch.object(TemporalBackend, 'connect', new=AsyncMock(return_value=backend)) as connect:
            gateway = await ShareTemporalGateway.connect(Path('/target'), CREDENTIALS, home=Path('/owner'))
        resolve.assert_called_once_with(Path('/target'), home=Path('/owner'))
        connect.assert_awaited_once_with({'address': '127.0.0.1:7233'})
        self.assertIs(gateway.client, self.client)
        with patch('packages.core.setup.temporal_config.resolve', return_value=SimpleNamespace(enabled=False)), \
             patch.object(TemporalBackend, 'connect', new=AsyncMock()) as connect:
            with self.assertRaisesRegex(ShareError, 'backend_mismatch'):
                await ShareTemporalGateway.connect(Path('/target'), CREDENTIALS)
            connect.assert_not_awaited()

    async def test_identity_scope_and_confirmation_precede_start(self):
        for token, project, code in [('bad', 'repo', 'unauthorized'),
                                      (TOKEN_C, 'repo', 'forbidden')]:
            with self.assertRaisesRegex(ShareError, code):
                await self.gateway.create(token, project, offer(), confirmed=True)
        with self.assertRaisesRegex(ShareError, 'confirmation_required'):
            await self.gateway.create(TOKEN_A, 'repo', offer())
        self.assertEqual(self.client.starts, [])
        self.assertEqual((await self.start())['state']['sender'], 'alice')
        serialized = json.dumps(self.client.starts[0][1])
        self.assertNotIn(TOKEN_A, serialized)
        self.assertNotIn(TOKEN_B, serialized)
        self.assertEqual(self.client.starts[0][2]['task_queue'], TASK_QUEUE)

    async def test_backend_is_immutable_and_no_local_fallback(self):
        value = offer(); value['backend'] = 'local'
        with self.assertRaisesRegex(ShareError, 'backend_mismatch'):
            await self.gateway.create(TOKEN_A, 'repo', value, confirmed=True)
        self.assertEqual(self.client.starts, [])

    async def test_duplicate_creation_requires_identical_envelope(self):
        original = await self.start()
        self.assertEqual(await self.start(), original)
        value = offer(); value['card']['goal'] = 'Different task'
        with self.assertRaisesRegex(ShareError, 'share_conflict'):
            await self.gateway.create(TOKEN_A, 'repo', value, confirmed=True)
        self.assertEqual(self.client.starts[0][2]['id_reuse_policy'], 3)

    async def test_unknown_start_can_be_queried_without_restarting(self):
        self.client.fail_start = True
        with self.assertRaisesRegex(ShareError, '^temporal_start_unknown$'):
            await self.start()
        result = await self.gateway.status(TOKEN_B, 'repo', 'share1')
        self.assertEqual(result['state']['status'], 'requested')
        self.assertEqual(len(self.client.starts), 1)

    async def test_project_isolation_on_query_and_event(self):
        await self.start()
        with self.assertRaisesRegex(ShareError, 'forbidden'):
            await self.gateway.status(TOKEN_C, 'repo', 'share1')
        with self.assertRaisesRegex(ShareError, 'forbidden'):
            await self.gateway.event(TOKEN_C, 'repo', 'share1', sequence()[0][1], confirmed=True)

    async def test_completed_updates_identity_dedup_and_conflicting_reuse(self):
        await self.start()
        item = sequence()[0][1]
        with self.assertRaisesRegex(ShareError, 'confirmation_required'):
            await self.gateway.event(TOKEN_B, 'repo', 'share1', item)
        result = await self.gateway.event(TOKEN_B, 'repo', 'share1', item, confirmed=True)
        self.assertEqual(result['state']['offers']['bob-offer']['actor'], 'bob')
        handle = next(iter(self.client.handles.values()))
        self.assertEqual(handle.updates[0][2]['id'], 'offered')
        await self.gateway.event(TOKEN_B, 'repo', 'share1', item, confirmed=True)
        self.assertEqual(len(handle.updates), 1)
        conflicting = copy.deepcopy(item); conflicting['data']['offer_id'] = 'different'
        with self.assertRaisesRegex(ShareError, 'idempotency_conflict'):
            await self.gateway.event(TOKEN_B, 'repo', 'share1', conflicting, confirmed=True)

    async def test_lost_update_response_reconciles_without_replay(self):
        await self.start()
        handle = next(iter(self.client.handles.values()))
        handle.fail_update_after_commit = True
        item = sequence()[0][1]
        with self.assertRaisesRegex(ShareError, '^temporal_update_unknown$'):
            await self.gateway.event(TOKEN_B, 'repo', 'share1', item, confirmed=True)
        state = (await self.gateway.status(TOKEN_A, 'repo', 'share1'))['state']
        self.assertEqual(state['events']['offered'], fingerprint(item, 'bob'))
        await self.gateway.event(TOKEN_B, 'repo', 'share1', item, confirmed=True)
        self.assertEqual(len(handle.updates), 1)

    async def test_sdk_dedup_result_cannot_mask_concurrent_conflicting_event(self):
        await self.start()
        handle = next(iter(self.client.handles.values()))
        invalid = copy.deepcopy(handle.state); invalid['events']['offered'] = 'f' * 64
        handle.result_override = dict(state=invalid, deadline_elapsed=False)
        with self.assertRaisesRegex(ShareError, 'idempotency_conflict'):
            await self.gateway.event(TOKEN_B, 'repo', 'share1', sequence()[0][1], confirmed=True)

    async def test_query_failure_is_sanitized_not_absence(self):
        await self.start()
        next(iter(self.client.handles.values())).fail_query = True
        with self.assertRaisesRegex(ShareError, '^temporal_query_unknown$'):
            await self.gateway.status(TOKEN_A, 'repo', 'share1')

    async def prepare_rework(self):
        await self.start()
        for actor, item in sequence()[:-1]:
            await self.gateway.event(TOKEN_A if actor == 'alice' else TOKEN_B,
                                     'repo', 'share1', item, confirmed=True)
        await self.gateway.event(TOKEN_A, 'repo', 'share1',
            event('rework_requested', {'evidence_sha256': 'f' * 64}, 1), confirmed=True)
        value = offer(); value.update(share_id='share2', previous_share_id='share1')
        return value

    async def test_linked_rework_preserves_prior_usage_and_compact_lineage(self):
        value = await self.prepare_rework()
        result = await self.gateway.create(TOKEN_A, 'repo', value, confirmed=True)
        self.assertEqual(result['state']['prior_usage']['share1']['bob']['tokens'], 50)
        self.assertEqual(result['state']['prior_usage']['share1']['alice']['tokens'], 20)
        request = self.client.starts[-1][1]
        self.assertEqual(request['predecessor']['status'], 'rework_requested')
        self.assertNotIn('card', request['predecessor'])
        self.assertNotIn('events', request['predecessor'])
        self.assertEqual(len(request['predecessor']['state_sha256']), 64)
        self.assertEqual(validate_creation(request, NOW)[1], result['state'])

    async def test_link_rejects_active_predecessor_and_other_owner(self):
        await self.start()
        value = offer(); value.update(share_id='share2', previous_share_id='share1')
        with self.assertRaisesRegex(ShareError, 'previous_share_active'):
            await self.gateway.create(TOKEN_A, 'repo', value, confirmed=True)
        handle = next(iter(self.client.handles.values()))
        handle.state['status'] = 'cancelled'
        with self.assertRaisesRegex(ShareError, 'previous_share_active'):
            await self.gateway.create(TOKEN_B, 'repo', value, confirmed=True)
        self.assertEqual(len(self.client.starts), 1)

    async def test_link_rejects_different_repository_task_run_and_self(self):
        value = await self.prepare_rework()
        for key in ('repository', 'task_id', 'run_id'):
            changed = copy.deepcopy(value); changed[key] = 'different'
            with self.assertRaisesRegex(ShareError, 'lineage_mismatch'):
                await self.gateway.create(TOKEN_A, 'repo', changed, confirmed=True)
        value['previous_share_id'] = 'share2'
        with self.assertRaisesRegex(ShareError, 'lineage_mismatch'):
            await self.gateway.create(TOKEN_A, 'repo', value, confirmed=True)

    async def test_link_caps_inherited_history_without_dropping_unknown_spend(self):
        value = await self.prepare_rework()
        prior = self.client.handles[workflow_id('repo', 'share1')]
        prior.state['usage']['bob'] = dict(usage_known=False, tokens=50, cost_micros=None)
        prior.state['prior_usage'] = {'old'+str(i): {} for i in range(7)}
        result = await self.gateway.create(TOKEN_A, 'repo', value, confirmed=True)
        self.assertEqual(len(result['state']['prior_usage']), 8)
        self.assertIsNone(result['state']['prior_usage']['share1']['bob']['cost_micros'])
        self.assertFalse(result['state']['prior_usage']['share1']['bob']['usage_known'])
        prior.state['prior_usage']['old7'] = {}
        value['share_id'] = 'share3'
        with self.assertRaisesRegex(ShareError, 'capacity_exhausted'):
            await self.gateway.create(TOKEN_A, 'repo', value, confirmed=True)

    async def test_full_consent_handoff_result_and_independent_acceptance(self):
        await self.start()
        for actor, item in sequence():
            token = TOKEN_A if actor == 'alice' else TOKEN_B
            result = await self.gateway.event(token, 'repo', 'share1', item, confirmed=True)
        self.assertEqual(result['state']['status'], 'accepted')
        self.assertEqual(result['state']['assignment_generation'], 1)
        self.assertEqual(result['state']['usage']['bob']['tokens'], 50)


class DeterminismTests(unittest.TestCase):
    def test_replay_accepted_events_after_serialized_state_restore(self):
        # Reducer replay, not a fabricated Temporal server recovery claim.
        request, initial = validate_creation(creation('repo', offer(), 'alice', True), NOW)
        uninterrupted = initial
        journal = []
        for index, (actor, item) in enumerate(sequence()):
            command = dict(project='repo', share_id='share1', actor=actor, event=item, confirmed=True)
            at = NOW + index + 1
            uninterrupted = transition(uninterrupted, request, command, at)
            journal.append((command, at))
        restored = json.loads(json.dumps(initial))
        for command, at in json.loads(json.dumps(journal)):
            restored = transition(restored, request, command, at)
        self.assertEqual(restored, uninterrupted)
        midway = initial
        for command, at in journal[:5]:
            midway = transition(midway, request, command, at)
        midway = json.loads(json.dumps(midway))
        for command, at in journal[5:]:
            midway = transition(midway, request, command, at)
        self.assertEqual(midway, uninterrupted)

    def test_expiry_and_stale_generation_fence_before_mutation(self):
        request, initial = validate_creation(creation('repo', offer(), 'alice', True), NOW)
        actor, item = sequence()[0]
        command = dict(project='repo', share_id='share1', actor=actor, event=item, confirmed=True)
        with self.assertRaisesRegex(ShareError, 'expired'):
            transition(initial, request, command, NOW + 100)
        command['event']['assignment_generation'] = 1
        with self.assertRaisesRegex(ShareError, 'stale_generation'):
            transition(initial, request, command, NOW + 1)
        self.assertEqual(initial['events'], {})

    def test_no_caller_identity_in_event_payload(self):
        request, initial = validate_creation(creation('repo', offer(), 'alice', True), NOW)
        actor, item = sequence()[0]
        item['actor'] = 'alice'
        with self.assertRaises(ShareError):
            transition(initial, request, dict(project='repo', share_id='share1', actor=actor,
                       event=item, confirmed=True), NOW + 1)


@unittest.skipUnless(importlib.util.find_spec('temporalio'), 'optional SDK not installed')
class RealSDKTests(unittest.IsolatedAsyncioTestCase):
    async def test_workflow_waits_for_explicit_events_and_preserves_expired_pending_owner(self):
        from datetime import datetime, timezone
        from packages.core.coordination import share_temporal_worker as module
        instance = module.ShareWorkflow()
        waits = []
        async def wait(predicate, **kwargs):
            waits.append(kwargs)
            if len(waits) == 1:
                self.assertEqual(instance.state['status'], 'requested')
                raise TimeoutError()
            if len(waits) == 2:
                self.assertTrue(instance.deadline_elapsed)
                self.assertEqual(instance.state['owner'], 'alice')
                for item in [event('cancel_requested'), event('cancelled', dict(stopped=True,
                        usage_known=True, tokens=0, cost_micros=0, evidence_sha256='e' * 64))]:
                    command = dict(project='repo', share_id='share1', event=item,
                                   actor='alice', confirmed=False)
                    instance.validate_update(command)
                    result = instance.update(command)
                self.assertEqual(result['state']['status'], 'cancelled')
            self.assertTrue(predicate())
        with patch.object(module.workflow, 'now', return_value=datetime.fromtimestamp(NOW, timezone.utc)), \
             patch.object(module.workflow, 'wait_condition', side_effect=wait), \
             patch.object(module.workflow, 'all_handlers_finished', return_value=True):
            result = await instance.run(creation('repo', offer(), 'alice', True))
        self.assertEqual(result['state']['status'], 'cancelled')
        self.assertTrue(result['deadline_elapsed'])
        self.assertEqual(waits[0]['timeout'].total_seconds(), 100)

    async def test_actual_sdk_sandbox_and_update_query_registration(self):
        from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner
        from temporalio.workflow import _Definition
        from packages.core.coordination.share_temporal_worker import ShareWorkflow
        definition = _Definition.must_from_class(ShareWorkflow)
        SandboxedWorkflowRunner().prepare_workflow(definition)
        self.assertEqual(definition.name, WORKFLOW_NAME)
        self.assertEqual(set(definition.updates), {'transition'})
        self.assertEqual(set(definition.queries), {'envelope', 'status'})
        self.assertEqual(definition.signals, {})


if __name__ == '__main__':
    unittest.main()
