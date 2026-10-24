"""Common managed entry for ordinary requests and skills, with durable continuation."""
from __future__ import annotations
import hashlib
import json


def _digest(manifest):
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def start(dispatcher, manifest, profile, *, origin='ordinary', reviewed=False, active_run_id=None):
    if origin not in ('ordinary', 'skill') or reviewed is not True:
        raise ValueError('Managed entry requires a reviewed task manifest and known origin')
    if type(manifest) is not dict:
        raise ValueError('A reviewed manifest is required; raw prompts are not executable plans')
    if active_run_id is not None:
        run = dispatcher.get_run(active_run_id)
        if manifest.get('run_id') != active_run_id:
            raise ValueError('Continuation must retain the existing run identity')
        # create_run is idempotent and verifies the immutable manifest/backend.
        dispatcher.create_run(manifest, backend=run['backend'])
        return dict(run_id=active_run_id, backend=run['backend'], origin=origin, continuation=True)
    backend = profile.backend
    run_id = dispatcher.create_run(manifest, backend=backend)
    return dict(run_id=run_id, backend=backend, origin=origin, continuation=False)


def execute(dispatcher, entry, adapter, verifier, *, temporal_submit=None):
    """An unavailable selected engine never falls back to a local launch."""
    run = dispatcher.get_run(entry['run_id'])
    if run['backend'] == 'temporal':
        if temporal_submit is None:
            return dict(run_id=entry['run_id'], backend='temporal', status='UNAVAILABLE', local_launches=0)
        try:
            return temporal_submit(entry['run_id'])
        except Exception:
            # Start outcome can be unknown; inspect the fixed run ID before retry.
            return dict(run_id=entry['run_id'], backend='temporal', status='unknown', local_launches=0)
    return dispatcher.run_local(entry['run_id'], adapter, verifier)
