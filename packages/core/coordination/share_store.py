"""Sharing transitions within the existing authenticated coordination transaction."""
import hashlib
import json
import time

if __package__:
    from . import share
else:
    import share

FIELDS = {
    'share.create': ({'project','request_id','offer','confirmed'},set()),
    'share.event': ({'project','request_id','share_id','event'}, {'confirmed'}),
    'share.get': ({'project','share_id'},set()),
}


def initialize(connection):
    connection.execute('CREATE TABLE IF NOT EXISTS shares(project TEXT NOT NULL,id TEXT NOT NULL,room TEXT NOT NULL,state TEXT NOT NULL,PRIMARY KEY(project,id))')


def validate(operation, payload):
    required, optional=FIELDS[operation]
    share.fields(payload,required,optional)
    if 'share_id' in payload:
        share.ident(payload['share_id'])
    if 'confirmed' in payload:
        share.require(payload['confirmed'] is True,'confirmation_required')


def read(connection, principal, payload):
    row=connection.execute('SELECT state FROM shares WHERE project=? AND id=?',
                           (payload['project'],payload['share_id'])).fetchone()
    share.require(row is not None,'share_missing')
    return {'share':json.loads(row['state'])}


def mutate(store, connection, principal, operation, payload):
    actor,project=principal['actor'],payload['project']
    now=int(time.time())
    if operation=='share.create':
        offer=payload['offer']
        state=share.create(offer,actor,now)
        share.require(offer['backend']=='local','backend_mismatch')
        store._room(connection,dict(project=project,room=offer['room']))
        share.require(connection.execute('SELECT 1 FROM shares WHERE project=? AND id=?',
                                        (project,offer['share_id'])).fetchone() is None,'share_exists')
        share.require(connection.execute('SELECT count(*) FROM shares WHERE project=?',(project,)).fetchone()[0]<100,'capacity_exhausted')
        if 'previous_share_id' in offer:
            prior=read(connection,principal,dict(project=project,share_id=offer['previous_share_id']))['share']
            share.require(prior['sender']==actor and prior['status'] in share.TERMINAL, 'previous_share_active')
            share.require(all(offer[key]==prior['offer'][key] for key in ('repository','task_id','run_id')), 'lineage_mismatch')
            inherited=dict(prior.get('prior_usage',{}));inherited[offer['previous_share_id']]=prior['usage']
            share.require(len(inherited)<=8,'capacity_exhausted');state['prior_usage']=inherited
            share.require(len(share.canonical(state))<=24000,'capacity_exhausted')
        kind='requested'
    else:
        state=read(connection,principal,payload)['share']
        old=state
        event=payload['event']
        share.require(type(event) is dict)
        if event.get('kind') in share.CONSENT:
            share.require(payload.get('confirmed') is True,'confirmation_required')
        # Membership is already authenticated by the coordination service.
        state=share.apply(state,event,actor,now)
        if state==old:
            return {'share':state}
        kind=event['kind']
    room=state['offer']['room']
    share.require(connection.execute('SELECT count(*) FROM messages WHERE project=? AND room=?',
                                    (project,room)).fetchone()[0]<2000,'capacity_exhausted')
    raw=share.canonical(state).decode()
    connection.execute('INSERT INTO shares VALUES(?,?,?,?) ON CONFLICT(project,id) DO UPDATE SET state=excluded.state',
                       (project,state['offer']['share_id'],room,raw))
    notice=dict(share_id=state['offer']['share_id'],event=kind,assignment_generation=state['assignment_generation'],
                plan_hash=state['offer']['plan_hash'],state_sha256=hashlib.sha256(raw.encode()).hexdigest())
    connection.execute('INSERT INTO messages(project,room,actor,kind,text,recipient,created_at) VALUES(?,?,?,?,?,?,?)',
                       (project,room,actor,'status',json.dumps(notice,sort_keys=True),None,now))
    return {'share':state}
