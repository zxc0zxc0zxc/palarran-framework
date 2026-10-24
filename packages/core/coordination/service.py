"""Bounded authenticated single-host coordination, never remote execution."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import stat
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_REQUEST = 16 * 1024
MAX_RESPONSE = 32 * 1024
MAX_DATABASE = 128 * 1024 * 1024
MAX_RECEIPTS = 100000
MAX_ACKS = 100000
MAX_ROOMS = 100
MAX_MESSAGES = 2000
MAX_RESOURCES = 100
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z")
REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
RESOURCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}\Z")
KINDS = {"fact", "hypothesis", "question", "assignment", "blocker", "decision", "status", "result"}
MUTATIONS = {"room.ensure", "message.post", "ack", "claim.acquire", "claim.renew", "claim.release", "claim.reconcile"}
FIELDS = {
    "room.ensure": ({"project", "room", "title", "request_id"}, set()),
    "message.post": ({"project", "room", "kind", "text", "request_id"}, {"recipient"}),
    "messages.list": ({"project", "room"}, {"after", "limit"}),
    "ack": ({"project", "room", "message_seq", "request_id"}, set()),
    "claim.acquire": ({"project", "room", "resource", "ttl", "request_id"}, set()),
    "claim.renew": ({"project", "room", "claim_id", "fence", "ttl", "request_id"}, set()),
    "claim.release": ({"project", "room", "claim_id", "fence", "request_id"}, set()),
    "claims.list": ({"project", "room"}, {"after", "limit"}),
    "claim.reconcile": ({"project", "room", "claim_id", "fence", "observed_state", "request_id"}, set()),
    "operation.get": ({"project", "request_id"}, set()),
}


class CoordinationError(Exception):
    """Safe fixed error code; never contains source data."""


class CapacityError(CoordinationError):
    pass


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def decode(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("nonfinite")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def failure(code):
    return {"ok": False, "error": {"code": code}}


def success(result):
    return {"ok": True, "result": result}


def _identifier(value, pattern=IDENTIFIER):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise CoordinationError("invalid_request")


def _integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise CoordinationError("invalid_request")


def _text(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise CoordinationError("invalid_request")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise CoordinationError("invalid_request") from None


def _ancestors(path):
    """Reject symlink ancestors before creating/opening private state."""
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise CoordinationError("unsafe_path")
        if current.exists() and current != path and not current.is_dir():
            raise CoordinationError("unsafe_path")


def _private_file(path, required=True):
    _ancestors(path)
    if not path.exists():
        if required:
            raise CoordinationError("unsafe_path")
        return
    info = path.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600):
        raise CoordinationError("unsafe_path")


def load_credentials(path):
    path = Path(os.path.abspath(os.path.expanduser(str(path))))
    _private_file(path)
    if path.stat().st_size > 1024 * 1024:
        raise CoordinationError("invalid_credentials")
    try:
        with path.open("rb") as stream:
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("oversized")
        return decode(raw)
    except (OSError, ValueError, UnicodeError):
        raise CoordinationError("invalid_credentials") from None


def supported_sqlite(version=None):
    """Linked releases with the documented concurrent WAL-reset fix."""
    version = sqlite3.sqlite_version_info if version is None else version
    if (not isinstance(version, tuple) or len(version) != 3
            or any(type(part) is not int or part < 0 for part in version)):
        return False
    return (version >= (3, 51, 3)
            or version[:2] == (3, 50) and version >= (3, 50, 7)
            or version[:2] == (3, 44) and version >= (3, 44, 6))


class CoordinationStore:
    def __init__(self, db_path, credentials):
        if not supported_sqlite():
            raise CoordinationError("unsupported_sqlite")
        self.credentials = self._credentials(credentials)
        self.path = Path(os.path.abspath(os.path.expanduser(str(db_path))))
        _ancestors(self.path)
        if not self.path.parent.exists():
            # Only one private leaf directory is created; no arbitrary tree.
            self.path.parent.mkdir(mode=0o700)
        parent = self.path.parent.stat()
        if parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) != 0o700:
            raise CoordinationError("unsafe_path")
        for suffix in ("", "-wal", "-shm"):
            _private_file(Path(str(self.path) + suffix), required=False)
        if not self.path.exists():
            descriptor = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY
                                 | getattr(os, "O_NOFOLLOW", 0), 0o600)
            os.close(descriptor)
        try:
            connection = self._connect()
            try:
                existing = connection.execute("PRAGMA table_info(claims)").fetchall()
                if existing:
                    primary = [row["name"] for row in sorted(existing, key=lambda row: row["pk"]) if row["pk"]]
                    if primary != ["project", "resource"]:
                        raise CoordinationError("incompatible_schema")
                connection.executescript("""
                    CREATE TABLE IF NOT EXISTS rooms(
                        project TEXT NOT NULL, room TEXT NOT NULL, title TEXT NOT NULL,
                        PRIMARY KEY(project,room));
                    CREATE TABLE IF NOT EXISTS messages(
                        seq INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL,
                        room TEXT NOT NULL, actor TEXT NOT NULL, kind TEXT NOT NULL,
                        text TEXT NOT NULL, recipient TEXT, created_at INTEGER NOT NULL);
                    CREATE INDEX IF NOT EXISTS messages_room ON messages(project,room,seq);
                    CREATE TABLE IF NOT EXISTS acknowledgments(
                        message_seq INTEGER NOT NULL, actor TEXT NOT NULL, at INTEGER NOT NULL,
                        PRIMARY KEY(message_seq,actor));
                    CREATE TABLE IF NOT EXISTS claims(
                        project TEXT NOT NULL, room TEXT NOT NULL, resource TEXT NOT NULL,
                        claim_id TEXT NOT NULL, owner TEXT, fence INTEGER NOT NULL,
                        state TEXT NOT NULL, expires_at INTEGER,
                        PRIMARY KEY(project,resource));
                    CREATE UNIQUE INDEX IF NOT EXISTS claim_ids ON claims(claim_id);
                    CREATE TABLE IF NOT EXISTS receipts(
                        actor TEXT NOT NULL, request_id TEXT NOT NULL, project TEXT NOT NULL,
                        operation TEXT NOT NULL, payload_hash TEXT NOT NULL, response TEXT NOT NULL,
                        PRIMARY KEY(actor,request_id));
                """)
            finally:
                connection.close()
        except sqlite3.Error:
            raise CoordinationError("unavailable") from None

    @staticmethod
    def _credentials(credentials):
        if not isinstance(credentials, dict) or not 1 <= len(credentials) <= 1000:
            raise CoordinationError("invalid_credentials")
        result, actors = {}, set()
        for token, profile in credentials.items():
            if (not isinstance(token, str) or not 32 <= len(token) <= 512
                    or any(not 33 <= ord(char) <= 126 for char in token)):
                raise CoordinationError("invalid_credentials")
            if not isinstance(profile, dict) or set(profile) != {"actor", "projects", "role"}:
                raise CoordinationError("invalid_credentials")
            try:
                _identifier(profile["actor"])
                projects = profile["projects"]
                if (not isinstance(projects, list) or not 1 <= len(projects) <= 100
                        or profile["actor"] in actors or profile["role"] not in ("agent", "operator")):
                    raise CoordinationError("invalid_credentials")
                for project in projects:
                    _identifier(project)
                if len(set(projects)) != len(projects):
                    raise CoordinationError("invalid_credentials")
            except (TypeError, CoordinationError):
                raise CoordinationError("invalid_credentials") from None
            actors.add(profile["actor"])
            result[token] = {"actor": profile["actor"], "projects": tuple(projects), "role": profile["role"]}
        return result

    def _connect(self):
        connection = sqlite3.connect(str(self.path), timeout=1, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA wal_autocheckpoint=100")
        connection.execute("PRAGMA journal_size_limit=4194304")
        page_size = connection.execute("PRAGMA page_size").fetchone()[0]
        connection.execute("PRAGMA max_page_count=" + str(max(1, MAX_DATABASE // page_size)))
        return connection

    def authenticate(self, token):
        if not isinstance(token, str) or len(token) > 512:
            raise CoordinationError("unauthorized")
        principal = self.credentials.get(token)
        if principal is None:
            raise CoordinationError("unauthorized")
        return principal

    @staticmethod
    def _validate(operation, payload):
        if not isinstance(operation, str) or operation not in FIELDS:
            raise CoordinationError("unknown_operation")
        required, optional = FIELDS[operation]
        if not isinstance(payload, dict) or not required <= payload.keys() or payload.keys() - required - optional:
            raise CoordinationError("invalid_request")
        _identifier(payload["project"])
        for key in ("room", "recipient"):
            if key in payload:
                _identifier(payload[key])
        if "request_id" in payload:
            _identifier(payload["request_id"], REQUEST_ID)
        if "resource" in payload:
            _identifier(payload["resource"], RESOURCE)
        if "claim_id" in payload:
            _identifier(payload["claim_id"], REQUEST_ID)
        for key in ("message_seq", "fence"):
            if key in payload:
                _integer(payload[key], 1, 2**63-1)
        if "ttl" in payload:
            _integer(payload["ttl"], 30, 300)
        if "limit" in payload:
            _integer(payload["limit"], 1, 20)
        if "after" in payload:
            if operation == "messages.list":
                _integer(payload["after"], 0, 2**63-1)
            elif payload["after"] != "":
                _identifier(payload["after"], RESOURCE)
        if "title" in payload:
            _text(payload["title"], 160)
        for key in ("text", "observed_state"):
            if key in payload:
                _text(payload[key], 4000)
        if "kind" in payload and (not isinstance(payload["kind"], str) or payload["kind"] not in KINDS):
            raise CoordinationError("invalid_request")

    def dispatch(self, token, operation, payload):
        connection = None
        try:
            principal = self.authenticate(token)
            self._validate(operation, payload)
            if len(encode(payload)) > MAX_REQUEST:
                return failure("request_too_large")
            if payload["project"] not in principal["projects"]:
                return failure("forbidden")
            connection = self._connect()
            if operation not in MUTATIONS:
                if operation == "claims.list":
                    connection.execute("BEGIN IMMEDIATE")
                    self._expire(connection, payload)
                result = self._read(connection, principal, operation, payload)
                connection.commit()
                return success(result)
            connection.execute("BEGIN IMMEDIATE")
            digest = hashlib.sha256(encode(payload)).hexdigest()
            old = connection.execute("SELECT * FROM receipts WHERE actor=? AND request_id=?",
                                     (principal["actor"], payload["request_id"])).fetchone()
            if old:
                connection.rollback()
                if old["operation"] != operation or old["payload_hash"] != digest:
                    return failure("idempotency_conflict")
                return decode(old["response"].encode("utf-8"))
            size = sum(Path(str(self.path)+suffix).stat().st_size
                       for suffix in ("", "-wal", "-shm") if Path(str(self.path)+suffix).exists())
            if size >= MAX_DATABASE or connection.execute("SELECT count(*) FROM receipts").fetchone()[0] >= MAX_RECEIPTS:
                raise CapacityError("capacity_exhausted")
            try:
                if operation.startswith("claim."):
                    self._expire(connection, payload)
                result = self._mutate(connection, principal, operation, payload)
                result["request_id"] = payload["request_id"]
                response = success(result)
            except CapacityError:
                raise
            except CoordinationError as error:
                response = failure(error.args[0])
            raw = encode(response)
            if len(raw) > MAX_RESPONSE:
                raise CapacityError("capacity_exhausted")
            connection.execute("INSERT INTO receipts VALUES(?,?,?,?,?,?)",
                               (principal["actor"], payload["request_id"], payload["project"],
                                operation, digest, raw.decode("utf-8")))
            connection.commit()
            return response
        except CoordinationError as error:
            return failure(error.args[0])
        except (sqlite3.Error, OSError, ValueError, TypeError, OverflowError):
            return failure("unavailable")
        finally:
            if connection is not None:
                if connection.in_transaction:
                    connection.rollback()
                connection.close()

    @staticmethod
    def _expire(connection, payload):
        # Once observed expired, clock rollback cannot resurrect ownership.
        connection.execute("UPDATE claims SET state='blocked_pending_reconciliation' "
                           "WHERE project=? AND state='active' AND expires_at<=?",
                           (payload["project"], int(time.time())))

    @staticmethod
    def _room(connection, payload):
        row = connection.execute("SELECT * FROM rooms WHERE project=? AND room=?",
                                 (payload["project"], payload["room"])).fetchone()
        if row is None:
            raise CoordinationError("room_missing")
        return row

    @staticmethod
    def _message(row):
        return {name: row[name] for name in ("seq", "actor", "kind", "text", "recipient", "created_at")}

    @staticmethod
    def _claim(row):
        result = {name: row[name] for name in ("room", "resource", "claim_id", "owner", "fence", "state", "expires_at")}
        if result["state"] == "active" and result["expires_at"] <= int(time.time()):
            result["state"] = "blocked_pending_reconciliation"
        return result

    def _read(self, connection, principal, operation, payload):
        if operation == "operation.get":
            row = connection.execute("SELECT * FROM receipts WHERE actor=? AND request_id=? AND project=?",
                                     (principal["actor"], payload["request_id"], payload["project"])).fetchone()
            return {"found": False} if row is None else {"found": True, "operation": row["operation"],
                                                        "receipt": decode(row["response"].encode("utf-8"))}
        self._room(connection, payload)
        project, room = payload["project"], payload["room"]
        if operation == "claims.list":
            after, limit = payload.get("after", ""), payload.get("limit", 5)
            rows = connection.execute("SELECT * FROM claims WHERE project=? AND resource>? ORDER BY resource LIMIT ?",
                                      (project, after, limit+1)).fetchall()
            claims = [self._claim(row) for row in rows[:limit]]
            return {"claims": claims, "next_cursor": claims[-1]["resource"] if claims else after,
                    "has_more": len(rows) > limit}
        after, limit = payload.get("after", 0), payload.get("limit", 20)
        rows = connection.execute("SELECT * FROM messages WHERE project=? AND room=? AND seq>? ORDER BY seq LIMIT ?",
                                  (project, room, after, limit+1)).fetchall()
        result = {"messages": [], "next_cursor": after, "has_more": False}
        for row in rows[:limit]:
            message = self._message(row)
            trial = {"messages": result["messages"]+[message], "next_cursor": message["seq"], "has_more": True}
            if len(encode(success(trial))) > MAX_RESPONSE:
                break
            result["messages"].append(message)
            result["next_cursor"] = message["seq"]
        result["has_more"] = len(rows) > len(result["messages"])
        return result

    def _mutate(self, connection, principal, operation, payload):
        project, room, actor = payload["project"], payload["room"], principal["actor"]
        if operation == "room.ensure":
            old = connection.execute("SELECT title FROM rooms WHERE project=? AND room=?", (project, room)).fetchone()
            if old and old["title"] != payload["title"]:
                raise CoordinationError("room_conflict")
            if old is None:
                if connection.execute("SELECT count(*) FROM rooms WHERE project=?", (project,)).fetchone()[0] >= MAX_ROOMS:
                    raise CapacityError("capacity_exhausted")
                connection.execute("INSERT INTO rooms VALUES(?,?,?)", (project, room, payload["title"]))
            return {"project": project, "room": room, "title": payload["title"]}
        self._room(connection, payload)
        if operation == "message.post":
            recipient = payload.get("recipient")
            if recipient is not None and not any(x["actor"] == recipient and project in x["projects"]
                                                 for x in self.credentials.values()):
                raise CoordinationError("forbidden")
            if connection.execute("SELECT count(*) FROM messages WHERE project=? AND room=?", (project, room)).fetchone()[0] >= MAX_MESSAGES:
                raise CapacityError("capacity_exhausted")
            cursor = connection.execute("INSERT INTO messages(project,room,actor,kind,text,recipient,created_at) VALUES(?,?,?,?,?,?,?)",
                                        (project, room, actor, payload["kind"], payload["text"], recipient, int(time.time())))
            row = connection.execute("SELECT * FROM messages WHERE seq=?", (cursor.lastrowid,)).fetchone()
            return {"message": self._message(row)}
        if operation == "ack":
            row = connection.execute("SELECT 1 FROM messages WHERE seq=? AND project=? AND room=?",
                                     (payload["message_seq"], project, room)).fetchone()
            if row is None:
                raise CoordinationError("message_missing")
            old = connection.execute("SELECT at FROM acknowledgments WHERE message_seq=? AND actor=?",
                                     (payload["message_seq"], actor)).fetchone()
            if old is None:
                if connection.execute("SELECT count(*) FROM acknowledgments").fetchone()[0] >= MAX_ACKS:
                    raise CapacityError("capacity_exhausted")
                at = int(time.time())
                connection.execute("INSERT INTO acknowledgments VALUES(?,?,?)", (payload["message_seq"], actor, at))
            else:
                at = old["at"]
            return {"message_seq": payload["message_seq"], "actor": actor, "acknowledged_at": at}
        if operation == "claim.acquire":
            row = connection.execute("SELECT * FROM claims WHERE project=? AND resource=?",
                                     (project, payload["resource"])).fetchone()
            if row and row["state"] != "released":
                if self._claim(row)["state"] == "blocked_pending_reconciliation":
                    raise CoordinationError("reconciliation_required")
                raise CoordinationError("resource_busy")
            if row is None and connection.execute("SELECT count(*) FROM claims WHERE project=?", (project,)).fetchone()[0] >= MAX_RESOURCES:
                raise CapacityError("capacity_exhausted")
            fence = 1 if row is None else row["fence"] + 1
            if fence >= 2**63:
                raise CapacityError("capacity_exhausted")
            resource, claim_id = payload["resource"], uuid.uuid4().hex
            connection.execute("INSERT OR REPLACE INTO claims VALUES(?,?,?,?,?,?,?,?)",
                               (project, room, resource, claim_id, actor, fence, "active", int(time.time())+payload["ttl"]))
        else:
            row = connection.execute("SELECT * FROM claims WHERE project=? AND room=? AND claim_id=?",
                                     (project, room, payload["claim_id"])).fetchone()
            if row is None or row["fence"] != payload["fence"]:
                raise CoordinationError("stale_claim")
            resource, claim_id, fence = row["resource"], row["claim_id"], row["fence"]
            if operation == "claim.reconcile":
                if principal["role"] != "operator":
                    raise CoordinationError("operator_required")
                if row["state"] == "released":
                    raise CoordinationError("stale_claim")
                if fence+1 >= 2**63:
                    raise CapacityError("capacity_exhausted")
                connection.execute("UPDATE claims SET owner=NULL,fence=?,state='released',expires_at=NULL WHERE claim_id=?",
                                   (fence+1, claim_id))
                # observed_state is bound into the immutable receipt payload hash;
                # retain the compact operator note with the reconciliation receipt.
                return {"claim": self._claim(connection.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()),
                        "observed_state": payload["observed_state"]}
            if row["owner"] != actor:
                raise CoordinationError("forbidden")
            if self._claim(row)["state"] == "blocked_pending_reconciliation":
                raise CoordinationError("reconciliation_required")
            if row["state"] != "active":
                raise CoordinationError("stale_claim")
            if operation == "claim.release":
                connection.execute("UPDATE claims SET owner=NULL,state='released',expires_at=NULL WHERE claim_id=?", (claim_id,))
            else:
                connection.execute("UPDATE claims SET expires_at=? WHERE claim_id=?", (int(time.time())+payload["ttl"], claim_id))
        return {"claim": self._claim(connection.execute("SELECT * FROM claims WHERE project=? AND room=? AND resource=?",
                                                        (project, room, resource)).fetchone())}


HTTP_CODES = {"unauthorized": 401, "forbidden": 403, "operator_required": 403,
              "idempotency_conflict": 409, "room_conflict": 409, "resource_busy": 409,
              "stale_claim": 409, "reconciliation_required": 409, "capacity_exhausted": 429,
              "request_too_large": 413, "unavailable": 503}


class CoordinationHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = True
    request_queue_size = 16

    def __init__(self, address, handler):
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(address, handler)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        # Do not print exceptions, headers, bodies or tokens.
        pass


def create_server(store, host="127.0.0.1", port=0, *, container_network=False):
    if type(container_network) is not bool or host not in (("127.0.0.1", "0.0.0.0") if container_network else ("127.0.0.1",)) or type(port) is not int or not 0 <= port <= 65535:
        raise CoordinationError("invalid_request")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def setup(self):
            self.request.settimeout(2)
            super().setup()

        def log_message(self, format, *args):
            pass

        def send_error(self, code, message=None, explain=None):
            self._reply(failure("invalid_request"), code if 400 <= code <= 599 else 400)

        def _reply(self, response, status=None):
            raw = encode(response)
            if len(raw) > MAX_RESPONSE:
                response, raw = failure("capacity_exhausted"), encode(failure("capacity_exhausted"))
            code = 200 if response["ok"] else HTTP_CODES.get(response["error"]["code"], 400)
            self.send_response(code if status is None else status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            try:
                auth = self.headers.get_all("Authorization", [])
                if len(auth) != 1 or not auth[0].startswith("Bearer "):
                    self._reply(failure("unauthorized"))
                    return
                token = auth[0][7:]
                store.authenticate(token)  # Authenticate before reading request JSON.
                if not self.path.startswith("/v1/") or self.path[4:] not in FIELDS:
                    self._reply(failure("unknown_operation"))
                    return
                lengths = self.headers.get_all("Content-Length", [])
                if (len(lengths) != 1 or not lengths[0].isdigit()
                        or self.headers.get("Transfer-Encoding") is not None
                        or self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json"):
                    self._reply(failure("invalid_request"))
                    return
                length = int(lengths[0])
                if length > MAX_REQUEST:
                    self._reply(failure("request_too_large"))
                    return
                raw = self.rfile.read(length)
                if len(raw) != length:
                    self._reply(failure("invalid_request"))
                    return
                payload = decode(raw)
                self._reply(store.dispatch(token, self.path[4:], payload))
            except CoordinationError as error:
                self._reply(failure(error.args[0]))
            except (ValueError, UnicodeError, TypeError):
                self._reply(failure("invalid_request"))
            except (OSError, socket.timeout):
                # Broken clients/timeouts cannot safely receive another reply.
                self.close_connection = True

    return CoordinationHTTPServer(("0.0.0.0" if container_network else host, port), Handler)


def main():
    parser = argparse.ArgumentParser(description="Private loopback agent coordination")
    parser.add_argument("--db", required=True)
    parser.add_argument("--credentials", required=True)
    parser.add_argument("--port", type=int, default=18792)
    parser.add_argument("--container-network", action="store_true", help="Explicit private-container bridge mode; never publish publicly")
    args = parser.parse_args()
    server = None
    try:
        store = CoordinationStore(args.db, load_credentials(args.credentials))
        server = create_server(store, port=args.port, container_network=args.container_network)
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except CoordinationError as error:
        print("Coordination startup failed: " + error.args[0])
        return 2
    except (OSError, sqlite3.Error):
        print("Coordination startup failed; verify private configuration.")
        return 2
    finally:
        if server is not None:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
