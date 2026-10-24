"""Bounded single-owner knowledge API; no model calls or arbitrary queries."""

import argparse
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

MAX_BODY = 1024 * 1024
RELATIONS = ('RELATES_TO', 'SUPERSEDES', 'CONTRADICTS', 'VALIDATED_BY')
READ = {'search', 'get', 'neighbors', 'artifact'}
AGENT = READ | {'propose', 'feedback'}
REVIEWER = AGENT | {'promote', 'link'}


class Rejected(ValueError):
    pass


def require(condition):
    if not condition:
        raise Rejected('Request rejected; check documented fields, scope and bounds.')


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result)
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: require(False))


def fields(obj, required, optional=()):
    require(type(obj) is dict and set(required) <= set(obj) <= set(required) | set(optional))


def text(value, size=2048):
    require(type(value) is str and 0 < len(value) <= size and bool(value.strip()))
    require(all(c in '\n\t' or (ord(c) >= 32 and ord(c) != 127) for c in value))
    encode(value)
    return value


def alias(value):
    text(value, 80)
    require(re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}', value) is not None)
    return value


def digest(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None)
    return value


def string_list(value, count=16, size=256):
    require(type(value) is list and 0 < len(value) <= count)
    for item in value:
        text(item, size)
    require(len(set(value)) == len(value))


def privacy(value):
    # Conservative guard, not a complete PII/secret detector. Human review remains required.
    require(not re.search(r'-----BEGIN .*PRIVATE KEY|(?:password|api[_-]?key|token|secret)\s*[:=]\s*[\w/+.-]{8,}|gh[pousr]_[A-Za-z0-9]{20,}', value, re.I))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Rejected('Redirect rejected.')


