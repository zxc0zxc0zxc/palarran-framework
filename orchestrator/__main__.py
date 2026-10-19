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


def main(argv=None):
    parser = argparse.ArgumentParser(description='Bounded local engineering workflow runtime')
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('create', 'work', 'status', 'events', 'export', 'cancel', 'resolve'):
        p = sub.add_parser(command)
        p.add_argument('--state', required=True, type=Path)
        if command == 'create':
            p.add_argument('--workflow', required=True, type=Path)
            p.add_argument('--target', required=True, type=Path)
        else:
            p.add_argument('--run', required=True)
        if command == 'resolve':
            p.add_argument('--task', required=True)
            p.add_argument('--reason', required=True)
            p.add_argument('--processes-stopped', action='store_true')
    p = sub.add_parser('product-create', help='Create a bounded product research pipeline without executing it')
    p.add_argument('--state', required=True, type=Path)
    p.add_argument('--target', required=True, type=Path)
    p.add_argument('--idea-file', required=True, type=Path)
    p.add_argument('--skills-root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--adapter', required=True, choices=['codex', 'claude'])
    p.add_argument('--agent', required=True)
    p.add_argument('--ai-policy', type=Path, help='Reviewed model routing and launch allocations JSON')
    p.add_argument('--run-seconds', type=float, default=7200)
    p.add_argument('--task-seconds', type=float, default=900)
    p.add_argument('--max-attempts', type=int, default=2)
    args = parser.parse_args(argv)
    try:
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
            if args.ai_policy is not None:
                fd = os.open(str(args.ai_policy), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, 'rb') as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError('Regular policy file required')
                    payload = stream.read(65537)
                if len(payload) > 65536:
                    raise ValueError('Policy exceeds byte budget')
                options['ai_policy'] = json.loads(payload)
                if not isinstance(options['ai_policy'], dict):
                    raise ValueError('AI policy object required')
            run = create_product(args.state, idea, args.target, args.skills_root, args.adapter, args.agent, limits=dict(run_seconds=args.run_seconds, task_seconds=args.task_seconds, max_attempts=args.max_attempts), **options)
            print(json.dumps({'run_id': run, 'budget': status(args.state, run)['budget']})); return 0
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
        elif args.command in ('cancel', 'resolve'):
            with closing(_store(args.state)) as store:
                if args.command == 'cancel':
                    store.cancel(args.run)
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
