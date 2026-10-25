"""Bounded private registry HTTP transport; no raw request/access logging."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import socket
import sqlite3
import stat
import threading

from .contract import PackageError, canonical, parse_json, require
from .storage import FilesystemBlobStore, private_path
from .store import RegistryStore, MAX_MESSAGE, OPERATIONS, MUTATIONS


def load_credentials(path):
    path = private_path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        meta = os.fstat(stream.fileno())
        require(stat.S_ISREG(meta.st_mode) and meta.st_uid == os.getuid()
                and not meta.st_mode & 0o077 and meta.st_size <= 128*1024,
                'private_credentials_required')
        return parse_json(stream.read(128*1024+1))


class RegistryHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = True
    def __init__(self, address, handler):
        self._slots = threading.BoundedSemaphore(8)
        super().__init__(address, handler)

    def process_request(self, request, client_address):
        if not self._slots.acquire(blocking=False):
            try:
                request.settimeout(2)
                raw = canonical({'ok':False,'error':{'code':'unavailable'}})
                header = ('HTTP/1.1 503 Service Unavailable\r\nContent-Type: application/json\r\n'
                          'Content-Length: '+str(len(raw))+'\r\nConnection: close\r\n\r\n')
                request.sendall(header.encode('ascii') + raw)
            except OSError:
                pass
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()

    def handle_error(self, request, client_address):
        # No exception text, paths, headers or body are written to service logs.
        pass


def create_server(store, host='127.0.0.1', port=0, container_network=False):
    require(type(container_network) is bool and (host == '127.0.0.1' or
            container_network and host == '0.0.0.0'), 'private_listener_required')
    require(type(port) is int and 0 <= port <= 65535, 'invalid_port')
    class Handler(BaseHTTPRequestHandler):
        server_version = 'PalarranRegistry'
        sys_version = ''
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            pass

        def reply(self, status, value):
            raw = canonical(value)
            if len(raw) > MAX_MESSAGE:
                status, raw = 503, canonical({'ok':False,'error':{'code':'response_too_large'}})
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True
            if self.command != 'HEAD':
                self.wfile.write(raw)

        def error(self, code, status=400):
            self.reply(status, {'ok':False, 'error':{'code':code}})

        def send_error(self, code, message=None, explain=None):
            self.error('invalid_request', code)

        def do_POST(self):
            try:
                require(self.path.startswith('/v1/') and self.path[4:] in OPERATIONS,
                        'unknown_operation')
                require(not self.headers.get('Transfer-Encoding') and
                        len(self.headers.get_all('Content-Length', [])) == 1, 'invalid_request')
                length = int(self.headers.get('Content-Length', '-1'))
                require(0 < length <= MAX_MESSAGE, 'request_too_large')
                require(self.headers.get('Content-Type', '').lower() == 'application/json', 'invalid_request')
                auth = self.headers.get_all('Authorization', [])
                require(len(auth) <= 1, 'unauthorized')
                token = None
                if auth:
                    require(auth[0].startswith('Bearer '), 'unauthorized')
                    token = auth[0][7:]
                    require(token in store.credentials, 'unauthorized')
                require(token is not None or self.path[4:] not in MUTATIONS | {'operation.get'},
                        'unauthorized')
                # Authenticate mutation callers before reading/parsing the body.
                payload = parse_json(self.rfile.read(length), MAX_MESSAGE)
                result = store.dispatch(token, self.path[4:], payload)
                code = result.get('error', {}).get('code')
                status = 200 if result['ok'] else {
                    'unauthorized':401, 'forbidden':403, 'not_found':404,
                    'already_exists':409, 'idempotency_conflict':409,
                    'visibility_conflict':409, 'capacity_exhausted':429,
                    'unavailable':503, 'storage_unavailable':503,
                    'blob_missing':503, 'blob_digest_mismatch':503,
                }.get(code, 400)
                self.reply(status, result)
            except PackageError as exc:
                self.error(exc.code, 401 if exc.code == 'unauthorized' else 400)
            except (ValueError, TypeError, UnicodeError, OSError, socket.timeout):
                self.error('invalid_request')

        def do_GET(self):
            self.error('method_not_allowed', 405)
        do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = do_TRACE = do_CONNECT = do_GET
    return RegistryHTTPServer((host, port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--blobs', required=True)
    parser.add_argument('--credentials', required=True)
    parser.add_argument('--port', type=int, default=18793)
    parser.add_argument('--container-network', action='store_true')
    args = parser.parse_args(argv)
    server = None
    try:
        credentials = load_credentials(args.credentials)
        store = RegistryStore(args.db, FilesystemBlobStore(args.blobs), credentials)
        host = '0.0.0.0' if args.container_network else '127.0.0.1'
        server = create_server(store, host=host, port=args.port,
                               container_network=args.container_network)
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except PackageError as exc:
        print('Registry startup rejected: ' + exc.code)
        return 2
    except (OSError, ValueError, sqlite3.Error):
        print('Registry startup rejected: inaccessible private configuration or state')
        return 2
    finally:
        if server is not None:
            server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
