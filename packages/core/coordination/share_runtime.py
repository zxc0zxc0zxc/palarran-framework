"""Explicit harness bindings for share advice and separately accounted receiver runs."""
import hashlib
import json
import time

from .share import ShareError, require, integer, ident, digest


def propose(dispatcher, run_id, *, plan_hash, quota=None, independent_task=False,
            resources_limited=False, now=None):
    """Local advice only. No notification/model call and no invented quota value."""
    now=int(time.time()) if now is None else integer(now)
    ident(run_id);digest(plan_hash)
    require(type(independent_task) is bool and type(resources_limited) is bool)
    reason='independent_task' if independent_task else ('local_resources' if resources_limited else None)
    if quota is not None:
        require(type(quota) is dict and set(quota)=={'remaining_percent','observed_at','resets_at','window_seconds','expected_seconds'})
        remaining=quota['remaining_percent']
        require(remaining is None or (type(remaining) in (int,float) and 0<=remaining<=100))
        for key in ('observed_at','resets_at','window_seconds','expected_seconds'):
            integer(quota[key])
        fresh=0<=now-quota['observed_at']<=300
        useful=quota['resets_at']>now+min(quota['expected_seconds'],600) and quota['window_seconds']>0
        if remaining is not None and remaining<=15 and fresh and useful:
            reason='low_quota'
    if reason is None:
        return {'suggested':False,'published':False}
    with dispatcher.ledger.transaction() as db:
        dispatcher.ledger.read_run(db,run_id)
        db.execute('CREATE TABLE IF NOT EXISTS share_advice(run TEXT PRIMARY KEY,plan TEXT NOT NULL,at INTEGER NOT NULL)')
        prior=db.execute('SELECT * FROM share_advice WHERE run=?',(run_id,)).fetchone()
        if prior and (now-prior['at']<900 or prior['plan']==plan_hash):
            return {'suggested':False,'published':False,'reason':'rate_limited'}
        db.execute('INSERT INTO share_advice VALUES(?,?,?) ON CONFLICT(run) DO UPDATE SET plan=excluded.plan,at=excluded.at',
                   (run_id,plan_hash,now))
    return dict(suggested=True,published=False,reason=reason,plan_hash=plan_hash,expires_at=now+600,
                confirmation_required=True,quota_public=False)


def execute_received(dispatcher, *, get_share, send_event, share_id, actor, manifest,
                     profile, adapter, verifier, temporal_submit=None):
    """Durable one-shot local launch intent. Unknown callbacks never auto replay.

    Callbacks are trusted authenticated gateway bindings. Sender must first fence
    the source dispatcher via pause_for_share and attach its evidence to transfer.
    The receiver's already approved budget remains local; no account switching.
    """
    from packages.core.parallelism.dispatcher import validate
    from packages.core.parallelism.entry import start, execute
    state=get_share(share_id)
    require(state['offer']['share_id']==share_id and state['receiver']==actor and state['owner']==actor,'forbidden')
    require(state['status']=='ready','invalid_state')
    require(state['offer']['backend']==profile.backend,'backend_mismatch')
    manifest=validate(manifest)
    require(manifest['run_id']==state['readiness']['local_run_id'],'readiness_mismatch')
    require(manifest['base_commit']==state['readiness']['commit'],'checkpoint_mismatch')
    cap=state['offers'][state['selected_offer']]['limits']
    require(all(manifest['budget'][key]<=cap[key] for key in ('tokens','cost_micros','seconds')),'scope_expansion')
    for task in manifest['tasks']:
        require(task['owner']==actor and task.get('session_id')==state['readiness']['session_id'],'readiness_mismatch')
        require(task['contracts'].get('share_plan_hash')==state['offer']['plan_hash'],'plan_mismatch')
        for key in ('files','resources','actions'):
            require(set(task[key])<=set(state['offer']['scope'][key]),'scope_expansion')
        require(set(task['tools'])<=set(state['offer']['card']['tools']),'scope_expansion')
    key=hashlib.sha256((share_id+':'+str(state['assignment_generation'])).encode()).hexdigest()
    fingerprint=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    with dispatcher.ledger.transaction() as db:
        db.execute('CREATE TABLE IF NOT EXISTS share_launches(id TEXT PRIMARY KEY,manifest TEXT NOT NULL,status TEXT NOT NULL)')
        prior=db.execute('SELECT * FROM share_launches WHERE id=?',(key,)).fetchone()
        if prior:
            require(prior['manifest']==fingerprint,'plan_mismatch')
            return dict(status=prior['status'],run_id=manifest['run_id'],launched=False,reconciliation_required=True)
        db.execute('INSERT INTO share_launches VALUES(?,?,?)',(key,fingerprint,'unknown'))
    # Start intent is durable before any execution. A crash at any point requires
    # reconciling this row + authority event + local run, never another start.
    entry=start(dispatcher,manifest,profile,reviewed=True,origin='skill')
    event=dict(event_id='start-'+key[:48],kind='started',assignment_generation=state['assignment_generation'],
               plan_hash=state['offer']['plan_hash'],data={k:state['readiness'][k] for k in ('local_run_id','session_id')})
    try:
        confirmed=send_event(share_id,event)
        require(confirmed['status']=='started' and confirmed['assignment_generation']==state['assignment_generation'],'stale_generation')
        current=get_share(share_id)
        require(current['status']=='started' and current['owner']==actor and current['assignment_generation']==state['assignment_generation'],'stale_generation')
        class FencedAdapter:
            integration=getattr(adapter,'integration','unsupported')
            def execute(self,task,*,heartbeat,cancel):
                def beat(**usage):
                    authority=get_share(share_id)
                    if (authority['status']!='started' or authority['owner']!=actor or
                            authority['assignment_generation']!=state['assignment_generation']):
                        return False
                    return heartbeat(**usage)
                if not beat():
                    raise ShareError('stale_generation')
                class FencedCancel:
                    def is_set(self):
                        return cancel.is_set() or not beat()
                    def set(self):
                        cancel.set()
                return adapter.execute(task,heartbeat=beat,cancel=FencedCancel())
        result=execute(dispatcher,entry,FencedAdapter(),verifier,temporal_submit=temporal_submit)
    except Exception:
        return dict(status='unknown',run_id=manifest['run_id'],launched=None,reconciliation_required=True)
    with dispatcher.ledger.transaction() as db:
        db.execute('UPDATE share_launches SET status=? WHERE id=?',(result['status'],key))
    return dict(result,share_id=share_id,assignment_generation=state['assignment_generation'])
