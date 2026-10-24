"""Optional Temporal client and bounded dispatcher bridge. No SDK import at load."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from datetime import timedelta
import re
import stat
from typing import Mapping

SDK_VERSION = "1.34.0"
WORKFLOW_NAME = "palarran.parallel.run.v1"
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
_NAMESPACE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
STATES = frozenset({"pending", "ready", "running", "submitted", "verified", "blocked",
                    "handoff_pending", "failed", "cancel_requested", "cancelled", "unknown", "not_admitted"})
TERMINAL = frozenset({"verified", "failed", "unknown", "blocked", "handoff_pending", "cancelled"})


class TemporalUnavailable(RuntimeError):
    """Connection/start outcome must be reconciled; no local fallback permitted."""


def identifier(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError("invalid opaque identifier")
    return value


def envelope(run_id, plan_sha256, *, max_cycles=1000, poll_seconds=2, task_seconds=3600):
    identifier(run_id)
    if not isinstance(plan_sha256, str) or not _HASH.fullmatch(plan_sha256):
        raise ValueError("invalid plan digest")
    for value, upper in ((max_cycles, 1000), (poll_seconds, 60), (task_seconds, 86400)):
        if type(value) is not int or not 1 <= value <= upper:
            raise ValueError("invalid scheduling bound")
    return dict(run_id=run_id, plan_sha256=plan_sha256, max_cycles=max_cycles,
                poll_seconds=poll_seconds, task_seconds=task_seconds)


def validate_envelope(value):
    if not isinstance(value, dict) or set(value) != {
            "run_id", "plan_sha256", "max_cycles", "poll_seconds", "task_seconds"}:
        raise ValueError("invalid Temporal envelope")
    return envelope(**value)


def safe_receipt(value):
    """Whitelist transport fields; discard private paths, prose, manifests and errors."""
    if not isinstance(value, dict) or value.get("status") not in STATES:
        raise ValueError("invalid dispatcher receipt")
    result = {"status": value["status"]}
    for key in ("run_id", "task_id"):
        if key in value:
            result[key] = identifier(value[key])
    for key in ("ready", "active", "unknown"):
        if key in value:
            if not isinstance(value[key], list) or len(value[key]) > 100:
                raise ValueError("oversized dispatcher receipt")
            result[key] = [identifier(item) for item in value[key]]
    if "available" in value:
        if type(value["available"]) is not int or not 0 <= value["available"] <= 100:
            raise ValueError("invalid admission capacity")
        result["available"] = value["available"]
    if "routes" in value:
        if not isinstance(value["routes"], dict) or len(value["routes"]) > 100:
            raise ValueError("invalid worker routes")
        result["routes"] = {identifier(k): identifier(v) for k, v in value["routes"].items()}
    for key in ("stopped", "usage_known"):
        if key in value:
            if type(value[key]) is not bool:
                raise ValueError("invalid dispatcher receipt flag")
            result[key] = value[key]
    for key in ("tokens", "cost_micros"):
        if key in value:
            if type(value[key]) is not int or not 0 <= value[key] <= 10**15:
                raise ValueError("invalid usage counter")
            result[key] = value[key]
    if "backend" in value:
        if value["backend"] != "temporal":
            raise ValueError("run backend mismatch")
        result["backend"] = "temporal"
    # Subject/evidence values are not assumed safe text: publish only their digests.
    for key in ("subject", "evidence"):
        if key in value:
            raw = json.dumps(value[key], sort_keys=True).encode()
            if len(raw) > 16384:
                raise ValueError("oversized subject reference")
            result[key + "_sha256"] = hashlib.sha256(raw).hexdigest()
    for key in ("subject_sha256", "evidence_sha256"):
        if key in value:
            if not isinstance(value[key], str) or not _HASH.fullmatch(value[key]):
                raise ValueError("invalid artifact digest")
            result[key] = value[key]
    if result["status"] == "cancelled" and (result.get("stopped") is not True or result.get("unknown")):
        result["status"] = "unknown"
    return result


def private_bytes(path, *, limit=1048576):
    """Read a single owner-only regular file without following its final symlink."""
    fd = os.open(Path(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid():
            raise ValueError("credential file must be owned and private")
        data = os.read(fd, limit + 1)
        if not data or len(data) > limit:
            raise ValueError("invalid credential file size")
        return data
    finally:
        os.close(fd)


class TemporalBackend:
    """Connection is explicit; a failed RPC never chooses another backend."""
    def __init__(self, client, *, task_queue="palarran", already_started=None, reject_duplicate=3):
        self.client = client
        self.task_queue = identifier(task_queue)
        self.already_started = already_started
        self.reject_duplicate = reject_duplicate

    @classmethod
    async def connect(cls, profile: Mapping):
        try:
            from temporalio.client import Client, TLSConfig
            from temporalio.exceptions import WorkflowAlreadyStartedError
            from temporalio.common import WorkflowIDReusePolicy
        except ImportError:
            raise TemporalUnavailable("optional Temporal SDK is not installed") from None
        address = profile.get("address")
        namespace = profile.get("namespace", "palarran")
        if not isinstance(address, str) or not address or len(address) > 255 or any(c.isspace() for c in address):
            raise ValueError("invalid Temporal address")
        if not isinstance(namespace, str) or not _NAMESPACE.fullmatch(namespace):
            raise ValueError("invalid Temporal namespace")
        tls = profile.get("tls", False)
        if type(tls) is not bool:
            raise ValueError("invalid Temporal TLS flag")
        loopback = address.rsplit(":", 1)[0] in ("127.0.0.1", "localhost", "[::1]")
        if not loopback and not tls:
            raise ValueError("non-loopback Temporal requires TLS")
        cert, key = profile.get("tls_cert_file"), profile.get("tls_key_file")
        if bool(cert) != bool(key) or (not tls and any(profile.get(k) for k in
                ("tls_cert_file", "tls_key_file", "tls_ca_file", "server_name", "api_key_file"))):
            raise ValueError("inconsistent Temporal credential profile")
        tls_config = TLSConfig(
            server_root_ca_cert=private_bytes(profile["tls_ca_file"]) if profile.get("tls_ca_file") else None,
            client_cert=private_bytes(cert) if cert else None,
            client_private_key=private_bytes(key) if key else None,
            domain=profile.get("server_name"),
        ) if tls else False
        api_key = private_bytes(profile["api_key_file"], limit=8192).decode().strip() if profile.get("api_key_file") else None
        try:
            client = await asyncio.wait_for(Client.connect(
                address, namespace=namespace, tls=tls_config, api_key=api_key,
                identity="palarran-worker"), timeout=10)
            healthy = await asyncio.wait_for(client.service_client.check_health(), timeout=10)
            if not healthy:
                raise TemporalUnavailable("Temporal service unavailable")
        except Exception:
            raise TemporalUnavailable("Temporal connection unavailable; no fallback") from None
        return cls(client, task_queue=profile.get("task_queue", "palarran"),
                   already_started=WorkflowAlreadyStartedError,
                   reject_duplicate=WorkflowIDReusePolicy.REJECT_DUPLICATE)

    @classmethod
    async def probe(cls, profile):
        """Actual SDK health, namespace existence and admitted server/SDK versions."""
        result = {"service": False, "namespace": False, "compatible": False}
        try:
            from importlib.metadata import version
            from temporalio.api.workflowservice.v1 import DescribeNamespaceRequest, GetSystemInfoRequest
            backend = await cls.connect(profile)
            result["service"] = True
            namespace = await asyncio.wait_for(backend.client.workflow_service.describe_namespace(
                DescribeNamespaceRequest(namespace=profile.get("namespace", "palarran"))), timeout=10)
            result["namespace"] = namespace.namespace_info.name == profile.get("namespace", "palarran")
            info = await asyncio.wait_for(backend.client.workflow_service.get_system_info(
                GetSystemInfoRequest()), timeout=10)
            result["compatible"] = version("temporalio") == SDK_VERSION and info.server_version == "1.32.1"
        except Exception:
            pass
        return result

    async def start(self, request):
        request = validate_envelope(request)
        workflow_id = "palarran-" + request["run_id"]
        try:
            handle = await self.client.start_workflow(WORKFLOW_NAME, request, id=workflow_id,
                                                     task_queue=self.task_queue,
                                                     id_reuse_policy=self.reject_duplicate,
                                                     rpc_timeout=timedelta(seconds=10))
        except Exception as exc:
            if self.already_started and isinstance(exc, self.already_started):
                handle = self.client.get_workflow_handle(workflow_id)
                try:
                    prior = await handle.query("envelope", rpc_timeout=timedelta(seconds=10))
                except Exception:
                    raise TemporalUnavailable("duplicate run requires reconciliation") from None
                if prior != request:
                    raise ValueError("existing workflow envelope mismatch") from None
            else:
                raise TemporalUnavailable("Temporal start outcome unknown; reconcile workflow ID") from None
        return {"run_id": request["run_id"], "workflow_id": workflow_id, "backend": "temporal"}

    async def status(self, run_id):
        try:
            value = await self.client.get_workflow_handle("palarran-" + identifier(run_id)).query("status", rpc_timeout=timedelta(seconds=10))
            return safe_receipt(value)
        except ValueError:
            raise
        except Exception:
            raise TemporalUnavailable("Temporal status unavailable") from None

    async def cancel(self, run_id):
        try:
            await self.client.get_workflow_handle("palarran-" + identifier(run_id)).signal("request_cancel", rpc_timeout=timedelta(seconds=10))
        except ValueError:
            raise
        except Exception:
            raise TemporalUnavailable("Temporal cancellation outcome unknown") from None
        return {"run_id": run_id, "status": "cancel_requested", "stopped": False}


class DispatcherBridge:
    """Local trusted registry/adapter/verifier binding; never serialized to Temporal."""
    def __init__(self, dispatcher, adapter, verifier):
        self.dispatcher, self.adapter, self.verifier = dispatcher, adapter, verifier

    def check(self, request):
        request = validate_envelope(request)
        run = self.dispatcher.get_run(request["run_id"])
        if run.get("backend") != "temporal":
            raise ValueError("run backend mismatch")
        digest = run.get("plan_sha256")
        if digest != request["plan_sha256"]:
            raise ValueError("run plan digest mismatch")
        return request

    def tick(self, request):
        request = self.check(request)
        return safe_receipt(self.dispatcher.tick(request["run_id"]))

    def execute(self, request, task_id):
        request = self.check(request)
        return safe_receipt(self.dispatcher.execute_task(request["run_id"], identifier(task_id),
                                                         self.adapter, self.verifier))

    def cancel(self, request):
        request = self.check(request)
        return safe_receipt(self.dispatcher.cancel(request["run_id"]))
