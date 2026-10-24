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


def execute(dispatcher, entry, adapter, verifier, *, temporal_submit=None, integration_factory=None):
    """An unavailable selected engine never falls back to a local launch."""
    run = dispatcher.get_run(entry['run_id'])
    if integration_factory is not None and _implementation_verified(run):
        return _integrate(dispatcher, entry['run_id'], integration_factory)
    if run['backend'] == 'temporal':
        if temporal_submit is None:
            return dict(run_id=entry['run_id'], backend='temporal', status='UNAVAILABLE', local_launches=0)
        try:
            return temporal_submit(entry['run_id'])
        except Exception:
            # Start outcome can be unknown; inspect the fixed run ID before retry.
            return dict(run_id=entry['run_id'], backend='temporal', status='unknown', local_launches=0)
    result = dispatcher.run_local(entry['run_id'], adapter, verifier)
    if integration_factory is not None and _implementation_verified(result):
        return _integrate(dispatcher, entry['run_id'], integration_factory)
    return result


def _implementation_verified(report):
    return (report.get('status') not in ('unknown', 'cancel_requested', 'cancelled', 'failed')
            and all(t['state'] == 'verified' for t in report['tasks'] if t.get('dispatch_mode', 'auto') == 'auto'))


def _integrate(dispatcher, run_id, factory):
    """Trusted coordinator binding; never publish or replay an unknown operation."""
    if not callable(factory):
        raise ValueError('Reviewed integration factory required')
    queue = factory(dispatcher.get_run(run_id))
    report = queue.report()
    if report.get('run_id') != run_id:
        raise ValueError('Integration run mismatch')
    if report['status'] == 'pending':
        report = queue.prepare()
    for _ in range(100):
        if report['status'] != 'integrating':
            break
        if report['remaining'] == 0:
            report = queue.finalize()
            break
        report = queue.advance()
    root = dispatcher.get_run(run_id)
    ready = report.get('pr_ready') is True and root['status'] == 'verified'
    status = 'ready_pr' if ready else ('unknown' if report['status'] == 'unknown' else 'blocked')
    return dict(root, status=status, root_status=root['status'], integration_queue=report, publication='not_requested')


def run_request(dispatcher, request, *, target, binding, profile, origin='ordinary', active_run_id=None):
    """A trusted configured planner binds ordinary text to a reviewed execution plan.

    Planning itself is inside the caller's already-approved scope/budget. This API
    neither invents decomposition nor supplies a hidden model/provider connection.
    """
    from pathlib import Path
    target = Path(target).absolute()
    if not target.is_dir() or any(p.is_symlink() for p in (target,*target.parents)):
        raise ValueError('Managed target must be an existing nonsymlink directory')
    if not isinstance(request,str) or not request.strip() or len(request.encode()) > 16384 or '\x00' in request:
        raise ValueError('Managed request must be bounded nonempty text')
    if not callable(binding):
        raise ValueError('A trusted configured planning binding is required')
    context = dict(target=str(target), origin=origin, profile=profile.report(),
        active_run=dispatcher.get_run(active_run_id) if active_run_id else None)
    selected = binding(request, context)
    if not isinstance(selected,dict) or selected.get('reviewed') is not True:
        raise ValueError('Planning binding must return a reviewed execution packet')
    adapter, verifier = selected['adapter'], selected['verifier']
    if not callable(getattr(adapter,'execute',None)) or not callable(verifier):
        raise ValueError('Managed binding requires an adapter and independent verifier')
    passport = selected.get('feature_passport')
    if selected['manifest'].get('repositories') and passport is None:
        raise ValueError('Cross-repository work requires a reviewed feature passport before execution')
    run = start(dispatcher, selected['manifest'], profile, origin=origin,
                reviewed=True, active_run_id=active_run_id)
    feature = None
    if passport is not None:
        from .feature import FeatureAuthority
        feature = FeatureAuthority(dispatcher, run['run_id'])
        feature.create(passport)  # Idempotent continuation; revisions require explicit owner approval.
    if selected.get('share_hint') is not None:
        from packages.core.coordination.share_runtime import propose
        advice=propose(dispatcher,run['run_id'],plan_hash=dispatcher.get_run(run['run_id'])['plan_sha256'],
                       **selected['share_hint'])
        if advice['suggested']:
            return dict(dispatcher.get_run(run['run_id']),status='share_suggested',share_advice=advice,
                        origin=origin,continuation=run['continuation'],local_launches=0)
    result = execute(dispatcher, run, adapter, verifier, temporal_submit=selected.get('temporal_submit'), integration_factory=selected.get('integration_factory'))
    if feature is not None:
        driver = selected.get('feature_driver')
        if driver is not None:
            if not callable(driver):
                raise ValueError('Reviewed feature acceptance binding required')
            if _implementation_verified(dispatcher.get_run(run['run_id'])):
                driver(feature)  # Explicit target binding; no default tools or deployment.
        result = dict(result, feature=feature.report())
    return dict(result, integration=getattr(adapter,'integration','unsupported'), origin=origin,
                continuation=run['continuation'])


def main(argv=None):
    import argparse
    import importlib
    from pathlib import Path
    import re
    import sys
    # Direct source invocation and `python -m` use the same reviewed runtime.
    for root in Path(__file__).resolve().parents:
        if (root/'scripts/palarran_paths.py').is_file():
            sys.path.insert(0,str(root)); break
    from packages.core.parallelism.dispatcher import Dispatcher
    from packages.core.setup.temporal_config import resolve
    parser=argparse.ArgumentParser(description='Managed ordinary/skill request entry; no implicit model planner')
    parser.add_argument('--request-file',required=True,type=Path)
    parser.add_argument('--state',required=True,type=Path)
    parser.add_argument('--target',required=True,type=Path)
    parser.add_argument('--binding',required=True,help='Explicit trusted Python module:factory; no auto discovery or installation')
    parser.add_argument('--origin',choices=('ordinary','skill'),default='ordinary')
    parser.add_argument('--active-run-id')
    args=parser.parse_args(argv)
    try:
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*',args.binding):
            raise ValueError('Invalid trusted binding reference')
        request_path=args.request_file.absolute()
        if any(p.is_symlink() for p in (request_path,*request_path.parents)) or not request_path.is_file() or request_path.stat().st_size>16384:
            raise ValueError('Invalid request file')
        # Resolve configuration before importing executable planner code.
        profile=resolve(args.target)
        module,attribute=args.binding.split(':')
        binding=getattr(importlib.import_module(module),attribute)
        report=run_request(Dispatcher(args.state),request_path.read_text(encoding='utf-8'),
            target=args.target,binding=binding,profile=profile,origin=args.origin,active_run_id=args.active_run_id)
        print(json.dumps(report,sort_keys=True))
        return 0 if report.get('status') in ('verified','ready_pr') else 2
    except (ValueError,TypeError,KeyError,AttributeError,OSError,ImportError):
        print(json.dumps({'status':'BLOCKED','reason':'Check trusted binding, profile, manifest and existing run; no automatic retry.'}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
