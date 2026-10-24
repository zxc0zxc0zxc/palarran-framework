"""Synthetic local coordination checks; no VPS, model or external APIs."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
import http.client
import io
import json
import os
from pathlib import Path
import sqlite3
import socket
import time
import tempfile
import threading
import unittest
from unittest.mock import patch

from packages.core.coordination import service


TOKENS = {"alice": "a" * 40, "bob": "b" * 40, "operator": "o" * 40, "other": "z" * 40}
CREDENTIALS = {
    TOKENS["alice"]: {"actor": "alice", "projects": ["alpha", "shared"], "role": "agent"},
    TOKENS["bob"]: {"actor": "bob", "projects": ["alpha"], "role": "agent"},
    TOKENS["operator"]: {"actor": "operator", "projects": ["alpha"], "role": "operator"},
    TOKENS["other"]: {"actor": "other", "projects": ["beta"], "role": "agent"},
}


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.path = self.root / "private" / "coordination.sqlite3"
        self.store = service.CoordinationStore(self.path, CREDENTIALS)
        self.counter = 0
        self.server = None
        self.thread = None
        self.ensure()

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=3)
        self.temp.cleanup()

    def call(self, operation, actor="alice", **fields):
        payload = {"project": "alpha", "room": "incident", **fields}
        if operation in service.MUTATIONS and "request_id" not in payload:
            self.counter += 1
            payload["request_id"] = "action_%d" % self.counter
        if operation == "operation.get":
            payload.pop("room", None)
        return self.store.dispatch(TOKENS[actor], operation, payload)

    def ensure(self, **fields):
        return self.call("room.ensure", **{"title": "Synthetic incident", **fields})

    def error(self, response, code):
        self.assertEqual(response, {"ok": False, "error": {"code": code}})

    def start_http(self):
        self.server = service.create_server(self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.server.server_address[1]

    def http(self, operation, payload, token=TOKENS["alice"], raw=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=3)
        body = service.encode(payload) if raw is None else raw
        request_headers = {"Content-Type": "application/json", **(headers or {})}
        if token is not None:
            request_headers["Authorization"] = "Bearer " + token
        connection.request("POST", "/v1/" + operation, body=body, headers=request_headers)
        response = connection.getresponse()
        raw_response = response.read()
        code = response.status
        connection.close()
        self.assertLessEqual(len(raw_response), service.MAX_RESPONSE)
        return code, json.loads(raw_response)

    def test_idempotence_lost_response_and_restart(self):
        posted = self.call("message.post", kind="fact", text="One durable fact", request_id="stable")
        self.assertTrue(posted["ok"])
        self.store = service.CoordinationStore(self.path, CREDENTIALS)
        self.assertEqual(self.call("message.post", kind="fact", text="One durable fact", request_id="stable"), posted)
        receipt = self.call("operation.get", request_id="stable")["result"]
        self.assertEqual(receipt, {"found": True, "operation": "message.post", "receipt": posted})
        self.assertEqual(len(self.call("messages.list")["result"]["messages"]), 1)
        self.error(self.call("message.post", kind="fact", text="Changed payload", request_id="stable"), "idempotency_conflict")
        self.error(self.call("ack", message_seq=posted["result"]["message"]["seq"], request_id="stable"), "idempotency_conflict")
        self.assertEqual(self.call("operation.get", actor="bob", request_id="stable")["result"], {"found": False})

    def test_actual_disconnected_http_response_reconciles_without_replay(self):
        port = self.start_http()
        payload = {"project": "alpha", "room": "incident", "kind": "fact",
                   "text": "Lost HTTP response", "request_id": "network-lost"}
        body = service.encode(payload)
        headers = ("POST /v1/message.post HTTP/1.0\r\n"
                   "Host: localhost\r\nAuthorization: Bearer %s\r\n"
                   "Content-Type: application/json\r\nContent-Length: %d\r\n\r\n"
                   % (TOKENS["alice"], len(body))).encode("ascii")
        with socket.create_connection(("127.0.0.1", port), timeout=2) as connection:
            connection.sendall(headers + body)
            # Deliberately discard the response rather than retrying the write.
        deadline = time.monotonic() + 2
        while True:
            receipt = self.call("operation.get", request_id="network-lost")["result"]
            if receipt["found"] or time.monotonic() >= deadline:
                break
            time.sleep(.01)
        self.assertTrue(receipt["found"])
        self.assertEqual(receipt["receipt"]["result"]["message"]["text"], payload["text"])
        self.assertEqual(len(self.call("messages.list")["result"]["messages"]), 1)

    def test_actor_request_ids_are_global_across_projects(self):
        self.error(self.ensure(project="shared", room="second", request_id="action_1"), "idempotency_conflict")
        self.assertEqual(self.call("operation.get", project="shared", request_id="action_1")["result"], {"found": False})

    def test_scope_recipient_and_actor_spoofing(self):
        self.error(self.call("messages.list", actor="other"), "forbidden")
        self.error(self.call("message.post", kind="fact", text="test", recipient="other"), "forbidden")
        self.error(self.call("message.post", kind="fact", text="test", recipient="missing"), "forbidden")
        self.error(self.store.dispatch(TOKENS["alice"], "message.post", {
            "project": "alpha", "room": "incident", "kind": "fact", "text": "test",
            "actor": "operator", "request_id": "spoof"}), "invalid_request")
        posted = self.call("message.post", kind="question", text="Attention", recipient="bob")["result"]["message"]
        self.assertEqual((posted["actor"], posted["recipient"]), ("alice", "bob"))
        self.ensure(room="other-room")
        self.assertEqual(self.call("messages.list", room="other-room")["result"]["messages"], [])

    def test_ack_is_identity_bound_not_approval(self):
        seq = self.call("message.post", kind="fact", text="Read this")["result"]["message"]["seq"]
        first = self.call("ack", actor="bob", message_seq=seq)["result"]
        later = self.call("ack", actor="bob", message_seq=seq)["result"]
        self.assertEqual(first["actor"], "bob")
        self.assertEqual(first["acknowledged_at"], later["acknowledged_at"])
        self.error(self.call("ack", message_seq=seq, room="nonexistent"), "room_missing")
        self.error(self.call("ack", message_seq=seq+100), "message_missing")

    def test_room_title_is_stable_and_error_receipt_is_durable(self):
        self.error(self.ensure(title="Rename", request_id="rename"), "room_conflict")
        receipt = self.call("operation.get", request_id="rename")["result"]["receipt"]
        self.error(receipt, "room_conflict")
        self.error(self.ensure(title="Synthetic incident", request_id="rename"), "idempotency_conflict")

    def test_claims_exclusive_race_two_http_clients(self):
        self.start_http()
        barrier = threading.Barrier(2)
        def acquire(actor):
            barrier.wait()
            return self.http("claim.acquire", {"project": "alpha", "room": "incident",
                "resource": "prod:service", "ttl": 30, "request_id": "race"}, TOKENS[actor])[1]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(acquire, ["alice", "bob"]))
        self.assertEqual(sum(item["ok"] for item in results), 1)
        winner = next(item["result"]["claim"] for item in results if item["ok"])
        loser = next(item for item in results if not item["ok"])
        self.error(loser, "resource_busy")
        self.assertEqual(winner["fence"], 1)

    def test_project_wide_resource_claim_excludes_other_rooms(self):
        self.ensure(room="feature-room")
        self.start_http()
        barrier = threading.Barrier(2)
        def acquire(pair):
            actor, room = pair
            barrier.wait()
            return self.http("claim.acquire", {"project": "alpha", "room": room,
                "resource": "prod:canonical-target", "ttl": 30, "request_id": "cross_room"}, TOKENS[actor])[1]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(acquire, [("alice", "incident"), ("bob", "feature-room")]))
        self.assertEqual(sum(result["ok"] for result in results), 1)
        winner = next(result["result"]["claim"] for result in results if result["ok"])
        self.error(next(result for result in results if not result["ok"]), "resource_busy")
        self.assertIn(winner["room"], ("incident", "feature-room"))
        self.assertEqual(self.call("claims.list", room="feature-room")["result"]["claims"], [winner])
        wrong_room = "feature-room" if winner["room"] == "incident" else "incident"
        self.error(self.call("claim.release", actor=winner["owner"], room=wrong_room,
                            claim_id=winner["claim_id"], fence=winner["fence"]), "stale_claim")
        self.ensure(project="beta", actor="other")
        independent = self.call("claim.acquire", project="beta", actor="other",
                                resource="prod:canonical-target", ttl=30)
        self.assertTrue(independent["ok"])
        self.assertEqual(independent["result"]["claim"]["fence"], 1)
        self.assertTrue(self.call("claim.release", actor=winner["owner"], room=winner["room"],
                                 claim_id=winner["claim_id"], fence=winner["fence"])["ok"])
        next_claim = self.call("claim.acquire", room=wrong_room, resource="prod:canonical-target", ttl=30)["result"]["claim"]
        self.assertEqual(next_claim["room"], wrong_room)
        self.assertGreater(next_claim["fence"], winner["fence"])

    def test_release_renew_and_monotonic_fencing(self):
        claim = self.call("claim.acquire", resource="data/schema", ttl=30)["result"]["claim"]
        renewed = self.call("claim.renew", claim_id=claim["claim_id"], fence=claim["fence"], ttl=300)["result"]["claim"]
        self.assertGreaterEqual(renewed["expires_at"], claim["expires_at"]+270)
        self.error(self.call("claim.release", actor="bob", claim_id=claim["claim_id"], fence=claim["fence"]), "forbidden")
        released = self.call("claim.release", claim_id=claim["claim_id"], fence=claim["fence"])["result"]["claim"]
        self.assertEqual((released["state"], released["owner"], released["expires_at"]), ("released", None, None))
        second = self.call("claim.acquire", actor="bob", resource="data/schema", ttl=30)["result"]["claim"]
        self.assertGreater(second["fence"], claim["fence"])
        self.assertNotEqual(second["claim_id"], claim["claim_id"])
        self.error(self.call("claim.renew", claim_id=claim["claim_id"], fence=claim["fence"], ttl=30), "stale_claim")

    def test_expiry_never_reassigns_without_operator_reconciliation(self):
        with patch.object(service.time, "time", return_value=1000):
            claim = self.call("claim.acquire", resource="shared", ttl=30)["result"]["claim"]
        with patch.object(service.time, "time", return_value=1031):
            self.store = service.CoordinationStore(self.path, CREDENTIALS)
            listed = self.call("claims.list")["result"]["claims"][0]
            self.assertEqual(listed["state"], "blocked_pending_reconciliation")
            with patch.object(service.time, "time", return_value=1001):
                self.error(self.call("claim.renew", claim_id=claim["claim_id"], fence=claim["fence"], ttl=30), "reconciliation_required")
            self.error(self.call("claim.acquire", actor="bob", resource="shared", ttl=30), "reconciliation_required")
            self.error(self.call("claim.renew", claim_id=claim["claim_id"], fence=claim["fence"], ttl=30), "reconciliation_required")
            self.error(self.call("claim.release", claim_id=claim["claim_id"], fence=claim["fence"]), "reconciliation_required")
            self.error(self.call("claim.reconcile", claim_id=claim["claim_id"], fence=claim["fence"], observed_state="Old process stopped"), "operator_required")
            self.error(self.call("claim.reconcile", actor="operator", claim_id=claim["claim_id"], fence=claim["fence"]+1, observed_state="Stopped"), "stale_claim")
            reconciled = self.call("claim.reconcile", actor="operator", claim_id=claim["claim_id"], fence=claim["fence"], observed_state="Stopped and checked")["result"]["claim"]
            self.assertEqual((reconciled["state"], reconciled["fence"]), ("released", claim["fence"]+1))
            new = self.call("claim.acquire", actor="bob", resource="shared", ttl=30)["result"]["claim"]
            self.assertGreater(new["fence"], reconciled["fence"])

    def test_message_pages_preserve_whole_near_limit_unicode_items(self):
        text = "\U0001f680" * 4000
        sequences = []
        for _ in range(4):
            message = self.call("message.post", kind="fact", text=text)
            self.assertTrue(message["ok"], message)
            sequences.append(message["result"]["message"]["seq"])
        after, seen, pages = 0, [], 0
        while True:
            response = self.call("messages.list", after=after, limit=20)
            self.assertLessEqual(len(service.encode(response)), service.MAX_RESPONSE)
            page = response["result"]
            for message in page["messages"]:
                self.assertEqual(message["text"], text)
                seen.append(message["seq"])
            pages += 1
            after = page["next_cursor"]
            if not page["has_more"]:
                break
            self.assertTrue(page["messages"])
        self.assertEqual(seen, sequences)
        self.assertGreater(pages, 1)
        empty = self.call("messages.list", after=after)["result"]
        self.assertEqual(empty, {"messages": [], "next_cursor": after, "has_more": False})

    def test_claim_pages_and_limit_validation(self):
        for resource in ("c", "a", "b"):
            self.call("claim.acquire", resource=resource, ttl=30)
        first = self.call("claims.list", limit=2)["result"]
        self.assertEqual([x["resource"] for x in first["claims"]], ["a", "b"])
        self.assertEqual((first["next_cursor"], first["has_more"]), ("b", True))
        second = self.call("claims.list", after="b", limit=2)["result"]
        self.assertEqual([x["resource"] for x in second["claims"]], ["c"])
        self.assertFalse(second["has_more"])
        self.error(self.call("claims.list", limit=True), "invalid_request")
        self.error(self.call("messages.list", limit=21), "invalid_request")
        self.error(self.call("messages.list", after=False), "invalid_request")

    def test_quotas_fail_before_requested_mutation(self):
        with patch.object(service, "MAX_ROOMS", 1):
            self.error(self.ensure(room="overflow"), "capacity_exhausted")
            self.error(self.call("messages.list", room="overflow"), "room_missing")
        with patch.object(service, "MAX_MESSAGES", 1):
            self.assertTrue(self.call("message.post", kind="fact", text="one")["ok"])
            self.error(self.call("message.post", kind="fact", text="two", request_id="quota"), "capacity_exhausted")
            self.assertEqual(self.call("operation.get", request_id="quota")["result"], {"found": False})
        with patch.object(service, "MAX_ACKS", 0):
            seq = self.call("messages.list")["result"]["messages"][0]["seq"]
            self.error(self.call("ack", message_seq=seq), "capacity_exhausted")
        with patch.object(service, "MAX_RESOURCES", 1):
            self.assertTrue(self.call("claim.acquire", resource="one", ttl=30)["ok"])
            self.error(self.call("claim.acquire", resource="two", ttl=30), "capacity_exhausted")
        with patch.object(service, "MAX_RECEIPTS", 0):
            self.error(self.ensure(room="receipt-overflow"), "capacity_exhausted")
        with patch.object(service, "MAX_DATABASE", 1):
            self.error(self.call("message.post", kind="fact", text="disk"), "capacity_exhausted")
        self.assertEqual(len(self.call("messages.list")["result"]["messages"]), 1)

    def test_auth_strict_json_and_oversize_http(self):
        self.start_http()
        payload = {"project": "alpha", "room": "incident"}
        for token in (None, "not_a_token"):
            code, response = self.http("messages.list", payload, token=token, raw=b"invalid")
            self.assertEqual(code, 401)
            self.error(response, "unauthorized")
        for raw in (b'{"project":"alpha","project":"beta"}', b'{"project":NaN}', b'{"project":Infinity}', b'[]', b'\xff', b'{}'):
            code, response = self.http("messages.list", payload, raw=raw)
            self.assertEqual(code, 400)
            self.error(response, "invalid_request")
        code, response = self.http("messages.list", payload, raw=b"x"*(service.MAX_REQUEST+1))
        self.assertEqual(code, 413)
        self.error(response, "request_too_large")
        code, response = self.http("messages.list", payload, headers={"Transfer-Encoding": "chunked"})
        self.assertEqual(code, 400)
        self.error(response, "invalid_request")
        self.error(self.call("message.post", kind=[], text="bad"), "invalid_request")
        self.error(self.call("claim.acquire", resource="x", ttl=True), "invalid_request")

    def test_http_receipts_and_no_body_token_logging(self):
        self.start_http()
        secret = "Synthetic private body sentinel"
        with redirect_stderr(io.StringIO()) as captured:
            payload = {"project": "alpha", "room": "incident", "kind": "fact", "text": secret, "request_id": "http-post"}
            code, posted = self.http("message.post", payload)
            self.assertEqual(code, 200)
            code, repeated = self.http("message.post", payload)
            self.assertEqual(posted, repeated)
            code, found = self.http("operation.get", {"project": "alpha", "request_id": "http-post"})
            self.assertEqual(found["result"]["receipt"], posted)
            code, _ = self.http("unknown", {})
            self.assertEqual(code, 400)
        self.assertNotIn(secret, captured.getvalue())
        self.assertNotIn(TOKENS["alice"], captured.getvalue())
        with sqlite3.connect(self.path) as connection:
            dump = "\n".join(connection.iterdump())
        for token in TOKENS.values():
            self.assertNotIn(token, dump)

    def test_private_files_and_no_symlinks(self):
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)
        credential_file = self.root / "credentials.json"
        credential_file.write_bytes(service.encode(CREDENTIALS))
        credential_file.chmod(0o600)
        self.assertEqual(service.load_credentials(credential_file), CREDENTIALS)
        credential_file.chmod(0o644)
        with self.assertRaises(service.CoordinationError):
            service.load_credentials(credential_file)
        credential_file.chmod(0o600)
        link = self.root / "link"
        link.symlink_to(self.path.parent, target_is_directory=True)
        with self.assertRaises(service.CoordinationError):
            service.CoordinationStore(link / "other.sqlite3", CREDENTIALS)
        with self.assertRaises(service.CoordinationError):
            service.create_server(self.store, host="0.0.0.0")
        unsafe = self.root / "unsafe.sqlite3"
        unsafe.write_bytes(b"")
        unsafe.chmod(0o644)
        with self.assertRaises(service.CoordinationError):
            service.CoordinationStore(unsafe, CREDENTIALS)

    def test_sqlite_wal_reset_fix_versions_and_prewrite_startup_gate(self):
        for version in ((3, 51, 3), (3, 52, 0), (3, 54, 0), (3, 50, 7), (3, 50, 8), (3, 44, 6)):
            with self.subTest(supported=version):
                self.assertTrue(service.supported_sqlite(version))
        for version in ((3, 51, 2), (3, 50, 6), (3, 44, 5), (3, 49, 9), (3, 39, 0), (True, 51, 3), "3.51.3"):
            with self.subTest(unsupported=version):
                self.assertFalse(service.supported_sqlite(version))
        absent = self.root / "not-created" / "blocked.sqlite3"
        with patch.object(service.sqlite3, "sqlite_version_info", (3, 51, 2)):
            with self.assertRaises(service.CoordinationError) as raised:
                service.CoordinationStore(absent, CREDENTIALS)
        self.assertEqual(raised.exception.args, ("unsupported_sqlite",))
        self.assertFalse(absent.parent.exists())

    def test_credentials_distinct_and_bounded(self):
        for credentials in ({"short": CREDENTIALS[TOKENS["alice"]]},
                            {"\x00"*40: CREDENTIALS[TOKENS["alice"]]},
                            {"\x7f"*40: CREDENTIALS[TOKENS["alice"]]},
                            {TOKENS["alice"]: {"actor": "alice", "projects": ["alpha"], "role": "admin"}},
                            {TOKENS["alice"]: CREDENTIALS[TOKENS["alice"]],
                             TOKENS["bob"]: CREDENTIALS[TOKENS["alice"]]}):
            with self.assertRaises(service.CoordinationError):
                service.CoordinationStore(self.path, credentials)

    def test_transaction_failure_rolls_back_effect_and_receipt(self):
        # Simulate a disk/schema failure at receipt insertion after message insert.
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TRIGGER reject_receipt BEFORE INSERT ON receipts BEGIN SELECT RAISE(ABORT,'private error'); END")
        self.error(self.call("message.post", kind="fact", text="must rollback", request_id="broken"), "unavailable")
        self.assertEqual(self.call("messages.list")["result"]["messages"], [])
        self.assertEqual(self.call("operation.get", request_id="broken")["result"], {"found": False})


if __name__ == "__main__":
    unittest.main()
