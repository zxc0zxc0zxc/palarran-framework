"""Chat-facing local supervisor for existing reviewed dispatcher runs.

No provider is configured or launched implicitly. A trusted Python binding is
executable operator code; session output is never forwarded to the main chat.
"""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from .dispatcher import Dispatcher
from .team_journal import TeamJournal


def paths(state, run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',run_id):
        raise ValueError('Invalid run identity')
    state=Path(state).absolute()
    if any(p.is_symlink() for p in (state,*state.parents)):
        raise ValueError('State symlinks are unsupported')
    return state, state.with_name(state.name+'.teams.sqlite'), state.with_name(state.name+'.'+run_id+'.supervisor.lock')


class ObservationReader:
    """A status read never creates or migrates a missing telemetry store."""
    def __init__(self, path):
        self.path = path

    def read(self, run_id, *, after=0):
        if self.path.exists():
            return TeamJournal(self.path,read_only=True).read(run_id,after=after)
        return dict(sessions=[],supervisor=None,cursor=after,changes=[],truncated=False)


def report(dispatcher, journal, run_id, *, after=0):
    run=dispatcher.get_run(run_id)
    observed=journal.read(run_id,after=after)
    supervisor=observed['supervisor']
    if supervisor:
        supervisor=dict(supervisor,stale=supervisor['state']=='running' and time.time()-supervisor['observed_at']>6)
    tasks={t['task_id']:t for t in run['tasks']}
    with dispatcher.ledger.transaction() as db:
        goals={r['id']:json.loads(r['packet'])['goal'] for r in dispatcher.ledger.read_tasks(db,run_id)}
    sessions=[]
    active_children=0
    for session in observed['sessions']:
        task=tasks.get(session['task_id'])
        if task is None or task.get('attempt_id')!=session['attempt_id']:continue
        held=task['state'] in ('running','submitted','cancel_requested','unknown','handoff_pending')
        active=session['observed_active'] if held and not session.get('root_stopped') else 0
        active_children+=active
        sessions.append(dict(session,observed_active=active,task_state=task['state']))
    roots=sum(t['state'] in ('running','submitted','cancel_requested') for t in tasks.values())
    return dict(run_id=run_id,status=run['status'],usage=run['usage'],budget=run['budget'],
                supervisor=supervisor,
                sessions=sessions,roots_active=roots,subagents_observed_active=active_children,
                agents_observed_active=roots+active_children,
                children_discovered=sum(s['discovered'] for s in sessions),
                count_scope='observed_lower_bound',
                cost_kinds=sorted({s.get('cost_kind','unknown') for s in sessions}),
                main_chat_usage='outside_subprocess_ledger',
                configured_child_capacity_per_session=sorted({s['capacity'] for s in sessions}),
                actual_count_complete=False,
                tasks=[dict(task_id=t['task_id'],state=t['state'],owner=t['owner'],goal=goals[t['task_id']][:256]) for t in tasks.values()],
                cursor=observed['cursor'],changes=observed['changes'],truncated=observed['truncated'],
                attention=any(t['state'] in ('unknown','blocked','failed','handoff_pending') for t in tasks.values())
                    or any(s.get('needs_human') for s in sessions)
                    or bool(supervisor and (supervisor['state']=='failed' or supervisor['stale'] or (supervisor['state']=='stopped' and roots))))


def text_report(value):
    usage=value['usage']
    lines=[f"Palarran {value['run_id']}: {value['status']}",
           f"Sessions active: {value['roots_active']}; subagents observed active: {value['subagents_observed_active']}; agents observed active: {value['agents_observed_active']} (lower bound)",
           f"Reported tokens: {usage['tokens']}; reported micro-USD: {usage['cost_micros']}; usage complete: {usage['known']}",
           f"Reserved tokens: {usage['reserved_tokens']}; reserved micro-USD: {usage['reserved_cost_micros']}"]
    lines += [f"- {t['task_id']}: {t['state']} / {t['owner']} / "+''.join(c if ord(c)>=32 else ' ' for c in t['goal']) for t in value['tasks']]
    lines += [f"  {s['task_id']}: {s.get('activity','unknown')} / children observed {s['observed_active']} / capacity {s['capacity']} / {s.get('cost_kind','unknown')}" for s in value['sessions']]
    if value['attention']:lines.append('Coordinator attention required; do not replay unknown attempts.')
    return '\n'.join(lines)


def _factory(reference):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*',reference):
        raise ValueError('Invalid trusted binding')
    module,attribute=reference.split(':')
    return getattr(importlib.import_module(module),attribute)


def supervise(state, run_id, binding):
    state,telemetry,lock=paths(state,run_id)
    if lock.is_symlink():raise ValueError('Supervisor lock symlink')
    fd=os.open(str(lock),os.O_CREAT|os.O_RDWR,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        dispatcher=Dispatcher(state);run=dispatcher.get_run(run_id)
        if run['backend']!='local':raise ValueError('Local supervisor cannot replace Temporal')
        journal=TeamJournal(telemetry)
        journal.supervisor(run_id,'running',os.getpid())
        heartbeat_stop=threading.Event()
        def supervise_heartbeat():
            while not heartbeat_stop.wait(2):
                try:journal.supervisor(run_id,'running',os.getpid())
                except Exception:
                    dispatcher.cancel(run_id)
                    return
        heartbeat_thread=threading.Thread(target=supervise_heartbeat,daemon=True)
        heartbeat_thread.start()
        selected=_factory(binding)(run,journal.publish)
        from .session_teams import NativeTeamHarness
        if (type(selected) is not dict or selected.get('reviewed') is not True
                or not isinstance(selected.get('adapter'),NativeTeamHarness)
                or not callable(selected.get('verifier'))):
            raise ValueError('Reviewed native team binding and independent verifier required')
        # The adapter cannot redefine manifest, budget, ownership or source here.
        result=dispatcher.run_local(run_id,selected['adapter'],selected['verifier'],
                                    initial_workers=selected.get('initial_workers', 1))
        heartbeat_stop.set();heartbeat_thread.join(timeout=6)
        journal.supervisor(run_id,'stopped',os.getpid())
        return result
    except Exception:
        if 'heartbeat_stop' in locals():
            heartbeat_stop.set();heartbeat_thread.join(timeout=6)
        if 'journal' in locals():journal.supervisor(run_id,'failed',os.getpid())
        raise
    finally:
        if 'heartbeat_stop' in locals():
            heartbeat_stop.set();heartbeat_thread.join(timeout=6)
        os.close(fd)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','start','worker','status','watch','cancel'])
    parser.add_argument('--state',required=True,type=Path)
    parser.add_argument('--run',required=True)
    parser.add_argument('--binding')
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--authorized',action='store_true')
    parser.add_argument('--plan',action='store_true')
    parser.add_argument('--after',type=int,default=0)
    parser.add_argument('--seconds',type=float,default=30)
    parser.add_argument('--format',choices=['json','text'],default='json')
    args=parser.parse_args(argv)
    if args.plan:
        print(json.dumps(dict(status='PLAN_ONLY',launches=0,writes=0)));return 0
    try:
        state,telemetry,lock=paths(args.state,args.run)
        if args.command=='prepare':
            if not args.authorized or args.manifest is None:
                raise ValueError('Reviewed manifest and explicit authorization required')
            path=args.manifest.absolute()
            if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file() or path.stat().st_size>1048576:
                raise ValueError('Invalid reviewed manifest path')
            from .team_observer import _pairs
            manifest=json.loads(path.read_text(),object_pairs_hook=_pairs)
            if manifest.get('run_id')!=args.run:raise ValueError('Run identity mismatch')
            result=Dispatcher(state).create_run(manifest)
            print(json.dumps(dict(status='prepared',run_id=args.run,launches=0)))
            return 0
        if not state.is_file():raise ValueError('Prepare an existing reviewed dispatcher run first')
        if args.command in ('status','watch'):
            from .dashboard import LocalReport
            dispatcher=LocalReport(state)
        else:
            dispatcher=Dispatcher(state)
        run=dispatcher.get_run(args.run)
        if args.command in ('start','worker'):
            if not args.authorized or not args.binding:raise ValueError('Explicit execution authorization and binding required')
            if run['backend']!='local':raise ValueError('No local fallback for Temporal runs')
            if args.command=='worker':
                supervise(state,args.run,args.binding);return 0
            # Check spelling before launching; imports execute only in the worker.
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*',args.binding):
                raise ValueError('Invalid trusted binding')
            if run['status'] in ('unknown','verified','cancelled','failed'):
                raise ValueError('Run requires inspection/reconciliation, not automatic restart')
            command=[str(Path(sys.executable).resolve()),'-m','packages.core.parallelism.session_pool','worker','--state',str(state),
                     '--run',args.run,'--binding',args.binding,'--authorized']
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,start_new_session=True,shell=False)
            print(json.dumps(dict(status='supervisor_start_requested',run_id=args.run,pid=process.pid,
                                  next='Read status; PID is not launch or acceptance evidence.')));return 0
        if args.command=='cancel':
            if not args.authorized:raise ValueError('Explicit cancellation authorization required')
            dispatcher.cancel(args.run)
        journal=ObservationReader(telemetry)
        if args.command=='watch':
            if not 0<args.seconds<=60:raise ValueError('Watch duration must be in (0,60]')
            deadline=time.monotonic()+args.seconds;last=None;cursor=args.after
            while time.monotonic()<deadline:
                value=report(dispatcher,journal,args.run,after=cursor)
                stable={k:v for k,v in value.items() if k not in ('changes','cursor')}
                if stable['supervisor']:
                    stable['supervisor']={k:v for k,v in stable['supervisor'].items() if k!='observed_at'}
                digest=hashlib.sha256(json.dumps(stable,sort_keys=True).encode()).hexdigest()
                if digest!=last:
                    print(text_report(value) if args.format=='text' else json.dumps(value),flush=True)
                    cursor=value['cursor'];last=digest
                if value['status'] in ('verified','failed','cancelled'):break
                time.sleep(min(1,max(0,deadline-time.monotonic())))
        else:
            value=report(dispatcher,journal,args.run,after=args.after)
            print(text_report(value) if args.format=='text' else json.dumps(value))
        return 0
    except (ValueError,TypeError,KeyError,OSError,ImportError,AttributeError):
        print(json.dumps(dict(status='BLOCKED',reason='Check reviewed run, binding, permissions and current attempts; no automatic retry.')))
        return 2


if __name__=='__main__':raise SystemExit(main())
