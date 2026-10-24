"""Optional SDK sharing Workflow. It never launches receiver work itself."""
from __future__ import annotations

import asyncio
import copy
from datetime import timedelta
from temporalio import workflow
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from .share import ShareError, TERMINAL
    from .share_temporal import (TASK_QUEUE, WORKFLOW_NAME, transition, validate_creation)


@workflow.defn(name=WORKFLOW_NAME)
class ShareWorkflow:
    def __init__(self):
        self.request = None
        self.state = None
        self.deadline_elapsed = False

    @workflow.query(name='envelope')
    def envelope(self):
        return copy.deepcopy(self.request)

    @workflow.query(name='status')
    def status(self):
        return dict(state=copy.deepcopy(self.state), deadline_elapsed=self.deadline_elapsed)

    def _next(self, command):
        if self.state is None:
            raise ShareError('not_initialized')
        return transition(self.state, self.request, command, int(workflow.now().timestamp()))

    @workflow.update(name='transition')
    def update(self, command):
        try:
            self.state = self._next(command)
        except ShareError as exc:
            raise ApplicationError(str(exc), non_retryable=True) from None
        return self.status()

    @update.validator
    def validate_update(self, command):
        try:
            self._next(command)
        except ShareError as exc:
            raise ApplicationError(str(exc), non_retryable=True) from None

    def _terminal(self):
        terminal = self.state['status'] in TERMINAL or self.state['status'] == 'rework_requested'
        return terminal and all(value['usage_known'] for value in self.state['usage'].values())

    @workflow.run
    async def run(self, request):
        try:
            self.request, self.state = validate_creation(request, int(workflow.now().timestamp()))
        except ShareError as exc:
            raise ApplicationError(str(exc), non_retryable=True) from None
        remaining = self.state['offer']['expires_at'] - int(workflow.now().timestamp())
        try:
            await workflow.wait_condition(self._terminal, timeout=timedelta(seconds=max(0, remaining)))
        except TimeoutError:
            self.deadline_elapsed = True
            # Expiry fences starts; it is not process-stop proof or owner release.
            await workflow.wait_condition(self._terminal)
        await workflow.wait_condition(workflow.all_handlers_finished)
        return self.status()


async def run_worker(profile):
    """Operator-selected profile only; private connection material stays in process."""
    from ..parallelism.temporal import TemporalBackend
    backend = await TemporalBackend.connect(profile)
    worker = Worker(backend.client, task_queue=TASK_QUEUE, workflows=[ShareWorkflow],
                    max_concurrent_workflow_tasks=16)
    await worker.run()


def main(argv=None):
    import argparse
    from pathlib import Path
    from ..setup.temporal_config import resolve
    parser = argparse.ArgumentParser(description='Run the optional task-sharing Temporal worker')
    parser.add_argument('--target', type=Path, required=True)
    args = parser.parse_args(argv)
    profile = resolve(args.target)
    if not profile.enabled:
        parser.error('Temporal is disabled by the inherited profile')
    try:
        asyncio.run(run_worker(profile.connection_mapping()))
    except KeyboardInterrupt:
        return 0
    except Exception:
        parser.exit(2, 'Sharing worker unavailable; reconcile existing Workflow IDs before retrying.\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
