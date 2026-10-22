"""CLI: admission is separate from execution; output excludes raw subprocess data."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sys
import sqlite3
import os
import stat

from .engine import _store, create, status, work


def read_object(path, limit):
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Regular policy file required')
        payload = stream.read(limit+1)
    if len(payload) > limit:
        raise ValueError('Policy exceeds byte budget')
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError('JSON object required')
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description='Bounded local engineering workflow runtime')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('create', 'work', 'status', 'events', 'export', 'cancel', 'modal-recover', 'resolve', 'usage-reconcile'):
        p = sub.add_parser(command)
        p.add_argument('--state', required=True, type=Path)
        if command == 'create':
            p.add_argument('--workflow', required=True, type=Path)
            p.add_argument('--target', required=True, type=Path)
        else:
            p.add_argument('--run', required=True)
        if command in ('resolve', 'usage-reconcile'):
            p.add_argument('--task', required=True)
            p.add_argument('--reason', required=True)
            p.add_argument('--processes-stopped', action='store_true')
        if command == 'usage-reconcile':
            p.add_argument('--attempt', required=True, type=int)
            p.add_argument('--usage-file', required=True, type=Path)
    p = sub.add_parser('product-create', help='Create a bounded product research pipeline without executing it')
    p.add_argument('--state', required=True, type=Path)
    p.add_argument('--target', required=True, type=Path)
    p.add_argument('--idea-file', required=True, type=Path)
    p.add_argument('--skills-root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--adapter', required=True, choices=['codex', 'claude'])
    p.add_argument('--agent', required=True)
    p.add_argument('--usage-policy', type=Path, help='Observed token/USD budgets and immutable pricing snapshot JSON')
    p.add_argument('--ai-policy', type=Path, help='Reviewed model routing and launch allocations JSON')
    p.add_argument('--run-seconds', type=float, default=7200)
    p.add_argument('--task-seconds', type=float, default=900)
    p.add_argument('--max-attempts', type=int, default=2)
    p.add_argument('--transport', choices=['app-server'], help='Codex incremental usage transport')
    p = sub.add_parser('product-continue', help='Import verified research prefix without regenerating it')
    for name in ('state', 'target', 'source', 'skills-root', 'usage-policy'):
        p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--pipeline', required=True)
    p.add_argument('--budget-ceiling', required=True, help='Explicit original monetary ceiling; not a fresh budget')
    p.add_argument('--through', required=True, choices=['define','market','compare','revenue','acquisition'])
    p.add_argument('--route', required=True, choices=['b2b','b2c'])
    p.add_argument('--agent', required=True)
    p = sub.add_parser('ml-create', help='Prepare a bounded ML pipeline; no agents or training are executed')
    for name in ('state', 'target', 'idea-file', 'ai-policy', 'usage-policy', 'execution-policy'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--skills-root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--adapter', required=True, choices=['codex', 'claude'])
    p.add_argument('--agent', required=True)
    p.add_argument('--transport', choices=['app-server'])
    for command in ('ml-approve', 'ml-reconcile'):
        p = sub.add_parser(command)
        p.add_argument('--state', required=True, type=Path)
        p.add_argument('--run', required=True)
        if command == 'ml-approve':
            p.add_argument('--prefix-sha', required=True)
        else:
            p.add_argument('--task', required=True, choices=['ml-fit', 'ml-evaluate'])
            p.add_argument('--attempt', required=True, type=int)
            p.add_argument('--cost-usd', required=True)
            p.add_argument('--processes-stopped', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command in ('ml-approve', 'ml-reconcile'):
            from .ml_resources import approve, reconcile
            with closing(_store(args.state)) as store:
                if args.command == 'ml-approve':
                    approve(store, args.run, args.prefix_sha)
                else:
                    reconcile(store, args.run, args.task, args.attempt, args.cost_usd, args.processes_stopped)
            print(json.dumps(status(args.state, args.run), indent=2)); return 0
        if args.command == 'ml-create':
            from .ml_pipeline import create_ml
            from .product_artifacts import read_bytes
            idea = read_bytes(args.idea_file.parent.resolve(), args.idea_file.name, 32768).decode('utf-8')
            options = {'transport': args.transport} if args.transport is not None else {}
            run = create_ml(args.state, idea, args.target, args.skills_root, args.adapter, args.agent,
                            read_object(args.execution_policy, 65536), read_object(args.ai_policy, 65536),
                            read_object(args.usage_policy, 65536), **options)
            print(json.dumps(status(args.state, run), indent=2)); return 0
        if args.command == 'product-continue':
            from .product_continue import create_continuation
            run=create_continuation(args.state,args.target,args.source,args.pipeline,args.through,args.skills_root,args.agent,read_object(args.usage_policy,65536),route=args.route,budget_ceiling=args.budget_ceiling)
            print(json.dumps({'run_id':run,'budget':status(args.state,run)['budget'],'usage':status(args.state,run)['usage']}));return 0
        if args.command == 'product-create':
            from .product_pipeline import create_product
            fd = os.open(str(args.idea_file), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError('Regular idea file required')
                data = stream.read(32769)
            if len(data) > 32768:
                raise ValueError('Idea exceeds byte budget')
            idea = data.decode('utf-8')
            options = {}
            if args.transport is not None: options['transport'] = args.transport
            for name in ('ai_policy', 'usage_policy'):
                file = getattr(args, name)
                if file is not None:
                    options[name] = read_object(file, 65536)
            run = create_product(args.state, idea, args.target, args.skills_root, args.adapter, args.agent, limits=dict(run_seconds=args.run_seconds, task_seconds=args.task_seconds, max_attempts=args.max_attempts), **options)
            print(json.dumps({'run_id': run, 'budget': status(args.state, run)['budget'], 'usage': status(args.state, run)['usage']})); return 0
        if args.command == 'create':
            if args.workflow.stat().st_size > 1048576:
                raise ValueError('Workflow exceeds admission byte budget')
            payload = json.loads(args.workflow.read_text())
            print(json.dumps({'run_id': create(args.state, payload, args.target)}))
            return 0
        if args.command == 'work':
            work(args.state, args.run)
        elif args.command == 'events':
            with closing(_store(args.state)) as store:
                print(json.dumps(store.events(args.run), indent=2)); return 0
        elif args.command in ('cancel', 'modal-recover', 'resolve', 'usage-reconcile'):
            with closing(_store(args.state)) as store:
                if args.command == 'cancel':
                    remote = json.loads(store.get(args.run)['workflow']).get('ml_policy', {}).get('backend') == 'modal'
                    if not remote or store.get(args.run)['status'] not in ('cancelled', 'failed', 'verified'):
                        store.cancel(args.run)
                    from .modal_adapter import recover
                    recover(store, args.run, cancel=True)
                elif args.command == 'modal-recover':
                    from .modal_adapter import recover
                    recover(store, args.run)
                elif args.command == 'usage-reconcile':
                    store.reconcile_usage(args.run, args.task, args.attempt, read_object(args.usage_file, 4096), args.reason, args.processes_stopped)
                else:
                    store.resolve(args.run, args.task, args.reason, args.processes_stopped)
        report = status(args.state, args.run)
        print(json.dumps(report, indent=2))
        if args.command == 'work':
            return 0 if report['status'] == 'verified' else 2
        return 0
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error):
        print('Factory operation rejected; check workflow, state and trusted target configuration.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
