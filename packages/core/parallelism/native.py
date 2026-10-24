"""Reviewed Codex/Claude CLI bindings using existing bounded transport/accounting.

Native CLI tool access and nested delegation remain instruction-based, not an OS
sandbox. A binding is explicit operator integration code, never a task-supplied
executable or a credential copied from a project environment.
"""
from __future__ import annotations
from pathlib import Path
import re
import threading
from packages.core.orchestration.runtime import runner
from packages.core.orchestration.runtime.accounting import priced_snapshot, amount
from .harness import unknown


class NativeHarness:
    integration = 'instruction-based'
    protocol = 'palarran.managed.v1'
    nested_delegation = False

    def __init__(self, bindings, *, authorized=False, output_limit=1048576):
        if authorized is not True or not isinstance(bindings,dict) or not bindings:
            raise ValueError('Native sessions need explicit approved per-task bindings')
        if type(output_limit) is not int or not 1024<=output_limit<=1048576:
            raise ValueError('Invalid native output limit')
        self.bindings={};self.output_limit=output_limit;self._sessions=set();self._lock=threading.Lock()
        for task_id,binding in bindings.items():
            if not isinstance(binding,dict) or set(binding)!={'adapter','executable','profile','pricing','prompt','environment','subject','authorization'}:
                raise ValueError('Incomplete native binding')
            executable=Path(binding['executable'])
            if (binding['adapter'] not in ('codex','claude') or not executable.is_absolute()
                    or not executable.is_file() or executable.is_symlink()):
                raise ValueError('Native executable must be explicitly registered')
            profile=binding['profile']
            if (not isinstance(profile,dict) or set(profile)!={'model','effort'}
                    or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,128}',v) for v in profile.values())):
                raise ValueError('Explicit model and effort are required')
            if not isinstance(binding['prompt'],str) or not 1<=len(binding['prompt'].encode())<=16384:
                raise ValueError('Bounded explicit native prompt required')
            if not callable(binding['subject']) or not isinstance(binding['authorization'],str) or not binding['authorization']:
                raise ValueError('Native scope and exact subject callback required')
            if (not isinstance(binding['environment'],dict)
                    or any(not isinstance(k,str) or not isinstance(v,str) or '\x00' in k+v for k,v in binding['environment'].items())):
                raise ValueError('Native environment must be explicit; never implicitly inherit secrets')
            if binding['adapter']=='codex':
                card=binding['pricing']
                if not isinstance(card,dict) or any(k not in card for k in ('input','cached_input','cache_creation','output','source_url','as_of')):
                    raise ValueError('Codex needs a dated explicit price card')
                for key in ('input','cached_input','cache_creation','output'): amount(card[key])
            self.bindings[task_id]=dict(binding,profile=dict(profile),environment=dict(binding['environment']),pricing=dict(binding['pricing']))

    def execute(self,task,*,heartbeat,cancel):
        binding=self.bindings.get(task['task_id'])
        if binding is None:raise ValueError('Native task has no reviewed binding')
        session=task.get('session_id')
        if not isinstance(session,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',session):
            raise ValueError('Native session identity must be registered before launch')
        if cancel.is_set():
            return dict(status='cancelled',subject='',tokens=0,cost_micros=0,usage_known=True,stopped=True)
        # Repeat execution must reconcile the original session, never relaunch it.
        with self._lock:
            if session in self._sessions:raise ValueError('Native session already admitted; reconcile before retry')
            self._sessions.add(session)
        packet=dict(adapter=binding['adapter'],executable=binding['executable'],model_role='worker',
            prompt=binding['prompt']+'\n\nDo not spawn subagents, background workers or detached processes. Return work to the coordinator; all delegation uses its registered dispatcher. Stay within the supplied task scope.\n')
        observed={'tokens':0,'cost_micros':0};known=False
        flow=dict(ai_policy=dict(profiles=dict(worker=binding['profile'])),
            usage_policy=dict(pricing={binding['profile']['model']:binding['pricing']}))
        def on_usage(snapshot):
            nonlocal known
            priced=priced_snapshot(flow,packet,snapshot)
            observed.update(tokens=priced['total_tokens'],cost_micros=(priced['cost_nano_usd']+999)//1000)
            known=True
            return not cancel.is_set() and heartbeat(**observed) is not False
        def live():return not cancel.is_set() and heartbeat() is not False
        try:
            argv,prompt=runner.invocation(packet,task['worktree'],profile=binding['profile'],telemetry=True,
                max_cost_usd=str(task['limits']['cost_micros']/1000000),output_limit=self.output_limit)
            result=runner.execute(argv,task['worktree'],timeout=task['limits']['seconds'],
                output_limit=self.output_limit,env=binding['environment'],heartbeat=live,
                stdin_text=prompt,usage_adapter=binding['adapter'],on_usage=on_usage)
            stopped=getattr(result,'stopped',False) is True
            complete=known and result.usage_complete is True
            status='submitted' if result.returncode==0 and result.reason=='exited' and complete and stopped else 'unknown'
            if result.returncode!=0 and complete and stopped:status='cancelled' if cancel.is_set() else 'failed'
            subject=''
            if status=='submitted':
                subject=binding['subject'](task)
                if not isinstance(subject,str) or not re.fullmatch(r'[0-9a-f]{40,64}',subject):
                    status='unknown';subject=''
            return dict(status=status,subject=subject,usage_known=complete,stopped=stopped,**observed)
        except (ValueError,TypeError,KeyError,OSError):
            return dict(unknown(),**observed)
