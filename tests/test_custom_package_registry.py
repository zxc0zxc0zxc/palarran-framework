"""Synthetic actors, real SQLite/HTTP, no live registry or cloud credentials."""
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from packages.core.packaging.contract import (PackageError, build_archive, canonical,
                                              refresh_manifest, scaffold)
from packages.core.packaging.service import create_server, load_credentials
from packages.core.packaging.storage import FilesystemBlobStore
from packages.core.packaging.store import RegistryStore, MAX_MESSAGE

TOKENS = {'alice': 'a'*40, 'bob': 'b'*40, 'carol': 'c'*40}
CREDENTIALS = {TOKENS[a]: {'actor':a, 'read_publishers':['alice'] if a=='bob' else []}
               for a in TOKENS}


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.blobs = FilesystemBlobStore(self.root/'blobs')
        self.store = RegistryStore(self.root/'registry.sqlite3', self.blobs, CREDENTIALS)
        self.counter = 0
        self.server = None

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=3)

    def bundle(self, *, publisher='alice', name='reports', visibility='private', version='0.1.0', title=None):
        self.counter += 1
        source = self.root/('source-'+str(self.counter))
        scaffold(source,publisher=publisher,name=name,visibility=visibility,
                 license_name='MIT' if visibility=='public' else 'UNLICENSED')
        manifest = json.loads((source/'palarran-package.json').read_text())
        manifest['version'] = version
        if title:
            manifest['title'] = title
        (source/'palarran-package.json').write_bytes(canonical(manifest))
        return build_archive(source)

    def publish(self, raw=None, actor='alice', request_id=None):
        if raw is None:
            raw = self.bundle()
        self.counter += 1
        payload = dict(request_id=request_id or 'publish-'+str(self.counter),
                       archive_base64=base64.b64encode(raw).decode())
        return self.store.dispatch(TOKENS[actor], 'publish', payload)

    def get(self, operation='get', actor=None, **fields):
        payload = dict(publisher='alice',name='reports',version='0.1.0',**fields)
        return self.store.dispatch(TOKENS.get(actor),operation,payload)

    def error(self, value, code):
        self.assertEqual({'ok':False,'error':{'code':code}}, value)

    def test_private_release_cannot_be_enumerated_or_downloaded(self):
        raw = self.bundle()
        result = self.publish(raw)
        self.assertTrue(result['ok'])
        for actor in (None,'carol'):
            self.assertEqual([],self.store.dispatch(TOKENS.get(actor),'search',{})['result']['packages'])
            self.error(self.get(actor=actor),'not_found')
            self.error(self.get('download',actor=actor),'not_found')
            self.error(self.store.dispatch(TOKENS.get(actor),'get',
                       dict(publisher='alice',name='absent',version='0.1.0')),'not_found')
        for actor in ('alice','bob'):
            self.assertEqual('alice',self.get(actor=actor)['result']['package']['publisher'])
            response = self.get('download',actor=actor)['result']
            self.assertEqual(raw,base64.b64decode(response['archive_base64']))
            self.assertEqual(hashlib.sha256(raw).hexdigest(),response['sha256'])
        self.error(self.store.dispatch('bad-token','search',{}),'unauthorized')

    def test_public_unlisted_exact_pin_and_deleted_tombstone(self):
        raw = self.bundle(visibility='public')
        self.assertTrue(self.publish(raw)['ok'])
        self.assertTrue(self.get()['ok'])
        self.assertEqual(1,len(self.store.dispatch(None,'search',{})['result']['packages']))
        result = self.get('delist','alice',request_id='unlist')
        self.assertTrue(result['ok'])
        self.assertEqual([],self.store.dispatch(None,'search',{})['result']['packages'])
        self.assertTrue(self.get('download')['ok'])
        self.assertTrue(self.get('delete','alice',request_id='remove')['ok'])
        self.error(self.get(),'not_found')
        self.error(self.get('download'),'not_found')
        self.error(self.publish(raw,request_id='new-publish'),'already_exists')
        own = self.store.dispatch(TOKENS['alice'],'search',dict(mine=True))['result']['packages']
        self.assertTrue(own[0]['deleted'])
        self.assertFalse(own[0]['listed'])
        self.assertEqual([],self.store.dispatch(TOKENS['bob'],'search',dict(mine=True))['result']['packages'])
        self.error(self.store.dispatch(None,'search',dict(mine=True)),'unauthorized')

    def test_publisher_forgery_and_reader_cannot_mutate(self):
        raw = self.bundle()
        self.error(self.publish(raw,'bob'),'forbidden')
        self.assertTrue(self.publish(raw)['ok'])
        self.error(self.get('delist','bob',request_id='reader-denied'),'not_found')
        self.assertTrue(self.get(actor='alice')['result']['package']['listed'])

    def test_visibility_frozen_and_versions_never_replaced(self):
        self.assertTrue(self.publish(self.bundle())['ok'])
        self.error(self.publish(self.bundle(title='Changed metadata')),'already_exists')
        self.error(self.publish(self.bundle(visibility='public',version='0.2.0')),'visibility_conflict')
        self.assertTrue(self.publish(self.bundle(version='0.2.0'))['ok'])

    def test_receipt_restart_actor_scope_and_conflicting_payload(self):
        raw = self.bundle()
        original = self.publish(raw,request_id='stable')
        self.store = RegistryStore(self.store.path,self.blobs,CREDENTIALS)
        self.assertEqual(original,self.publish(raw,request_id='stable'))
        found = self.store.dispatch(TOKENS['alice'],'operation.get',dict(request_id='stable'))
        self.assertEqual(original,found['result']['receipt'])
        self.assertEqual('publish',found['result']['operation'])
        self.assertEqual({'found':False},self.store.dispatch(TOKENS['bob'],'operation.get',
                                                           dict(request_id='stable'))['result'])
        self.error(self.get('delist','alice',request_id='stable'),'idempotency_conflict')
        self.assertTrue(self.get(actor='alice')['result']['package']['listed'])

    def test_two_concurrent_identical_publish_requests_commit_once(self):
        raw = self.bundle();barrier=threading.Barrier(2)
        def publish():
            barrier.wait(timeout=2)
            return self.publish(raw,request_id='same-key')
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:publish(),range(2)))
        self.assertEqual(results[0],results[1]);self.assertTrue(results[0]['ok'])
        with sqlite3.connect(self.store.path) as db:
            self.assertEqual(1,db.execute('SELECT count(*) FROM releases').fetchone()[0])
            self.assertEqual(1,db.execute('SELECT count(*) FROM receipts').fetchone()[0])

    def test_two_publishers_cannot_replace_same_owned_version(self):
        raw = self.bundle();barrier=threading.Barrier(2)
        def publish(index):
            barrier.wait(timeout=2)
            return self.publish(raw,request_id='version-race-'+str(index))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(publish,range(2)))
        self.assertEqual(1,sum(r['ok'] for r in results))
        denied=next(r for r in results if not r['ok'])
        self.error(denied,'already_exists')

    def test_metadata_rollback_leaves_only_unreachable_blob(self):
        raw=self.bundle()
        with patch.object(self.store,'_record',side_effect=RuntimeError('do-not-relay-private')):
            self.error(self.publish(raw,request_id='failed-tx'),'unavailable')
        self.assertEqual([],self.store.dispatch(TOKENS['alice'],'search',dict(mine=True))['result']['packages'])
        self.assertEqual({'found':False},self.store.dispatch(TOKENS['alice'],'operation.get',
                                                           dict(request_id='failed-tx'))['result'])
        self.assertEqual(raw,self.blobs.get(hashlib.sha256(raw).hexdigest()))
        self.assertTrue(self.publish(raw,request_id='failed-tx')['ok'])

    def test_corrupt_blob_download_fails_closed(self):
        raw=self.bundle();self.publish(raw)
        key=hashlib.sha256(raw).hexdigest()
        (self.blobs.path/key).write_bytes(b'changed')
        self.error(self.get('download','alice'),'blob_digest_mismatch')

    def test_literal_query_cursor_limits_and_quota(self):
        for i in range(3):
            self.assertTrue(self.publish(self.bundle(name='package-'+str(i),visibility='public'))['ok'])
        first=self.store.dispatch(None,'search',dict(limit=2))['result']
        self.assertEqual(2,len(first['packages']));self.assertTrue(first['has_more'])
        last=self.store.dispatch(None,'search',dict(limit=2,after=first['next_cursor']))['result']
        self.assertEqual(1,len(last['packages']));self.assertFalse(last['has_more'])
        self.assertEqual([],self.store.dispatch(None,'search',dict(query='%'))['result']['packages'])
        for value in (True,0,21):self.error(self.store.dispatch(None,'search',dict(limit=value)),'invalid_limit')
        with patch('packages.core.packaging.store.MAX_RELEASES',3):
            self.error(self.publish(self.bundle(name='fourth')),'capacity_exhausted')
        with patch('packages.core.packaging.store.MAX_RECEIPTS',0):
            self.error(self.get('delist','alice',request_id='quota'),'capacity_exhausted')

    def test_foreign_database_rejected_without_journal_mode_mutation(self):
        path=self.root/'foreign.sqlite3'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE foreign_state(id INTEGER)')
            db.execute('PRAGMA journal_mode=WAL')
        path.chmod(0o600)
        before=path.read_bytes()
        with self.assertRaisesRegex(PackageError,'unsupported_state'):
            RegistryStore(path,self.blobs,CREDENTIALS)
        self.assertEqual(before,path.read_bytes())
        with sqlite3.connect(path) as db:
            self.assertEqual('wal',db.execute('PRAGMA journal_mode').fetchone()[0])

    def start_http(self):
        self.server=create_server(self.store,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def http(self,operation,payload,actor=None,raw=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        body=canonical(payload) if raw is None else raw
        actual={'Content-Type':'application/json',**(headers or {})}
        if actor:actual['Authorization']='Bearer '+TOKENS[actor]
        conn.request('POST','/v1/'+operation,body=body,headers=actual)
        response=conn.getresponse();data=response.read();status=response.status
        conn.close();return status,json.loads(data)

    def test_actual_http_publish_read_private_denial_and_receipt(self):
        self.start_http();raw=self.bundle()
        payload=dict(request_id='http-publish',archive_base64=base64.b64encode(raw).decode())
        status,response=self.http('publish',payload,'alice')
        self.assertEqual(200,status);self.assertTrue(response['ok'])
        lookup=self.http('operation.get',dict(request_id='http-publish'),'alice')[1]
        self.assertEqual(response,lookup['result']['receipt'])
        fields=dict(publisher='alice',name='reports',version='0.1.0')
        self.assertEqual(404,self.http('get',fields,'carol')[0])
        self.assertEqual(200,self.http('download',fields,'bob')[0])

    def test_auth_and_strict_http_never_log_tokens_or_body(self):
        self.start_http()
        with redirect_stderr(io.StringIO()) as logs:
            status,result=self.http('publish',{},raw=b'not-json-secret-marker')
            self.assertEqual(401,status);self.error(result,'unauthorized')
            self.assertEqual(400,self.http('search',{},raw=b'{"query":"a","query":"b"}')[0])
            self.assertEqual(400,self.http('search',{},headers={'Transfer-Encoding':'chunked'})[0])
            self.assertEqual(400,self.http('search',{},headers={'Content-Length':str(MAX_MESSAGE+1)})[0])
        self.assertEqual('',logs.getvalue())
        with self.assertRaisesRegex(PackageError,'private_listener_required'):
            create_server(self.store,host='0.0.0.0')

    def test_credential_file_permissions_and_symlinks(self):
        path=self.root/'credentials.json';path.write_bytes(canonical(CREDENTIALS));path.chmod(0o600)
        self.assertEqual(CREDENTIALS,load_credentials(path))
        path.chmod(0o644)
        with self.assertRaisesRegex(PackageError,'private_credentials_required'):load_credentials(path)
        link=self.root/'credential-link';link.symlink_to(path)
        with self.assertRaisesRegex(PackageError,'symlink_path'):load_credentials(link)
