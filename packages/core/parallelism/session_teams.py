"""Explicit headless team adapter; the existing dispatcher owns all allocations."""
from __future__ import annotations
from .native import NativeHarness, verify_worktree
from .harness import unknown
from .team_observer import TeamObserver
from packages.core.orchestration.runtime import runner
from packages.core.orchestration.runtime.accounting import priced_snapshot


class NativeTeamHarness(NativeHarness):
    """Reviewed opt-in to native children, not an OS-enforced delegation boundary."""
    nested_delegation = True
    integration = 'instruction-based'

    def __init__(self, bindings, *, max_subagents=3, authorized=False,
                 publish=None, output_limit=1048576):
        super().__init__(bindings, authorized=authorized, output_limit=output_limit)
        if type(max_subagents) is not int or not 1 <= max_subagents <= 32:
            raise ValueError('Team child capacity must be between 1 and 32')
        if not callable(publish):
            raise ValueError('Durable team observation callback required')
        self.max_subagents, self.publish = max_subagents, publish

    def execute(self, task, *, heartbeat, cancel):
        binding = self.bindings[task['task_id']]
        worktree = verify_worktree(task)
        session = task['session_id']
        with self._lock:
            if session in self._sessions or worktree in self._worktrees:
                raise ValueError('Team session already admitted; reconcile before retry')
            self._sessions.add(session); self._worktrees[worktree] = task['task_id']
        instruction = (f'\nYou are one headless team root supervised by the main chat. '
            f'Use at most {self.max_subagents} concurrent native subagents and no deeper nesting. '
            'Delegate only independent work within this task ownership, tools and total team budget. '
            'Do not start additional CLI sessions, detached processes or remote workers. '
            'Wait for children, summarize evidence, and return to the main coordinator. '
            'Do not integrate other teams or change the shared plan.\n')
        packet = dict(adapter=binding['adapter'], executable=binding['executable'],
                      model_role='worker', prompt=binding['prompt']+instruction)
        flow = dict(ai_policy=dict(profiles=dict(worker=binding['profile'])),
                    usage_policy=dict(pricing={binding['profile']['model']:binding['pricing']}))
        observed = {'tokens':0, 'cost_micros':0}
        key = dict(run_id=task['run_id'], task_id=task['task_id'], attempt_id=task['attempt_id'])
        def publish(metadata):self.publish(dict(key, **metadata))
        def usage(snapshots):
            amounts = [priced_snapshot(flow, packet, s) for s in snapshots]
            tokens = sum(x['total_tokens'] for x in amounts)
            cost = (sum(x['cost_nano_usd'] for x in amounts)+999)//1000
            if tokens < observed['tokens'] or cost < observed['cost_micros']:
                raise ValueError('Team usage cannot decrease')
            observed.update(tokens=tokens, cost_micros=cost)
            return not cancel.is_set() and heartbeat(**observed) is not False
        def partial_tokens(tokens):
            observed['tokens'] = max(observed['tokens'], tokens)
            return not cancel.is_set() and heartbeat(**observed) is not False
        observer = TeamObserver(binding['adapter'], self.max_subagents, publish, usage, partial_tokens)
        environment = dict(binding['environment'])
        stopped = False
        try:
            argv,prompt = runner.invocation(packet, worktree, profile=binding['profile'], telemetry=True,
                max_cost_usd=str(task['limits']['cost_micros']/1000000), output_limit=self.output_limit)
            if binding['adapter']=='codex':
                argv += ['-c','agents.enabled=true','-c',
                         'agents.max_concurrent_threads_per_session='+str(self.max_subagents)]
            else:
                tools = argv.index('--allowedTools')+1
                argv[tools] += ',Agent'
                environment.update(CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=str(self.max_subagents),
                                   CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH='1')
            publish(observer.report())
            result = runner.execute(argv, worktree, timeout=task['limits']['seconds'],
                output_limit=self.output_limit, env=environment,
                heartbeat=lambda: not cancel.is_set() and heartbeat() is not False,
                stdin_text=prompt, on_stdout=observer.feed)
            complete = observer.finish()
            stopped = result.stopped is True
            metadata = dict(observer.report(), root_stopped=stopped, usage_complete=complete,
                            transport_reason=result.reason)
            publish(metadata)
            known = complete and stopped
            status = 'submitted' if result.returncode==0 and result.reason=='exited' and known else 'unknown'
            if result.returncode!=0 and known:status='cancelled' if cancel.is_set() else 'failed'
            subject = binding['subject'](task) if status=='submitted' else ''
            if status=='submitted':
                import re
                if not isinstance(subject,str) or not re.fullmatch('[0-9a-f]{40,64}',subject):
                    status='unknown';subject=''
            return dict(status=status,subject=subject,usage_known=known,stopped=stopped,**observed)
        except (ValueError,TypeError,KeyError,OSError):
            return dict(unknown(stopped=stopped), **observed)
