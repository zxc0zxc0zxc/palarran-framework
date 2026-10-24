"""Actual optional Temporal Workflow and local Worker. Import requires temporalio."""
from __future__ import annotations

import asyncio
from datetime import timedelta
from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from .temporal import (DispatcherBridge, TemporalBackend, TERMINAL, WORKFLOW_NAME,
                           safe_receipt, validate_envelope)

NO_RETRY = RetryPolicy(maximum_attempts=1)


@workflow.defn(name=WORKFLOW_NAME)
class ParallelWorkflow:
    def __init__(self):
        self.request = None
        self.receipt = {"status": "pending"}
        self.cancel_requested = False
        self.dispatched = set()

    @workflow.query(name="envelope")
    def envelope(self):
        return self.request

    @workflow.query(name="status")
    def status(self):
        return self.receipt

    @workflow.signal(name="request_cancel")
    def request_cancel(self):
        self.cancel_requested = True

    async def call(self, name, payload, *, seconds=30):
        return await workflow.execute_activity(
            name, payload, start_to_close_timeout=timedelta(seconds=seconds),
            schedule_to_close_timeout=timedelta(seconds=seconds + 60),
            heartbeat_timeout=timedelta(seconds=15), retry_policy=NO_RETRY)

    @workflow.run
    async def run(self, request):
        self.request = validate_envelope(request)
        self.receipt = {"run_id": request["run_id"], "status": "pending"}
        try:
            for _ in range(request["max_cycles"]):
                if self.cancel_requested:
                    self.receipt = await self.call("palarran.parallel.cancel.v1", request)
                    return self.receipt
                self.receipt = await self.call("palarran.parallel.tick.v1", request)
                if self.cancel_requested:
                    self.receipt = await self.call("palarran.parallel.cancel.v1", request)
                    return self.receipt
                if self.receipt["status"] in TERMINAL:
                    return self.receipt
                ready = self.receipt.get("ready", [])[:self.receipt.get("available", 100)]
                routes = self.receipt.get("routes", {})
                if self.dispatched.intersection(ready) or len(self.dispatched) + len(ready) > 100:
                    self.receipt = {"run_id": request["run_id"], "status": "unknown"}
                    return self.receipt
                self.dispatched.update(ready)
                tasks = [workflow.start_activity(
                    "palarran.parallel.execute.v1", {"envelope": request, "task_id": task_id},
                    start_to_close_timeout=timedelta(seconds=request["task_seconds"]),
                    schedule_to_close_timeout=timedelta(seconds=request["task_seconds"] + 60),
                    heartbeat_timeout=timedelta(seconds=15), retry_policy=NO_RETRY,
                    **({"task_queue": routes[task_id]} if task_id in routes else {}),
                ) for task_id in ready]
                if tasks:
                    # A signal can revoke dispatcher leases while task Activities are still running.
                    await workflow.wait_condition(lambda: self.cancel_requested or all(t.done() for t in tasks))
                    if self.cancel_requested:
                        self.receipt = await self.call("palarran.parallel.cancel.v1", request)
                        if self.receipt["status"] == "unknown":
                            return self.receipt
                    results = await asyncio.gather(*tasks)
                    for task_id, result in zip(ready, results):
                        if result["status"] == "not_admitted":
                            # An authoritative rejected claim consumed no attempt or harness.
                            self.dispatched.discard(task_id)
                    if results and all(r["status"] == "not_admitted" for r in results):
                        try:
                            await workflow.wait_condition(lambda: self.cancel_requested,
                                                          timeout=timedelta(seconds=request["poll_seconds"]))
                        except TimeoutError:
                            pass
                    if any(r["status"] == "unknown" for r in results):
                        self.receipt = {"run_id": request["run_id"], "status": "unknown"}
                        return self.receipt
                    if self.cancel_requested:
                        self.receipt = await self.call("palarran.parallel.cancel.v1", request)
                        return self.receipt
                else:
                    try:
                        await workflow.wait_condition(lambda: self.cancel_requested,
                                                      timeout=timedelta(seconds=request["poll_seconds"]))
                    except TimeoutError:
                        pass
            self.receipt = {"run_id": request["run_id"], "status": "blocked"}
        except Exception:
            # No raw SDK/harness exception messages enter this Workflow result.
            self.receipt = {"run_id": request["run_id"], "status": "unknown"}
        return self.receipt


