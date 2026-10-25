"""Real local HTTP/profile checks; no remote registry or paid services."""
import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from packages.core.packaging.client import Client, configuration, origin
from packages.core.packaging.contract import PackageError


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def profile(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o600)

    def test_project_profile_never_borrows_global_token(self):
        project, home = self.root/'project', self.root/'home'
        project.mkdir()
        self.profile(home/'.palarran/.env', 'PACKAGING_URL=https://global.example\nPACKAGING_TOKEN='+'g'*40+'\n')
        self.profile(project/'.env', 'PACKAGING_URL=https://project.example\n')
        self.assertEqual({'PACKAGING_URL':'https://project.example','PACKAGING_TOKEN':None},
                         configuration(project, home))
        self.profile(project/'.env', 'OTHER_VALUE=local\n')
        self.assertEqual('g'*40, configuration(project, home)['PACKAGING_TOKEN'])
        self.profile(project/'.env', 'PACKAGING_TOKEN='+'l'*40+'\n')
        with self.assertRaises(PackageError):
            configuration(project, home)

    def test_profile_private_regular_file_and_literal_values(self):
        project = self.root/'project';project.mkdir()
        profile = project/'.env'
        self.profile(profile, 'PACKAGING_URL=https://registry.example\n')
        profile.chmod(0o644)
        with self.assertRaises(PackageError):configuration(project, self.root/'empty')
        profile.chmod(0o600)
        self.profile(profile, 'PACKAGING_URL=$(touch no)\n')
        with self.assertRaises(PackageError):configuration(project, self.root/'empty')
        profile.unlink();profile.symlink_to(self.root/'missing')
        with self.assertRaises(PackageError):configuration(project, self.root/'empty')

    def test_origin_rejects_credential_query_redirect_style_and_nonloopback_http(self):
        for url in ('http://example.com:80','http://localhost:1234','https://user:pass@registry.example',
                    'https://registry.example/?token=value','https://registry.example/path',
                    'https://127.0.0.1','http://127.0.0.1:3/#fragment'):
            with self.subTest(url=url), self.assertRaises(PackageError):origin(url)
        self.assertEqual('https://registry.example',origin('https://registry.example/'))
        self.assertEqual('http://127.0.0.1:1234',origin('http://127.0.0.1:1234'))

    def server(self, mode):
        events = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                events.append((self.path,self.headers.get('Authorization')))
                length=int(self.headers.get('Content-Length','0'));self.rfile.read(length)
                if mode == 'disconnect':
                    self.close_connection=True;self.connection.close();return
                if mode == 'redirect':
                    self.send_response(307);self.send_header('Location','https://forbidden.example/');self.end_headers();return
                if mode == 'invalid':raw=b'{"ok":false,"error":{"code":"secret value"}}'
                elif mode == 'duplicate':raw=b'{"ok":true,"ok":false,"result":{}}'
                elif mode == 'large':raw=b'x'*1025
                else:raw=b'{"ok":true,"result":{"packages":[]}}'
                self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join,3);self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        return 'http://127.0.0.1:'+str(server.server_port),events

    def test_authenticated_http_and_anonymous_requests(self):
        url,events=self.server('ok')
        self.assertTrue(Client(url,'a'*40).request('search',{})['ok'])
        self.assertTrue(Client(url).request('search',{})['ok'])
        self.assertEqual([('/v1/search','Bearer '+'a'*40),('/v1/search',None)],events)

    def test_unknown_reply_and_redirect_are_not_retried(self):
        for mode in ('disconnect','redirect','invalid','duplicate'):
            with self.subTest(mode=mode):
                url,events=self.server(mode)
                result=Client(url,'a'*40).request('publish',{'request_id':'one'})
                self.assertEqual({'ok':False,'error':{'code':'unavailable_or_unknown'}},result)
                self.assertEqual(1,len(events))

    def test_response_bound_is_checked(self):
        url,events=self.server('large')
        with patch('packages.core.packaging.client.MAX_WIRE',1024):
            self.assertEqual('unavailable_or_unknown',Client(url).request('search',{})['error']['code'])
        self.assertEqual(1,len(events))



if __name__=='__main__':unittest.main()
