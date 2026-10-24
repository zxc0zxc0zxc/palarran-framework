"""Offline coordination transport and MCP tests; no production or model calls."""
import io
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import URLError

from packages.core.coordination.client import Client, configuration, encode, parse
from packages.core.coordination.proxy import Proxy


class Response(io.BytesIO):
    pass


class Transport:
    def __init__(self, value=None, failure=None):
        self.value, self.failure, self.requests = value, failure, []

    def open(self, request, timeout):
        self.requests.append(request)
        if self.failure:
            raise self.failure
        return Response(encode(self.value))


class CoordinationClientTest(unittest.TestCase):
    def client(self, transport):
        client = Client('http://127.0.0.1:18792', 'a' * 40)
        client.opener = transport
        return client

    def test_unknown_write_is_not_retried_and_preserves_request_id(self):
        transport = Transport(failure=URLError('server might have committed; secret detail'))
        result = self.client(transport).request('message.post', {'project': 'p', 'room': 'i', 'request_id': 'original'})
        self.assertEqual(result, {'ok': False, 'error': {'code': 'unavailable_or_unknown'}})
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(parse(transport.requests[0].data)['request_id'], 'original')

    def test_loopback_only_and_response_error_does_not_relay_raw_details(self):
        for url in ('http://example.org:80', 'https://127.0.0.1:80', 'http://127.0.0.1:80/x', 'http://u@127.0.0.1:80'):
            with self.assertRaises(ValueError):
                Client(url, 'a' * 40)
        transport = Transport({'ok': False, 'error': {'code': 'forbidden', 'detail': 'private server diagnostic'}})
        self.assertEqual(self.client(transport).request('claims.list', {'project': 'p', 'room': 'i'}),
                         {'ok': False, 'error': {'code': 'forbidden'}})

    def test_complete_project_profile_overrides_global_and_partial_does_not_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            project, home = root/'project', root/'home'
            project.mkdir(); (home/'.palarran').mkdir(parents=True)
            def write(path, text):
                path.write_text(text); path.chmod(0o600)
            write(home/'.palarran/.env', 'COORDINATION_URL=http://127.0.0.1:18792\nCOORDINATION_TOKEN='+'g'*40+'\n')
            write(project/'.env', 'UNRELATED=value\n')
            self.assertEqual(configuration(cwd=project, home=home)['COORDINATION_TOKEN'], 'g'*40)
            write(project/'.env', 'COORDINATION_TOKEN='+'p'*40+'\n')
            with self.assertRaises(ValueError):
                configuration(cwd=project, home=home)
            write(project/'.env', 'COORDINATION_URL=http://127.0.0.1:18793\nCOORDINATION_TOKEN='+'p'*40+'\n')
            self.assertEqual(configuration(cwd=project, home=home)['COORDINATION_TOKEN'], 'p'*40)
            (project/'.env').chmod(0o644)
            with self.assertRaises(ValueError):
                configuration(cwd=project, home=home)

    def test_mcp_lifecycle_does_not_advertise_operator_or_execute_capabilities(self):
        transport = Transport({'ok': True, 'result': {'found': False}})
        proxy = Proxy(self.client(transport))
        def call(method, params=None, rid=1):
            return proxy.dispatch(dict(jsonrpc='2.0', id=rid, method=method, params=params or {}))
        self.assertIn('error', call('tools/list'))
        self.assertEqual(call('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {},
                                           'clientInfo': {'name': 'test', 'version': '1'}})['result']['protocolVersion'], '2025-11-25')
        proxy.dispatch(dict(jsonrpc='2.0', method='notifications/initialized'))
        tools = call('tools/list')['result']['tools']
        self.assertEqual(len(tools), 9)
        self.assertNotIn('reconcile', ' '.join(t['name'] for t in tools))
        result = call('tools/call', {'name': 'coordination.get_operation', 'arguments': {'project': 'p', 'request_id': 'old'}})
        self.assertEqual(result['result']['structuredContent']['data'], {'found': False})
        self.assertEqual(len(transport.requests), 1)
        bad = call('tools/call', {'name': 'coordination.get_operation', 'arguments': {'project': 'p', 'request_id': 'old', 'actor': 'other'}})
        self.assertTrue(bad['result']['isError'])
        self.assertEqual(len(transport.requests), 1)

    def test_oversized_request_and_malformed_response_fail_closed(self):
        transport = Transport({'ok': True, 'result': []})
        client = self.client(transport)
        with self.assertRaises(ValueError):
            client.request('message.post', {'text': 'x' * 17000})
        self.assertFalse(transport.requests)
        self.assertEqual(client.request('operation.get', {'project': 'p', 'request_id': 'old'})['error']['code'], 'unavailable_or_unknown')
        with self.assertRaises(ValueError):
            parse(b'{"a":1,"a":2}')
        with self.assertRaises(ValueError):
            parse(b'{"a":NaN}')

    def test_two_real_mcp_proxies_exchange_messages_and_share_cross_room_claims(self):
        from packages.core.coordination.service import CoordinationStore, create_server
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory).resolve()/'state'
            state.mkdir(mode=0o700)
            tokens = {'a'*40: {'actor': 'developer-a', 'projects': ['p'], 'role': 'agent'},
                      'b'*40: {'actor': 'developer-b', 'projects': ['p'], 'role': 'agent'}}
            server = create_server(CoordinationStore(state/'chat.sqlite', tokens), port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = 'http://127.0.0.1:'+str(server.server_address[1])
                a, b = Proxy(Client(url, 'a'*40)), Proxy(Client(url, 'b'*40))
                def invoke(proxy, tool, **arguments):
                    result = proxy.call('coordination.'+tool, dict(project='p', **arguments), 1)
                    self.assertFalse(result['isError'], result)
                    return result['structuredContent']['data']
                for room in ('incident-a', 'incident-b'):
                    invoke(a, 'ensure_room', room=room, title=room, request_id='ensure-'+room)
                posted = invoke(a, 'post_message', room='incident-a', kind='fact', text='503 observed; source E1',
                                recipient='developer-b', request_id='observation-1')['message']
                read = invoke(b, 'read_messages', room='incident-a')
                self.assertEqual(read['messages'][0]['actor'], 'developer-a')
                self.assertEqual(read['messages'][0]['seq'], posted['seq'])
                ack = invoke(b, 'ack_message', room='incident-a', message_seq=posted['seq'], request_id='received-1')
                self.assertEqual(ack['actor'], 'developer-b')
                invoke(a, 'acquire_claim', room='incident-a', resource='prod/api/deployment', ttl=30, request_id='claim-1')
                conflict = b.call('coordination.acquire_claim', dict(project='p', room='incident-b',
                                  resource='prod/api/deployment', ttl=30, request_id='claim-2'), 1)
                self.assertEqual(conflict['structuredContent']['error']['code'], 'resource_busy')
                found = invoke(a, 'get_operation', request_id='observation-1')
                self.assertEqual(found['receipt']['result']['message'], posted)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