class Neo4j:
    def __init__(self, url, password, *, container_network=False):
        require(type(container_network) is bool)
        parsed = urlsplit(url)
        require(parsed.scheme == 'http' and (parsed.hostname in ('127.0.0.1', 'localhost') or
                (container_network and url in ('http://graph:7474', 'http://graph:7474/'))))
        require(not parsed.username and not parsed.password and not parsed.query and not parsed.fragment and parsed.path in ('', '/'))
        require(type(password) is str and len(password) >= 16)
        self.url = url.rstrip('/') + '/db/neo4j/query/v2'
        self.authorization = 'Basic ' + base64.b64encode(('neo4j:' + password).encode()).decode()
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def query(self, statement, parameters=None):
        request = Request(self.url, data=encode(dict(statement=statement, parameters=parameters or {})),
                          headers={'Authorization': self.authorization, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with self.opener.open(request, timeout=10) as response:
                raw = response.read(MAX_BODY + 1)
            require(len(raw) <= MAX_BODY)
            body = parse(raw)
            require(type(body) is dict and not body.get('errors'))
            data = body['data']
            names, rows = data['fields'], data['values']
            require(type(names) is list and type(rows) is list and len(rows) <= 1000)
            require(all(type(row) is list and len(row) == len(names) for row in rows))
            return [dict(zip(names, row)) for row in rows]
        except Exception as error:
            # Never leak database messages, request data or credentials. No automatic write replay.
            raise Rejected('Database outcome unavailable; reconcile by deterministic ID before retry.') from error

    def initialize(self):
        for statement in (
            'CREATE CONSTRAINT memory_case_id IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE',
            'CREATE CONSTRAINT memory_project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE',
            'CREATE CONSTRAINT memory_artifact_id IF NOT EXISTS FOR (a:Artifact) REQUIRE a.id IS UNIQUE',
            'CREATE CONSTRAINT memory_feedback_id IF NOT EXISTS FOR (f:Feedback) REQUIRE f.id IS UNIQUE',
            'CREATE CONSTRAINT memory_review_id IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE',
            'CREATE CONSTRAINT memory_chunk_id IF NOT EXISTS FOR (n:ArtifactChunk) REQUIRE n.id IS UNIQUE',
            'CREATE FULLTEXT INDEX memory_cases IF NOT EXISTS FOR (c:Case) ON EACH [c.title,c.search_text]',
            'CREATE FULLTEXT INDEX memory_search IF NOT EXISTS FOR (n:Case|ArtifactChunk) ON EACH [n.title,n.search_text]',
        ):
            self.query(statement)


class Artifacts:
    def __init__(self, root, quota=4 * 1024**3):
        self.root = Path(root).absolute()
        require(not any(p.is_symlink() for p in (self.root, *self.root.parents)))
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        require(self.root.is_dir())
        os.chmod(self.root, 0o700)
        self.quota = quota

    def put(self, value):
        raw = text(value, 131072).encode('utf-8')
        require(len(raw) <= 131072)
        privacy(value)
        key = hashlib.sha256(raw).hexdigest()
        target = self.root / key
        if target.exists() or target.is_symlink():
            require(self.read(key) == raw)
            return key
        total = sum(p.stat().st_size for p in self.root.iterdir() if p.is_file() and not p.is_symlink())
        require(total + len(raw) <= self.quota)
        temp = self.root / ('.pending-' + secrets.token_hex(16))
        try:
            fd = os.open(str(temp), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            # Atomic no-overwrite publication; quota assumes a single service writer.
            try:
                os.link(str(temp), str(target), follow_symlinks=False)
            except FileExistsError:
                require(self.read(key) == raw)
            directory = os.open(str(self.root), os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            temp.unlink(missing_ok=True)
        return key

    def read(self, key):
        digest(key)
        fd = os.open(str(self.root / key), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        import stat
        with os.fdopen(fd, 'rb') as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode))
            raw = stream.read(131073)
        require(len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == key)
        return raw


class Knowledge:
    def __init__(self, database, artifacts):
        self.db, self.artifacts = database, artifacts

    def get(self, key, project, feedback_offset=0, review_offset=0):
        rows = self.db.query('/* get */ MATCH (c:Case {id:$id}) WHERE c.status="global" OR c.repo=$project OPTIONAL MATCH (c)-[attachment:HAS_ARTIFACT]->(a:Artifact) RETURN c.payload AS payload,c.status AS status,c.reason AS reason,collect(CASE WHEN a IS NULL THEN null ELSE {id:a.id,type:attachment.type,summary:attachment.summary} END) AS artifacts', dict(id=key, project=project))
        require(len(rows) == 1)
        row = rows[0]
        feedback = self.db.query('/* feedback_read */ MATCH (:Case {id:$id})-[:HAS_FEEDBACK]->(f:Feedback) RETURN f.id AS id,f.repo AS project,f.commit AS commit,f.outcome AS outcome,f.note AS note,f.evidence AS evidence ORDER BY id SKIP $offset LIMIT 4', dict(id=key,offset=feedback_offset))
        # Stable IDs; concurrent insertions require restarting pagination.
        reviews = self.db.query('/* review_read */ MATCH (:Case {id:$id})-[:HAS_REVIEW]->(r:Review) RETURN r.id AS id,r.status AS status,r.reason AS reason,toString(r.created_at) AS created_at ORDER BY id SKIP $offset LIMIT 4',dict(id=key,offset=review_offset))
        return dict(id=key, case=json.loads(row['payload']), status=row['status'], review_reason=row.get('reason'), artifacts=row['artifacts'], feedback=feedback[:3], next_feedback_offset=feedback_offset+3 if len(feedback)>3 else None, reviews=reviews[:3], next_review_offset=review_offset+3 if len(reviews)>3 else None)

    def execute(self, operation, args, role='agent'):
        require(operation in (REVIEWER if role == 'reviewer' else AGENT))
        require(type(args) is dict)
        project = alias(args.get('project'))
        if operation == 'propose':
            fields(args, ('project', 'case'), ('artifacts',))
            case = args['case']
            fields(case, ('type', 'title', 'problem', 'root_cause', 'solution', 'applies_when', 'limitations', 'tags', 'source', 'evidence', 'privacy_reviewed'))
            require(case['type'] in ('pattern', 'incident', 'decision', 'solution', 'anti_pattern') and case['privacy_reviewed'] is True)
            text(case['title'], 160)
            for name in ('problem', 'root_cause', 'solution'):
                text(case[name])
            for name in ('applies_when', 'limitations', 'tags', 'evidence'):
                string_list(case[name])
            source = case['source']
            fields(source, ('repo', 'commit', 'adr'))
            require(alias(source['repo']) == project and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', source['commit']) is not None)
            text(source['adr'], 256)
            require(not source['adr'].startswith('/') and '..' not in source['adr'].split('/') and '://' not in source['adr'])
            privacy(encode(case).decode())
            payload = encode(case).decode()
            require(len(payload.encode('utf-8')) <= 8192)
            supplied = args.get('artifacts', [])
            require(type(supplied) is list and len(supplied) <= 4)
            artifacts = []
            # Validate every artifact before persisting any.
            for item in supplied:
                fields(item, ('type', 'summary', 'text'))
                require(item['type'] in ('adr', 'patch', 'verification'))
                text(item['summary'], 256)
                privacy(item['summary'])
                privacy(text(item['text'], 131072))
                require(len(item['text'].encode('utf-8')) <= 131072)
            for item in supplied:
                artifacts.append(dict(id=self.artifacts.put(item['text']), type=item['type'], summary=item['summary']))
            require(len({a['id'] for a in artifacts}) == len(artifacts))
            artifacts.sort(key=lambda a: a['id'])
            key = hashlib.sha256(encode(dict(case=case, artifacts=artifacts))).hexdigest()
            search = ' '.join([case['problem'], case['root_cause'], case['solution']] + case['applies_when'] + case['tags'] + [a['summary'] for a in artifacts])
            indexed=[]
            for item in artifacts:
                value=self.artifacts.read(item['id']).decode('utf-8')
                chunks=[dict(id=hashlib.sha256((item['id']+':'+str(offset)).encode()).hexdigest(),offset=offset,text=value[offset:offset+4096]) for offset in range(0,len(value),4096)]
                indexed.append(dict(item,chunks=chunks))
            rows = self.db.query('/* propose */ MERGE (c:Case {id:$id}) ON CREATE SET c.payload=$payload,c.repo=$project,c.title=$title,c.search_text=$search,c.status="candidate",c.created_at=datetime() WITH c MERGE (p:Project {id:$project}) MERGE (c)-[:ORIGINATED_IN]->(p) FOREACH (item IN $artifacts | MERGE (a:Artifact {id:item.id}) MERGE (c)-[attachment:HAS_ARTIFACT]->(a) ON CREATE SET attachment.type=item.type,attachment.summary=item.summary FOREACH (part IN item.chunks | MERGE (chunk:ArtifactChunk {id:part.id}) ON CREATE SET chunk.search_text=part.text,chunk.artifact_hash=item.id,chunk.offset=part.offset MERGE (a)-[:HAS_CHUNK]->(chunk))) RETURN c.id AS id,c.status AS status', dict(id=key, payload=payload, project=project, title=case['title'], search=search, artifacts=indexed))
            require(len(rows) == 1)
            return rows[0]
        if operation == 'search':
            fields(args, ('project', 'query'), ('limit',))
            text(args['query'], 256)
            limit = args.get('limit', 3)
            require(type(limit) is int and 1 <= limit <= 5)
            words = re.findall(r'\w+', args['query'], re.UNICODE)
            require(0 < len(words) <= 24)
            query = ' OR '.join('"' + word + '"' for word in words)
            rows = self.db.query('/* search */ CALL db.index.fulltext.queryNodes("memory_search",$query,{limit:200}) YIELD node,score OPTIONAL MATCH (owner:Case)-[:HAS_ARTIFACT]->(:Artifact)-[:HAS_CHUNK]->(node) WITH CASE WHEN node:Case THEN node ELSE owner END AS c,node,score WHERE c IS NOT NULL AND (c.status="global" OR (c.repo=$project AND c.status="candidate")) WITH c,node,score ORDER BY score DESC WITH c,max(score) AS score,head(collect(node{.artifact_hash,.offset})) AS matched_artifact RETURN c.id AS id,c.title AS title,c.repo AS project,c.status AS status,EXISTS { MATCH (c)-[:HAS_FEEDBACK]->(f:Feedback) WHERE f.outcome="refuted" } AS has_refutations,matched_artifact,score ORDER BY score DESC,c.id LIMIT $limit', dict(project=project, query=query, limit=limit))
            return dict(items=rows, full_content=False, retrieval='native_fulltext_cards_and_artifacts', candidate_limit=200, semantic=False)
        if operation in ('get', 'neighbors', 'artifact', 'promote', 'feedback', 'link'):
            key = digest(args.get('id'))
            feedback_offset,review_offset=args.get('feedback_offset',0),args.get('review_offset',0)
            require(type(feedback_offset) is int and 0<=feedback_offset<=1000000 and type(review_offset) is int and 0<=review_offset<=1000000)
            current = self.get(key, project,feedback_offset,review_offset)
        if operation == 'get':
            fields(args, ('project', 'id'),('feedback_offset','review_offset'))
            return current
        if operation == 'neighbors':
            fields(args, ('project', 'id'))
            rows = self.db.query('/* neighbors */ MATCH (c:Case {id:$id})-[r:RELATES_TO|SUPERSEDES|CONTRADICTS|VALIDATED_BY]-(n:Case) WHERE n.status="global" OR n.repo=$project RETURN n.id AS id,n.title AS title,n.status AS status,type(r) AS relation,startNode(r).id AS from_id,endNode(r).id AS to_id ORDER BY id,relation LIMIT 21', dict(id=key, project=project))
            return dict(items=rows[:20], has_more=len(rows) > 20)
        if operation == 'artifact':
            fields(args, ('project', 'id', 'hash'), ('offset',))
            artifact = digest(args['hash'])
            require(artifact in {a['id'] for a in current['artifacts']})
            offset = args.get('offset', 0)
            require(type(offset) is int and offset >= 0)
            # Character paging preserves arbitrary long lines; clients concatenate pages exactly.
            value = self.artifacts.read(artifact).decode('utf-8')
            require(offset <= len(value))
            end = min(offset + 4096, len(value))
            return dict(hash=artifact, text=value[offset:end], offset=offset, next_offset=end if end < len(value) else None, complete=end == len(value))
        if operation == 'promote':
            fields(args, ('project', 'id', 'status', 'reason', 'evidence_reviewed'))
            require(args['status'] in ('global', 'rejected', 'retracted') and args['evidence_reviewed'] is True)
            privacy(text(args['reason'], 512))
            # One atomic update; only reviewer can enter this branch.
            review_id = hashlib.sha256(encode(dict(id=key,status=args['status'],reason=args['reason']))).hexdigest()
            rows = self.db.query('/* promote */ MATCH (c:Case {id:$id}) SET c.status=$status,c.reason=$reason,c.reviewed_at=datetime() MERGE (r:Review {id:$review_id}) ON CREATE SET r.status=$status,r.reason=$reason,r.created_at=datetime() MERGE (c)-[:HAS_REVIEW]->(r) RETURN c.id AS id,c.status AS status', dict(id=key, status=args['status'], reason=args['reason'], review_id=review_id))
            require(len(rows) == 1)
            return rows[0]
        if operation == 'feedback':
            fields(args, ('project', 'id', 'commit', 'outcome', 'note', 'evidence'))
            require(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', args['commit']) is not None and args['outcome'] in ('helped', 'not_applicable', 'refuted'))
            privacy(text(args['note'], 512))
            string_list(args['evidence'])
            privacy(encode(args['evidence']).decode())
            require(len(encode(args)) <= 2048)
            fid = hashlib.sha256(encode(args)).hexdigest()
            rows = self.db.query('/* feedback */ MATCH (c:Case {id:$id}) MERGE (f:Feedback {id:$fid}) ON CREATE SET f.repo=$project,f.commit=$commit,f.outcome=$outcome,f.note=$note,f.evidence=$evidence,f.created_at=datetime() MERGE (c)-[:HAS_FEEDBACK]->(f) RETURN f.id AS id,f.outcome AS outcome', dict(args, fid=fid))
            require(len(rows) == 1)
            return rows[0]
        if operation == 'link':
            fields(args, ('project', 'id', 'target', 'relation'))
            target = digest(args['target'])
            self.get(target, project)
            relation = args['relation']
            require(relation in RELATIONS and key != target)
            rows = self.db.query('/* link */ MATCH (a:Case {id:$id}),(b:Case {id:$target}) MERGE (a)-[r:' + relation + ']->(b) RETURN a.id AS id,b.id AS target,type(r) AS relation', dict(id=key, target=target))
            require(len(rows) == 1)
            return rows[0]
        raise Rejected('Unknown operation.')


def handler(knowledge, agent_token, reviewer_token):
    require(len(agent_token) >= 32 and len(reviewer_token) >= 32 and agent_token != reviewer_token)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.0'

        def setup(self):
            super().setup()
            self.connection.settimeout(12)

        def log_message(self, *args):
            pass

        def reply(self, status, value):
            raw = encode(value)
            require(len(raw) <= MAX_BODY)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            role = None
            received = self.headers.get('Authorization', '').encode('utf-8')
            if hmac.compare_digest(received, ('Bearer ' + reviewer_token).encode('utf-8')):
                role = 'reviewer'
            elif hmac.compare_digest(received, ('Bearer ' + agent_token).encode('utf-8')):
                role = 'agent'
            if role is None:
                self.reply(401, dict(ok=False, error='unauthorized'))
                return
            try:
                require(len(self.headers.get_all('Content-Length', [])) == 1 and not self.headers.get('Transfer-Encoding'))
                require(self.headers.get('Content-Type') == 'application/json')
                length = int(self.headers['Content-Length'])
                require(0 < length <= MAX_BODY)
                raw = self.rfile.read(length)
                require(len(raw) == length and self.path.startswith('/v1/'))
                result = knowledge.execute(self.path[4:], parse(raw), role)
                self.reply(200, dict(ok=True, data=result))
            except (ValueError, TypeError, KeyError, OSError, RecursionError):
                self.reply(400, dict(ok=False, error='rejected_or_reconciliation_required'))
    return Handler



def create_server(knowledge, agent_token, reviewer_token, *, port=18791, container_network=False):
    require(type(container_network) is bool and type(port) is int and 0 <= port <= 65535)
    host = '0.0.0.0' if container_network else '127.0.0.1'
    return HTTPServer((host, port), handler(knowledge, agent_token, reviewer_token))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('init', 'serve'))
    parser.add_argument('--port', type=int, default=18791)
    parser.add_argument('--container-network', action='store_true', help='Explicit private-container bridge mode; never publish publicly')
    args = parser.parse_args()
    os.umask(0o077)
    try:
        db = Neo4j(os.environ.get('NEO4J_URL', 'http://127.0.0.1:17474'), os.environ['NEO4J_PASSWORD'], container_network=args.container_network)
        if args.operation == 'init':
            db.initialize()
        else:
            knowledge = Knowledge(db, Artifacts(os.environ['MEMORY_ARTIFACT_DIR']))
            create_server(knowledge, os.environ['MEMORY_AGENT_TOKEN'], os.environ['MEMORY_REVIEWER_TOKEN'],
                          port=args.port, container_network=args.container_network).serve_forever()
        return 0
    except (ValueError, KeyError, OSError):
        print('Memory service rejected configuration or database outcome; inspect scoped status without replay.')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
