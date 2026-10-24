"""Independent synthetic sharing protocol cases: no model or deployed service calls."""
import copy
import json
import tempfile
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from packages.core.coordination import share, service


NOW = 1000
PLAN = "a" * 64
BASE = "b" * 40
PROOF = "c" * 64
TOKENS = {name: char * 40 for name, char in (("alice", "a"), ("bob", "b"), ("carol", "c"), ("other", "z"))}
CREDENTIALS = {token: {"actor": name, "projects": ["beta" if name == "other" else "alpha"], "role": "agent"}
               for name, token in TOKENS.items()}


def offer(mode="new"):
    return dict(share_id="share-1", task_id="task-1", run_id="sender-run", repository="repo", room="feature",
                mode=mode, plan_hash=PLAN, base_commit=BASE, expires_at=NOW+100,
                card=dict(goal="Build export", outcome="Verified export", estimate="Small task",
                          uncertainties=["format"], tools=["python"], data_categories=["source"], checks=["contract"]),
                scope=dict(files=["src/export.py"], resources=["export"], actions=["edit"], contracts=["api"]),
                limits=dict(tokens=1000, cost_micros=10000, seconds=100), backend="local")


class ShareReducerTests(unittest.TestCase):
    def setUp(self):
        self.state = share.create(offer(), "alice", NOW)
        self.seq = 0

    def event(self, kind, actor="alice", data=None, **overrides):
        self.seq += 1
        event = dict(event_id="event-%d" % self.seq, kind=kind,
                     assignment_generation=self.state["assignment_generation"], plan_hash=PLAN, data=data or {})
        event.update(overrides)
        self.state = share.apply(self.state, event, actor, NOW+1)
        return event

    def ready(self, mode="new", transfer=True):
        self.state = share.create(offer(mode), "alice", NOW)
        self.event("offered", "bob", dict(offer_id="offer-bob", limits=offer()["limits"]))
        self.event("assigned", data=dict(offer_id="offer-bob"))
        self.event("plan_proposed")
        self.event("plan_accepted", "bob")
        if mode == "continue":
            self.event("checkpoint_published", data=dict(commit=BASE, remote="origin", branch="continuation", evidence_sha256=PROOF))
        self.event("receiver_ready", "bob", dict(commit=BASE, evidence_sha256=PROOF, session_id="receiver-session", local_run_id="receiver-run"))
        if transfer:
            self.event("ownership_transferred", data=dict(stopped=True, unknown_operations=False, usage_known=True,
                                                          tokens=100, cost_micros=100, evidence_sha256=PROOF))
        return self.state

    def started(self):
        self.ready()
        self.event("started", "bob", dict(session_id="receiver-session", local_run_id="receiver-run"))

    def test_no_consent_or_readiness_cannot_start(self):
        before = copy.deepcopy(self.state)
        with self.assertRaises(share.ShareError):
            self.event("started", "bob", dict(session_id="receiver-session", local_run_id="receiver-run"))
        self.assertEqual(self.state, before)
        self.ready(transfer=False)
        with self.assertRaises(share.ShareError):
            self.event("started", "bob", dict(session_id="receiver-session", local_run_id="receiver-run"))
        self.assertEqual(self.state["owner"], "alice")

    def test_replay_preserves_attempt_and_conflict_is_rejected(self):
        self.ready()
        event = self.event("started", "bob", dict(session_id="receiver-session", local_run_id="receiver-run"))
        before = copy.deepcopy(self.state)
        self.assertEqual(share.apply(self.state, event, "bob", NOW+2), before)
        self.assertEqual(self.state["attempt_id"], 1)
        changed = copy.deepcopy(event); changed["data"]["session_id"] = "changed"
        with self.assertRaisesRegex(share.ShareError, "idempotency_conflict"):
            share.apply(self.state, changed, "bob", NOW+2)
        self.assertEqual(self.state, before)

    def test_stale_generation_and_changed_plan_do_not_modify_owner(self):
        self.ready()
        for overrides in (dict(assignment_generation=0), dict(plan_hash="d"*64)):
            with self.assertRaises(share.ShareError):
                self.event("started", "bob", dict(session_id="receiver-session", local_run_id="receiver-run"), **overrides)
        self.assertEqual((self.state["owner"], self.state["status"]), ("bob", "ready"))

    def test_expiry_blocks_start_without_releasing_active_owner(self):
        self.ready()
        event = dict(event_id="late", kind="started", assignment_generation=1, plan_hash=PLAN,
                     data=dict(session_id="receiver-session", local_run_id="receiver-run"))
        with self.assertRaisesRegex(share.ShareError, "expired"):
            share.apply(self.state, event, "bob", NOW+101)
        self.assertEqual(self.state["owner"], "bob")

    def test_expired_negotiation_has_explicit_terminal_record(self):
        event = dict(event_id="expiry", kind="expired", assignment_generation=0, plan_hash=PLAN, data={})
        state = share.apply(self.state, event, "alice", NOW+101)
        self.assertEqual(state["status"], "expired")

    def test_unknown_operations_and_missing_stop_block_transfer(self):
        self.ready(transfer=False)
        for stopped, unknown in ((False, False), (True, True)):
            with self.assertRaisesRegex(share.ShareError, "reconciliation_required"):
                self.event("ownership_transferred", data=dict(stopped=stopped, unknown_operations=unknown, usage_known=False,
                                                              tokens=None, cost_micros=None, evidence_sha256=PROOF))
        self.assertEqual((self.state["owner"], self.state["assignment_generation"]), ("alice", 0))

    def test_cancellation_requires_stop_and_late_result_never_accepts(self):
        self.started()
        self.event("cancel_requested")
        with self.assertRaises(share.ShareError):
            self.event("cancelled", "bob", dict(stopped=False, usage_known=True, tokens=20, cost_micros=30, evidence_sha256=PROOF))
        self.assertEqual(self.state["owner"], "bob")
        self.event("cancelled", "bob", dict(stopped=True, usage_known=True, tokens=20, cost_micros=30, evidence_sha256=PROOF))
        with self.assertRaises(share.ShareError):
            self.event("result_submitted", "bob", dict(subject=BASE, evidence_sha256=PROOF, checks={"contract":"PASS"},
                                                      stopped=True, usage_known=True, tokens=20, cost_micros=30))
        self.assertEqual(self.state["status"], "cancelled")
        self.assertEqual(self.state["usage"]["alice"]["tokens"], 100)
        self.assertEqual(self.state["usage"]["bob"]["tokens"], 20)

    def test_confirmed_spend_cannot_disappear_when_next_usage_is_unknown(self):
        self.started()
        self.event("progress", "bob", dict(completed=["parse"], blockers=[], next="verify", usage_known=True, tokens=20, cost_micros=30))
        try:
            self.event("progress", "bob", dict(completed=["parse"], blockers=[], next="verify", usage_known=False, tokens=None, cost_micros=None))
        except share.ShareError:
            pass
        self.assertGreaterEqual(self.state["usage"]["bob"]["tokens"], 20)
        self.assertGreaterEqual(self.state["usage"]["bob"]["cost_micros"], 30)

    def test_receiver_limit_expansion_and_actor_forgery_rejected(self):
        increased = dict(offer()["limits"], tokens=1001)
        with self.assertRaisesRegex(share.ShareError, "scope_expansion"):
            self.event("offered", "bob", dict(offer_id="offer-bob", limits=increased))
        self.ready()
        with self.assertRaises(share.ShareError):
            self.event("started", "carol", dict(session_id="receiver-session", local_run_id="receiver-run"))

    def test_bad_nested_types_and_secret_fields_fail_safely(self):
        for value in ([{}], [[]], [True]):
            malformed = offer(); malformed["scope"]["files"] = value
            with self.assertRaises(share.ShareError):
                share.create(malformed, "alice", NOW)
        for location in ("offer", "card", "scope"):
            malformed = offer()
            (malformed if location == "offer" else malformed[location])["api_key"] = "secret-fixture"
            with self.assertRaises(share.ShareError):
                share.create(malformed, "alice", NOW)

    def test_continuation_requires_matching_published_checkpoint(self):
        self.state = share.create(offer("continue"), "alice", NOW)
        self.event("offered", "bob", dict(offer_id="offer-bob", limits=offer()["limits"]))
        self.event("assigned", data=dict(offer_id="offer-bob")); self.event("plan_proposed"); self.event("plan_accepted", "bob")
        payload=dict(commit=BASE, evidence_sha256=PROOF, session_id="receiver-session", local_run_id="receiver-run")
        with self.assertRaisesRegex(share.ShareError, "checkpoint_mismatch"):
            self.event("receiver_ready", "bob", payload)
        self.event("checkpoint_published", data=dict(commit="d"*40, remote="origin", branch="checkpoint", evidence_sha256=PROOF))
        with self.assertRaisesRegex(share.ShareError, "checkpoint_mismatch"):
            self.event("receiver_ready", "bob", payload)


    # Exercise the separately accounted receiver dispatcher without provider calls.
    def test_receiver_launch_once_and_separate_dispatcher_run(self):
        from test_parallel_dispatcher import manifest, FakeAdapter, verify
        from packages.core.parallelism.dispatcher import Dispatcher
        from packages.core.setup.temporal_config import TemporalProfile
        from packages.core.coordination import share_runtime
        self.ready()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            dispatcher = Dispatcher(root / "private" / "dispatch.sqlite")
            value = manifest(root, workers=1, count=1, run_id="receiver-run")
            value["base_commit"] = BASE
            task = value["tasks"][0]
            task.update(base_commit=BASE, owner="bob", session_id="receiver-session", files=["src/export.py"],
                        resources=["export"], actions=["edit"], tools=["python"], contracts={"share_plan_hash": PLAN})
            adapter = FakeAdapter()
            def get_state(share_id):
                self.assertEqual(share_id, "share-1")
                return copy.deepcopy(self.state)
            def send(share_id, event):
                self.state = share.apply(self.state, event, "bob", NOW+1)
                return copy.deepcopy(self.state)
            kwargs = dict(get_share=get_state, send_event=send, share_id="share-1", actor="bob", manifest=value,
                          profile=TemporalProfile(False, "fixture"), adapter=adapter, verifier=verify)
            result = share_runtime.execute_received(dispatcher, **kwargs)
            self.assertEqual(result["status"], "verified", result)
            self.assertEqual(len(adapter.calls), 1)
            self.assertEqual(dispatcher.get_run("receiver-run")["usage"]["tokens"], 10)
            with self.assertRaises(share.ShareError):
                share_runtime.execute_received(dispatcher, **kwargs)
            self.assertEqual(len(adapter.calls), 1)


    def test_lost_start_reply_keeps_intent_and_never_calls_adapter_twice(self):
        from test_parallel_dispatcher import manifest, FakeAdapter, verify
        from packages.core.parallelism.dispatcher import Dispatcher
        from packages.core.setup.temporal_config import TemporalProfile
        from packages.core.coordination import share_runtime
        self.ready()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            dispatcher = Dispatcher(root / "private" / "dispatch.sqlite")
            value = manifest(root, workers=1, count=1, run_id="receiver-run")
            value["base_commit"] = BASE
            value["tasks"][0].update(base_commit=BASE, owner="bob", session_id="receiver-session", files=["src/export.py"],
                resources=["export"], actions=["edit"], tools=["python"], contracts={"share_plan_hash": PLAN})
            adapter = FakeAdapter()
            sends = []
            def lost(share_id, event):
                sends.append(event)
                raise OSError("synthetic lost reply")
            kwargs = dict(get_share=lambda _: copy.deepcopy(self.state), send_event=lost, share_id="share-1", actor="bob",
                          manifest=value, profile=TemporalProfile(False, "fixture"), adapter=adapter, verifier=verify)
            result = share_runtime.execute_received(dispatcher, **kwargs)
            self.assertEqual(result["status"], "unknown")
            self.assertTrue(result["reconciliation_required"])
            replay = share_runtime.execute_received(dispatcher, **kwargs)
            self.assertFalse(replay["launched"])
            self.assertTrue(replay["reconciliation_required"])
            self.assertEqual(len(sends), 1)
            self.assertEqual(adapter.calls, [])


class ShareStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name).resolve() / "private" / "bus.sqlite"
        self.store = service.CoordinationStore(self.path, CREDENTIALS)
        self.seq = 0
        self.clock = patch("packages.core.coordination.share_store.time.time", return_value=NOW)
        self.clock.start()
        self.call("room.ensure", room="feature", title="Sharing fixture")

    def tearDown(self):
        self.clock.stop()
        self.tmp.cleanup()

    def call(self, op, actor="alice", **values):
        self.seq += 1
        payload = dict(project="alpha", **values)
        if op in service.MUTATIONS:
            payload.setdefault("request_id", "request-%d" % self.seq)
        return self.store.dispatch(TOKENS[actor], op, payload)

    def create(self, **values):
        result = self.call("share.create", offer=offer(), confirmed=True, **values)
        self.assertTrue(result["ok"], result)
        return result

    def event(self, kind, actor="alice", data=None, event_id=None, request_id=None, confirmed=True):
        event = dict(event_id=event_id or "event-%d" % (self.seq+1), kind=kind,
                     assignment_generation=0, plan_hash=PLAN, data=data or {})
        payload = dict(share_id="share-1", event=event)
        if request_id:
            payload["request_id"] = request_id
        if confirmed is not None:
            payload["confirmed"] = confirmed
        return self.call("share.event", actor=actor, **payload)

    def test_consent_is_required_both_sides_and_ack_does_not_replace_it(self):
        denied = self.call("share.create", offer=offer(), confirmed=False)
        self.assertFalse(denied["ok"])
        self.assertFalse(self.call("share.get", share_id="share-1")["ok"])
        self.create()
        notice = self.call("messages.list", room="feature")["result"]["messages"][0]
        self.assertTrue(self.call("ack", actor="bob", room="feature", message_seq=notice["seq"])["ok"])
        denied = self.event("offered", "bob", dict(offer_id="offer-bob", limits=offer()["limits"]), confirmed=None)
        self.assertEqual(denied["error"]["code"], "confirmation_required")
        state = self.call("share.get", share_id="share-1")["result"]["share"]
        self.assertEqual(state["offers"], {})
        self.assertEqual(state["status"], "requested")

    def test_two_responders_and_concurrent_selection_have_one_assignment(self):
        self.create()
        for actor in ("bob", "carol"):
            self.assertTrue(self.event("offered", actor, dict(offer_id="offer-"+actor, limits=offer()["limits"]))["ok"])
        barrier = threading.Barrier(2)
        def assign(actor):
            barrier.wait()
            event = dict(event_id="choose-"+actor, kind="assigned", assignment_generation=0, plan_hash=PLAN,
                         data=dict(offer_id="offer-"+actor))
            return self.store.dispatch(TOKENS["alice"], "share.event", dict(project="alpha", request_id="choose-"+actor,
                share_id="share-1", event=event, confirmed=True))
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(assign, ("bob", "carol")))
        self.assertEqual(sum(result["ok"] for result in outcomes), 1)
        state = self.call("share.get", share_id="share-1")["result"]["share"]
        self.assertEqual(state["status"], "assigned")
        self.assertIn(state["receiver"], ("bob", "carol"))
        self.assertEqual(sum(item["kind"] == "assigned" for item in state["history"]), 1)

    def test_restart_replay_and_conflicting_request_do_not_repeat_notice(self):
        first = self.create(request_id="stable")
        self.store = service.CoordinationStore(self.path, CREDENTIALS)
        replay = self.call("share.create", offer=offer(), confirmed=True, request_id="stable")
        self.assertEqual(first, replay)
        changed = offer(); changed["card"]["goal"] = "Changed"
        self.assertEqual(self.call("share.create", offer=changed, confirmed=True, request_id="stable")["error"]["code"], "idempotency_conflict")
        receipt = self.call("operation.get", request_id="stable")["result"]
        self.assertEqual(receipt["receipt"], first)
        notices = self.call("messages.list", room="feature")["result"]["messages"]
        self.assertEqual(len(notices), 1)

    def test_actor_project_isolation_and_notification_redaction(self):
        self.create()
        self.assertEqual(self.call("share.get", actor="other", share_id="share-1")["error"]["code"], "forbidden")
        spoof = dict(project="alpha", share_id="share-1", actor="alice")
        self.assertEqual(self.store.dispatch(TOKENS["bob"], "share.get", spoof)["error"]["code"], "invalid_request")
        notices = self.call("messages.list", room="feature")["result"]["messages"]
        notice = json.loads(notices[0]["text"])
        self.assertEqual(set(notice), {"share_id", "event", "assignment_generation", "plan_hash", "state_sha256"})
        serialized = json.dumps(notices)
        for private in ("Build export", "src/export.py", "10000", "api_key"):
            self.assertNotIn(private, serialized)

    def test_linked_round_requires_stopped_predecessor_and_keeps_usage(self):
        self.create()
        next_offer = offer(); next_offer.update(share_id="share-2", previous_share_id="share-1")
        denied = self.call("share.create", offer=next_offer, confirmed=True)
        self.assertFalse(denied["ok"])
        self.assertTrue(self.event("cancel_requested")["ok"])
        self.assertTrue(self.event("cancelled", data=dict(stopped=True, usage_known=False, tokens=45,
                                                          cost_micros=60, evidence_sha256=PROOF))["ok"])
        wrong = copy.deepcopy(next_offer); wrong["task_id"] = "another-task"
        self.assertFalse(self.call("share.create", offer=wrong, confirmed=True)["ok"])
        created = self.call("share.create", offer=next_offer, confirmed=True)
        self.assertTrue(created["ok"], created)
        inherited = created["result"]["share"]["prior_usage"]["share-1"]["alice"]
        self.assertEqual(inherited, dict(usage_known=False, tokens=45, cost_micros=60))

    def test_malformed_event_has_safe_error_without_transition(self):
        self.create()
        for malformed in (None, [], "secret-fixture"):
            response = self.call("share.event", share_id="share-1", event=malformed, confirmed=True)
            self.assertFalse(response["ok"])
            self.assertIn(response["error"]["code"], ("invalid_request", "unavailable"))
        self.assertEqual(self.call("share.get", share_id="share-1")["result"]["share"]["status"], "requested")

    def test_receipt_failure_rolls_back_state_and_notice(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TRIGGER reject_receipt BEFORE INSERT ON receipts BEGIN SELECT RAISE(ABORT,'private fixture'); END")
        denied = self.call("share.create", offer=offer(), confirmed=True)
        self.assertFalse(denied["ok"])
        self.assertFalse(self.call("share.get", share_id="share-1")["ok"])
        self.assertEqual(self.call("messages.list", room="feature")["result"]["messages"], [])


if __name__ == "__main__":
    unittest.main()
