"""Offline contract tests: fake SDK transport is not real Temporal replay evidence."""
import asyncio
import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from packages.core.parallelism.temporal import (
    DispatcherBridge, TemporalBackend, TemporalUnavailable, envelope, private_bytes, safe_receipt,
)

REQUEST = envelope("run1", "a" * 64, max_cycles=3, poll_seconds=1, task_seconds=10)


class Handle:
    def __init__(self):
        self.prior = REQUEST
        self.signals = []
    async def query(self, name, **kwargs):
        return self.prior if name == "envelope" else {"status": "running", "secret": "never transport"}
    async def signal(self, name, **kwargs):
        self.signals.append(name)


class AlreadyStarted(Exception):
    pass


class FakeClient:
    def __init__(self, fail=None):
        self.fail, self.calls, self.handle = fail, 0, Handle()
    async def start_workflow(self, *args, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        if self.fail:
            raise self.fail
        return self.handle
    def get_workflow_handle(self, workflow_id):
        return self.handle


class TemporalClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_duplicate_attach_exact_envelope(self):
        client = FakeClient(AlreadyStarted())
        backend = TemporalBackend(client, already_started=AlreadyStarted)
        result = await backend.start(REQUEST)
        self.assertEqual(result["workflow_id"], "palarran-run1")
        self.assertEqual(client.calls, 1)
        self.assertEqual(client.last_kwargs["id_reuse_policy"], 3)
        client.handle.prior = {**REQUEST, "plan_sha256": "b" * 64}
        with self.assertRaisesRegex(ValueError, "mismatch"):
            await backend.start(REQUEST)

    async def test_ambiguous_start_does_not_replay_or_fallback(self):
        client = FakeClient(RuntimeError("secret URL and key"))
        with self.assertRaisesRegex(TemporalUnavailable, "outcome unknown") as error:
            await TemporalBackend(client).start(REQUEST)
        self.assertNotIn("secret", str(error.exception))
        self.assertEqual(client.calls, 1)

    async def test_cancel_only_requests_never_proves_stop(self):
        client = FakeClient()
        result = await TemporalBackend(client).cancel("run1")
        self.assertEqual(result["status"], "cancel_requested")
        self.assertFalse(result["stopped"])
        self.assertEqual(client.handle.signals, ["request_cancel"])

    async def test_status_strips_private_payload(self):
        result = await TemporalBackend(FakeClient()).status("run1")
        self.assertEqual(result, {"status": "running"})


class TemporalBoundaryTests(unittest.TestCase):
    def test_history_metadata_is_bounded(self):
        result = safe_receipt({"status": "submitted", "tokens": 20, "subject": "private path",
                               "stdout": "secret", "prompt": "private", "argv": ["secret"]})
        self.assertNotIn("private", json.dumps(result))
        self.assertEqual(len(result["subject_sha256"]), 64)
        with self.assertRaises(ValueError):
            safe_receipt({"status": "ready", "ready": ["x"] * 101})
        with self.assertRaises(ValueError):
            envelope("secret@example", "a" * 64)
        with self.assertRaises(ValueError):
            envelope("r", "a" * 64, max_cycles=True)

    def test_cancel_requires_terminal_proof(self):
        for value in ({"status": "cancelled"}, {"status": "cancelled", "stopped": False},
                      {"status": "cancelled", "stopped": True, "unknown": ["t"]}):
            self.assertEqual(safe_receipt(value)["status"], "unknown")
        self.assertEqual(safe_receipt({"status": "cancelled", "stopped": True, "unknown": []})["status"], "cancelled")

    def test_private_regular_file_only(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "key"
            p.write_text("secret")
            p.chmod(0o600)
            self.assertEqual(private_bytes(p), b"secret")
            p.chmod(0o644)
            with self.assertRaises(ValueError):
                private_bytes(p)
            (p.parent / "link").symlink_to(p)
            with self.assertRaises(OSError):
                private_bytes(p.parent / "link")

    def test_bridge_uses_existing_budget_authority(self):
        class Registry:
            def get_run(self, run_id):
                return {"backend": "temporal", "plan_sha256": "a" * 64}
            def execute_task(self, run, task, adapter, verifier):
                self.call = (run, task, adapter, verifier)
                return {"status": "verified", "task_id": task}
        registry = Registry()
        bridge = DispatcherBridge(registry, "adapter", "verifier")
        self.assertEqual(bridge.execute(REQUEST, "task1")["status"], "verified")
        self.assertEqual(registry.call, ("run1", "task1", "adapter", "verifier"))
        with self.assertRaisesRegex(ValueError, "digest"):
            bridge.execute({**REQUEST, "plan_sha256": "b" * 64}, "task1")

    def test_compose_profile_is_isolated_and_loopback(self):
        root = Path(__file__).resolve().parents[1]
        profile = json.loads((root / "packages/infrastructure/hosting/temporal.compose.yaml").read_text())
        services = profile["services"]
        self.assertEqual(set(services), {"temporal", "temporal-postgres", "temporal-ui"})
        self.assertNotIn("ports", services["temporal-postgres"])
        for item in services.values():
            self.assertEqual(item["profiles"], ["temporal"])
            self.assertEqual(item["networks"], ["temporal-private"])
            for port in item.get("ports", []):
                self.assertTrue(port.startswith("127.0.0.1:"))
            self.assertNotIn("POSTGRES_PASSWORD", item.get("environment", {}))
        self.assertNotIn("--allow-no-auth", services["temporal"]["command"])


def fake_worker_module():
    """Minimal SDK contract stand-in; never downloads SDK or starts a Service."""
    workflow = types.ModuleType("temporalio.workflow")
    class Passthrough:
        def __enter__(self): return self
        def __exit__(self, *args): return False
    workflow.unsafe = types.SimpleNamespace(imports_passed_through=Passthrough)
    def decorator(*args, **kwargs):
        if args and callable(args[0]): return args[0]
        return lambda value: value
    workflow.defn = workflow.run = workflow.query = workflow.signal = decorator
    activity = types.ModuleType("temporalio.activity")
    activity.defn = decorator
    activity.heartbeats = []
    activity.heartbeat = lambda value: activity.heartbeats.append(value)
    sdk = types.ModuleType("temporalio")
    sdk.activity, sdk.workflow = activity, workflow
    common = types.ModuleType("temporalio.common")
    common.RetryPolicy = lambda **kwargs: types.SimpleNamespace(**kwargs)
    errors = types.ModuleType("temporalio.exceptions")
    class ApplicationError(Exception):
        def __init__(self, message, **kwargs): super().__init__(message)
    errors.ApplicationError = ApplicationError
    worker = types.ModuleType("temporalio.worker")
    worker.Worker = object
    modules = {"temporalio": sdk, "temporalio.activity": activity, "temporalio.workflow": workflow,
               "temporalio.common": common, "temporalio.exceptions": errors, "temporalio.worker": worker}
    return modules, workflow, activity


class TemporalWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.modules, self.workflow, self.activity = fake_worker_module()
        self.patch = patch.dict(sys.modules, self.modules)
        self.patch.start()
        name = "packages.core.parallelism.temporal_worker"
        sys.modules.pop(name, None)
        self.module = importlib.import_module(name)

    async def asyncTearDown(self):
        sys.modules.pop("packages.core.parallelism.temporal_worker", None)
        self.patch.stop()

    async def test_workflow_dispatches_distinct_task_activities(self):
        calls, ticks = [], 0
        async def execute(name, payload, **kwargs):
            nonlocal ticks
            self.assertEqual(kwargs["retry_policy"].maximum_attempts, 1)
            if name.endswith("tick.v1"):
                ticks += 1
                return {"status": "ready", "ready": ["a", "b"]} if ticks == 1 else {"status": "verified"}
            calls.append(payload["task_id"])
            await asyncio.sleep(0)
            return {"status": "verified"}
        async def wait(predicate, **kwargs):
            if "timeout" in kwargs and not predicate():
                raise TimeoutError
            while not predicate(): await asyncio.sleep(0)
        self.workflow.execute_activity = execute
        self.workflow.start_activity = lambda *args, **kwargs: asyncio.create_task(execute(*args, **kwargs))
        self.workflow.wait_condition = wait
        result = await self.module.ParallelWorkflow().run(REQUEST)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(set(calls), {"a", "b"})

    async def test_capacity_one_and_rejected_claim_eventually_complete(self):
        completed, attempts, ticks = [], {}, 0
        async def execute(name, payload, **kwargs):
            nonlocal ticks
            if name.endswith("tick.v1"):
                ticks += 1
                pending = [t for t in ("a", "b", "c", "d") if t not in completed]
                return {"status": "ready", "ready": pending, "available": 1,
                        "routes": {t: "worker-" + t for t in pending}} if pending else {"status": "verified"}
            task_id = payload["task_id"]
            self.assertEqual(kwargs["task_queue"], "worker-" + task_id)
            attempts[task_id] = attempts.get(task_id, 0) + 1
            if task_id == "a" and attempts[task_id] == 1:
                return {"status": "not_admitted", "task_id": task_id}
            completed.append(task_id)
            return {"status": "verified", "task_id": task_id}
        async def wait(predicate, **kwargs):
            if "timeout" in kwargs and not predicate():
                raise TimeoutError
            while not predicate(): await asyncio.sleep(0)
        self.workflow.execute_activity = execute
        self.workflow.start_activity = lambda *args, **kwargs: asyncio.create_task(execute(*args, **kwargs))
        self.workflow.wait_condition = wait
        result = await self.module.ParallelWorkflow().run({**REQUEST, "max_cycles": 10})
        self.assertEqual(result["status"], "verified")
        self.assertEqual(completed, ["a", "b", "c", "d"])
        self.assertEqual(attempts, {"a": 2, "b": 1, "c": 1, "d": 1})

    async def test_failed_activity_stops_unknown_without_retry(self):
        calls = []
        async def execute(name, payload, **kwargs):
            calls.append(name)
            raise RuntimeError("raw secret")
        self.workflow.execute_activity = execute
        result = await self.module.ParallelWorkflow().run(REQUEST)
        self.assertEqual(result, {"run_id": "run1", "status": "unknown"})
        self.assertEqual(len(calls), 1)

    async def test_cancel_signal_during_task_requires_dispatcher_proof(self):
        instance = self.module.ParallelWorkflow()
        gate = asyncio.Event()
        async def execute(name, payload, **kwargs):
            if name.endswith("tick.v1"): return {"status": "ready", "ready": ["a"]}
            if name.endswith("cancel.v1"):
                gate.set()
                return {"status": "unknown", "stopped": False, "unknown": ["a"]}
            instance.request_cancel()
            await gate.wait()
            return {"status": "cancelled", "stopped": True}
        async def wait(predicate, **kwargs):
            if "timeout" in kwargs and not predicate():
                raise TimeoutError
            while not predicate(): await asyncio.sleep(0)
        self.workflow.execute_activity = execute
        self.workflow.start_activity = lambda *args, **kwargs: asyncio.create_task(execute(*args, **kwargs))
        self.workflow.wait_condition = wait
        result = await instance.run(REQUEST)
        self.assertEqual(result["status"], "unknown")

    async def test_signal_during_terminal_tick_precedes_acceptance(self):
        instance = self.module.ParallelWorkflow()
        calls = []
        async def execute(name, payload, **kwargs):
            calls.append(name)
            if name.endswith("tick.v1"):
                instance.request_cancel()
                return {"status": "verified"}
            return {"status": "cancelled", "stopped": True, "unknown": []}
        self.workflow.execute_activity = execute
        result = await instance.run(REQUEST)
        self.assertEqual(result["status"], "cancelled")
        self.assertTrue(calls[-1].endswith("cancel.v1"))

    async def test_activity_bridge_sanitizes_failure(self):
        class BadBridge:
            def tick(self, request): raise RuntimeError("password")
        activities = self.module.DispatcherActivities(BadBridge())
        with self.assertRaisesRegex(Exception, "requires reconciliation") as error:
            await activities.tick(REQUEST)
        self.assertNotIn("password", str(error.exception))
        self.assertTrue(self.activity.heartbeats)


@unittest.skipUnless(importlib.util.find_spec("temporalio"), "optional Temporal SDK not installed")
class RealSDKDefinitionTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_sdk_workflow_sandbox_and_activity_registration(self):
        from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner
        from temporalio.workflow import _Definition
        from temporalio.activity import _Definition as ActivityDefinition
        from temporalio.common import WorkflowIDReusePolicy
        from packages.core.parallelism.temporal_worker import ParallelWorkflow, DispatcherActivities
        definition = _Definition.must_from_class(ParallelWorkflow)
        SandboxedWorkflowRunner().prepare_workflow(definition)
        self.assertEqual(definition.name, "palarran.parallel.run.v1")
        self.assertEqual(int(WorkflowIDReusePolicy.REJECT_DUPLICATE), 3)
        for method in (DispatcherActivities.tick, DispatcherActivities.execute, DispatcherActivities.cancel):
            self.assertTrue(ActivityDefinition.must_from_callable(method).name.startswith("palarran.parallel."))
