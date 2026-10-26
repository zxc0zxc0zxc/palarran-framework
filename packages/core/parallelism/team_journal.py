"""Private, bounded team metadata sidecar; never a second budget ledger."""
import json
from contextlib import contextmanager
import os
from pathlib import Path
import re
import sqlite3
import time

_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')
_FIELDS = {'run_id','task_id','attempt_id','children','observed_active','discovered','capacity',
           'count_scope','observation_complete','usage_scope','telemetry_failed',
           'capacity_exceeded','root_stopped','usage_complete','transport_reason','cost_kind','activity','needs_human'}


class TeamJournal:
    def __init__(self, path, *, read_only=False):
        self.read_only = read_only
        self.path = Path(path).absolute()
        if any(p.is_symlink() for p in (self.path,*self.path.parents)):
            raise ValueError('Telemetry symlinks are unsupported')
        if not read_only:
            self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        elif not self.path.is_file():
            raise ValueError("Existing private telemetry required")
        if self.path.exists() and (not self.path.is_file() or self.path.stat().st_mode & 0o077 or self.path.stat().st_uid != os.getuid()):
            raise ValueError('Telemetry database must be owner-only')
        if read_only:return
        fd=os.open(str(self.path),os.O_CREAT|os.O_RDWR,0o600);os.close(fd)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS observations(run TEXT,task TEXT,attempt INTEGER,body TEXT,updated REAL,PRIMARY KEY(run,task))')
            db.execute('CREATE TABLE IF NOT EXISTS supervisors(run TEXT PRIMARY KEY,state TEXT,pid INTEGER,updated REAL)')
            db.execute('CREATE TABLE IF NOT EXISTS updates(sequence INTEGER PRIMARY KEY AUTOINCREMENT,run TEXT,task TEXT,updated REAL)')

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True,timeout=5) if self.read_only else sqlite3.connect(str(self.path),timeout=5)
        db.execute('PRAGMA trusted_schema=OFF')
        if not self.read_only:db.execute('PRAGMA journal_mode=DELETE')
        try:
            with db:
                yield db
        finally:
            db.close()

    def supervisor(self, run_id, state, pid):
        if not _ID.fullmatch(run_id) or state not in ('running','stopped','failed') or type(pid) is not int or pid<=0:
            raise ValueError('Invalid supervisor metadata')
        with self._db() as db:
            old=db.execute('SELECT state,pid FROM supervisors WHERE run=?',(run_id,)).fetchone()
            db.execute('INSERT OR REPLACE INTO supervisors VALUES(?,?,?,?)',(run_id,state,pid,time.time()))
            if old!=(state,pid):
                db.execute('INSERT INTO updates(run,task,updated) VALUES(?,?,?)',(run_id,'supervisor',time.time()))

    def publish(self, value):
        if type(value) is not dict or set(value)-_FIELDS:
            raise ValueError('Only allowlisted team metadata may be stored')
        for field in ('run_id','task_id'):
            if not isinstance(value.get(field),str) or not _ID.fullmatch(value[field]):
                raise ValueError('Invalid team identity')
        if type(value.get('attempt_id')) is not int or value['attempt_id']<1:
            raise ValueError('Invalid team attempt')
        children=value.get('children')
        if type(children) is not list or len(children)>256:
            raise ValueError('Bounded children required')
        for child in children:
            if (type(child) is not dict or set(child)!={'agent_id','state'}
                    or not re.fullmatch('[0-9a-f]{24}',str(child['agent_id']))
                    or child['state'] not in ('requested','running','completed','errored','shutdown','stopped','failed')):
                raise ValueError('Invalid child metadata')
        if value.get('activity','starting') not in ('starting','working','command','editing','research','delegating','reading','needs_human'):
            raise ValueError('Invalid activity category')
        if value.get('cost_kind','provider_report') not in ('provider_report','price_card_estimate'):
            raise ValueError('Invalid cost classification')
        raw=json.dumps(value,sort_keys=True,allow_nan=False)
        if len(raw.encode())>65536:raise ValueError('Team metadata exceeds bound')
        now=time.time()
        with self._db() as db:
            old=db.execute('SELECT attempt,body FROM observations WHERE run=? AND task=?',(value['run_id'],value['task_id'])).fetchone()
            if old and old[0]>value['attempt_id']:raise ValueError('Stale observation attempt')
            if old and old[1]==raw:return
            if db.execute('SELECT COUNT(*) FROM observations').fetchone()[0]>=1000 and old is None:
                raise ValueError('Team journal capacity reached')
            db.execute('INSERT OR REPLACE INTO observations VALUES(?,?,?,?,?)',(value['run_id'],value['task_id'],value['attempt_id'],raw,now))
            db.execute('INSERT INTO updates(run,task,updated) VALUES(?,?,?)',(value['run_id'],value['task_id'],now))
            # Cursor consumers explicitly see truncated=True when they fall behind.
            db.execute('DELETE FROM updates WHERE sequence <= (SELECT COALESCE(MAX(sequence),0)-10000 FROM updates)')

    def read(self, run_id, *, after=0):
        if not _ID.fullmatch(run_id) or type(after) is not int or after<0:
            raise ValueError('Invalid telemetry cursor')
        with self._db() as db:
            rows=db.execute('SELECT body,updated FROM observations WHERE run=? ORDER BY task',(run_id,)).fetchall()
            supervisor=db.execute('SELECT state,pid,updated FROM supervisors WHERE run=?',(run_id,)).fetchone()
            bounds=db.execute('SELECT MIN(sequence),MAX(sequence) FROM updates').fetchone()
            changes=db.execute('SELECT sequence,task,updated FROM updates WHERE run=? AND sequence>? ORDER BY sequence LIMIT 100',(run_id,after)).fetchall()
        return dict(supervisor=dict(state=supervisor[0],pid=supervisor[1],observed_at=supervisor[2]) if supervisor else None,
                    sessions=[dict(json.loads(row[0]),observed_at=row[1]) for row in rows],
                    cursor=changes[-1][0] if changes else max(after,bounds[1] or 0),
                    truncated=bool(after and bounds[0] and after<bounds[0]-1),
                    changes=[dict(sequence=r[0],task_id=r[1],observed_at=r[2]) for r in changes])
