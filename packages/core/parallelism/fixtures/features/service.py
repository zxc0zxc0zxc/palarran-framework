"""Synthetic trusted referral service; CONFIG is prefixed by the laboratory."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

lock = threading.RLock()
bindings, postings, reversals = {}, {}, set()
consumer_down = False

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.reply(200, {'role': CONFIG['role'], 'healthy': True})

    def reply(self, code, value):
        raw = json.dumps(value).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        global consumer_down
        try:
            count = int(self.headers.get('Content-Length', '0'))
            if not 0 < count <= 8192:
                raise ValueError()
            value = json.loads(self.rfile.read(count))
            tenant = value['tenant']
            if tenant != value.get('actor_tenant'):
                self.reply(403, {'error': 'tenant'}); return
            with lock:
                role = CONFIG['role']
                if role == 'auth':
                    key = tenant + ':' + value['user']
                    if key in bindings and bindings[key] != value['referrer']:
                        self.reply(409, {'error': 'immutable_binding'}); return
                    bindings[key] = value['referrer']
                    self.reply(200, {'referrer': bindings[key]}); return
                if role == 'cards':
                    eligible = value['action'] == 'first_card_activated'
                    self.reply(200, {'eligible': eligible, 'event': {
                        'tenant': tenant, 'actor_tenant': tenant, 'key': value['key'],
                        'user': value['user'], 'amount_minor': 500, 'currency': 'USD',
                        'rule_version': 1, 'version': value.get('version', CONFIG.get('event_version', 2)),
                        'created_at': value.get('created_at', 100), 'eligible': eligible}}); return
                if self.path == '/down':
                    consumer_down = value['down']; self.reply(200, {'down': consumer_down}); return
                if consumer_down:
                    self.reply(503, {'error': 'consumer_down'}); return
                key = tenant + ':' + value['key']
                if self.path == '/balance':
                    self.reply(200, {'balance_minor': sum(p['amount'] for k, p in postings.items()
                        if k.startswith(tenant + ':') and p['user'] == value['user'] and k not in reversals)}); return
                if self.path == '/reverse':
                    if key not in postings:
                        self.reply(404, {'error': 'missing_original'}); return
                    reversals.add(key); self.reply(200, {'reversed': True}); return
                if value.get('version', 1) not in (1, 2):
                    self.reply(400, {'error': 'version'}); return
                if value['currency'] != 'USD' or type(value['amount_minor']) is not int or value['amount_minor'] < 0:
                    self.reply(400, {'error': 'amount'}); return
                if not value.get('enabled', True) or not value['eligible']:
                    self.reply(200, {'credited_minor': 0, 'duplicate': False}); return
                duplicate = key in postings
                if not duplicate:
                    postings[key] = {'user': value['user'], 'amount': value['amount_minor'] * CONFIG['multiplier']}
                if value.get('simulate_response_loss') and not duplicate:
                    self.reply(503, {'error': 'ack_lost_after_posting'}); return
                self.reply(200, {'credited_minor': postings[key]['amount'], 'duplicate': duplicate})
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            self.reply(400, {'error': 'malformed'})

server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
server.daemon_threads = True
with open(sys.argv[1], 'w') as handle:
    json.dump({'port': server.server_port}, handle)
server.serve_forever(poll_interval=0.05)