class DispatcherActivities:
    def __init__(self, bridge):
        self.bridge = bridge

    async def invoke(self, function, *args):
        task = asyncio.create_task(asyncio.to_thread(function, *args))
        # If Activity cancellation outlives a thread, do not emit its raw exception
        # through asyncio's unhandled-task logger. The ledger still needs reconciliation.
        task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
        try:
            while not task.done():
                activity.heartbeat({"run_id": (args[0].get("run_id") if args and isinstance(args[0], dict) else None)})
                await asyncio.wait({task}, timeout=2)
            return safe_receipt(task.result())
        except asyncio.CancelledError:
            # A raw Service cancellation is not terminal process evidence.
            if args:
                try:
                    await asyncio.wait_for(asyncio.to_thread(self.bridge.cancel, args[0]), timeout=5)
                except Exception:
                    pass
            raise
        except Exception:
            raise ApplicationError("dispatcher operation requires reconciliation", non_retryable=True) from None

    @activity.defn(name="palarran.parallel.tick.v1")
    async def tick(self, request):
        return await self.invoke(self.bridge.tick, validate_envelope(request))

    @activity.defn(name="palarran.parallel.execute.v1")
    async def execute(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"envelope", "task_id"}:
            raise ApplicationError("invalid task reference", non_retryable=True)
        return await self.invoke(self.bridge.execute, validate_envelope(payload["envelope"]), payload["task_id"])

    @activity.defn(name="palarran.parallel.cancel.v1")
    async def cancel(self, request):
        return await self.invoke(self.bridge.cancel, validate_envelope(request))


async def run_worker(profile, dispatcher, adapter, verifier, *, concurrency=4):
    """Operator-selected local bindings; no credential/profile values enter history."""
    if type(concurrency) is not int or not 1 <= concurrency <= 32:
        raise ValueError("invalid worker concurrency")
    backend = await TemporalBackend.connect(profile)
    activities = DispatcherActivities(DispatcherBridge(dispatcher, adapter, verifier))
    worker = Worker(backend.client, task_queue=backend.task_queue,
                    workflows=[ParallelWorkflow],
                    activities=[activities.tick, activities.execute, activities.cancel],
                    max_concurrent_activities=concurrency)
    await worker.run()


def main(argv=None):
    """Explicit operator entrypoint. Factory module is trusted local code, not input from history."""
    import argparse
    import importlib
    import json
    from .temporal import private_bytes
    parser = argparse.ArgumentParser(description="Run the optional local Palarran Temporal Worker")
    parser.add_argument("--profile-file", required=True, help="Owner-only JSON resolved connection profile")
    parser.add_argument("--binding", required=True, help="Trusted installed module:function returning dispatcher,adapter,verifier")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args(argv)
    module, separator, function = args.binding.partition(":")
    if not separator or not module or not function.isidentifier() or not all(p.isidentifier() for p in module.split(".")):
        parser.error("binding must be a trusted module:function")
    try:
        profile = json.loads(private_bytes(args.profile_file, limit=65536))
        if not isinstance(profile, dict):
            raise ValueError("invalid profile")
        factory = getattr(importlib.import_module(module), function)
        dispatcher, adapter, verifier = factory()
        asyncio.run(run_worker(profile, dispatcher, adapter, verifier, concurrency=args.concurrency))
    except KeyboardInterrupt:
        return 130
    except Exception:
        parser.exit(2, "Temporal Worker unavailable; inspect private configuration and reconcile active runs\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
