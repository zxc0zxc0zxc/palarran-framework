"""Deterministic two-party task sharing. No credentials, transport or execution."""
import copy
import hashlib
import json
import re

ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
COMMIT = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
CONSENT = frozenset({'offered', 'assigned', 'plan_proposed', 'plan_accepted',
                     'ownership_transferred', 'accepted', 'rework_requested'})
TERMINAL = frozenset({'accepted', 'cancelled', 'expired', 'rework_requested'})


class ShareError(ValueError):
    """Arguments contain only safe error codes."""


def require(condition, code='invalid_request'):
    if not condition:
        raise ShareError(code)


def canonical(value):
    try:
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        require(len(raw) <= 24000)
        return raw
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ShareError('invalid_request') from None


def ident(value):
    require(isinstance(value, str) and ID.fullmatch(value))
    return value


def digest(value):
    require(isinstance(value, str) and HASH.fullmatch(value))
    return value


def integer(value, maximum=10**15, minimum=0):
    require(type(value) is int and minimum <= value <= maximum)
    return value


def fields(value, keys, optional=()):
    require(type(value) is dict and set(keys) <= value.keys() and not value.keys()-set(keys)-set(optional))


def strings(value, *, paths=False):
    require(type(value) is list and len(value) <= 32 and all(isinstance(v,str) for v in value)
            and len(set(value)) == len(value))
    for item in value:
        require(isinstance(item, str) and 0 < len(item) <= 256 and not any(ord(c)<32 for c in item))
        if paths:
            require(not item.startswith(('/', '.git', '.env')) and '\\' not in item and ':' not in item
                    and not any(p in ('', '.', '..') for p in item.split('/'))
                    and not any(c in item for c in '*?['))
        else:
            ident(item)


def limits(value):
    fields(value, {'tokens', 'cost_micros', 'seconds'})
    for item in value.values():
        integer(item, minimum=1)


def usage(value):
    fields(value, {'usage_known', 'tokens', 'cost_micros'})
    require(type(value['usage_known']) is bool)
    for k in ('tokens', 'cost_micros'):
        if value[k] is None:
            require(value['usage_known'] is False)
        else:
            integer(value[k])


def create(offer, actor, now):
    canonical(offer)
    fields(offer, {'share_id', 'task_id', 'run_id', 'repository', 'room', 'mode', 'plan_hash',
                   'base_commit', 'expires_at', 'card', 'scope', 'limits', 'backend'}, {'previous_share_id'})
    ident(actor)
    for k in ('share_id', 'task_id', 'run_id', 'repository', 'room'):
        ident(offer[k])
    if 'previous_share_id' in offer:
        ident(offer['previous_share_id'])
    digest(offer['plan_hash'])
    require(isinstance(offer['base_commit'], str) and COMMIT.fullmatch(offer['base_commit']))
    require(offer['backend'] in ('local', 'temporal') and offer['mode'] in ('new', 'continue'))
    integer(now)
    integer(offer['expires_at'], minimum=now+1, maximum=now+7*86400)
    fields(offer['card'], {'goal', 'outcome', 'estimate', 'uncertainties', 'tools', 'data_categories', 'checks'})
    for k in ('goal', 'outcome', 'estimate'):
        v=offer['card'][k]
        require(isinstance(v,str) and 0<len(v)<=400 and not any(ord(c)<32 for c in v))
    for k in ('uncertainties', 'tools', 'data_categories', 'checks'):
        strings(offer['card'][k])
    fields(offer['scope'], {'files', 'resources', 'actions', 'contracts'})
    for k,v in offer['scope'].items():
        strings(v, paths=k=='files')
    limits(offer['limits'])
    return dict(offer=copy.deepcopy(offer), sender=actor, owner=actor, receiver=None, status='requested',
                assignment_generation=0, attempt_id=0, offers={}, events={}, history=[], usage={},
                checkpoint=None, readiness=None, result=None, created_at=now, updated_at=now)


def apply(state, event, actor, now):
    """Generation is checked before transitions; exact duplicate returns prior state."""
    canonical(event)
    fields(event, {'event_id', 'kind', 'assignment_generation', 'plan_hash', 'data'})
    require(isinstance(event['kind'],str))
    ident(actor); ident(event['event_id']); digest(event['plan_hash']); integer(now)
    integer(event['assignment_generation'])
    require(type(event['data']) is dict)
    s=copy.deepcopy(state)
    fingerprint=hashlib.sha256(canonical(dict(event=event,actor=actor))).hexdigest()
    prior=s['events'].get(event['event_id'])
    if prior:
        require(prior == fingerprint, 'idempotency_conflict')
        return s
    require(len(s['events'])<256, 'capacity_exhausted')
    require(event['plan_hash']==s['offer']['plan_hash'], 'plan_mismatch')
    require(event['assignment_generation']==s['assignment_generation'], 'stale_generation')
    k,d=event['kind'],event['data']; status=s['status']
    sender=actor==s['sender']; receiver=actor==s['receiver']
    if now>=s['offer']['expires_at'] and k not in ('expired','cancel_requested','cancelled','progress','result_submitted','accepted','usage_reconciled'):
        raise ShareError('expired')
    require(status not in TERMINAL or k=='usage_reconciled', 'terminal')
    if k=='offered':
        fields(d, {'offer_id','limits'})
        require(not sender and status=='requested', 'invalid_state')
        ident(d['offer_id']); limits(d['limits'])
        require(len(s['offers'])<32 and d['offer_id'] not in s['offers'], 'offer_conflict')
        require(not any(v['actor']==actor for v in s['offers'].values()), 'offer_conflict')
        require(all(d['limits'][key]<=s['offer']['limits'][key] for key in d['limits']), 'scope_expansion')
        s['offers'][d['offer_id']]=dict(actor=actor,limits=d['limits'])
    elif k=='assigned':
        fields(d, {'offer_id'});require(sender and status=='requested','invalid_state')
        require(d['offer_id'] in s['offers'],'offer_missing')
        s['receiver']=s['offers'][d['offer_id']]['actor'];s['selected_offer']=d['offer_id'];s['status']='assigned'
    elif k=='plan_proposed':
        fields(d,set());require(sender and status=='assigned','invalid_state');s['status']='plan_proposed'
    elif k=='plan_accepted':
        fields(d,set());require(receiver and status=='plan_proposed','invalid_state');s['status']='handoff_pending'
    elif k=='checkpoint_published':
        fields(d,{'commit','remote','branch','evidence_sha256'})
        require(sender and status=='handoff_pending' and s['offer']['mode']=='continue','invalid_state')
        require(isinstance(d['commit'],str) and COMMIT.fullmatch(d['commit']));ident(d['remote']);ident(d['branch']);digest(d['evidence_sha256'])
        require(s['checkpoint'] is None,'checkpoint_frozen');s['checkpoint']=d
    elif k=='receiver_ready':
        fields(d,{'commit','evidence_sha256','session_id','local_run_id'})
        require(receiver and status=='handoff_pending','invalid_state')
        expected=s['offer']['base_commit'] if s['offer']['mode']=='new' else (s['checkpoint'] or {}).get('commit')
        require(expected is not None and d['commit']==expected,'checkpoint_mismatch')
        digest(d['evidence_sha256']);ident(d['session_id']);ident(d['local_run_id'])
        require(d['local_run_id']!=s['offer']['run_id'],'separate_run_required')
        require(s['readiness'] is None,'readiness_frozen');s['readiness']=d
    elif k=='ownership_transferred':
        fields(d,{'stopped','unknown_operations','usage_known','tokens','cost_micros','evidence_sha256'})
        require(sender and status=='handoff_pending' and s['readiness'] is not None,'invalid_state')
        require(d['stopped'] is True and d['unknown_operations'] is False,'reconciliation_required')
        usage({key:d[key] for key in ('usage_known','tokens','cost_micros')});digest(d['evidence_sha256'])
        s['usage'][actor]={key:d[key] for key in ('usage_known','tokens','cost_micros')}
        s['owner']=s['receiver'];s['assignment_generation']+=1;s['status']='ready'
    elif k=='started':
        fields(d,{'local_run_id','session_id'})
        require(receiver and status=='ready','invalid_state')
        require(all(d[key]==s['readiness'][key] for key in d),'readiness_mismatch')
        s['attempt_id']+=1;s['status']='started'
    elif k=='progress':
        fields(d,{'completed','blockers','next','usage_known','tokens','cost_micros'})
        require(receiver and status in ('started','cancel_requested'),'invalid_state')
        for key in ('completed','blockers'):
            strings(d[key])
        ident(d['next']);_record_usage(s,actor,d);s['progress']=d
    elif k=='usage_reconciled':
        fields(d,{'stopped','usage_known','tokens','cost_micros','evidence_sha256'})
        require((sender or receiver) and actor in s['usage'] and not s['usage'][actor]['usage_known'],'invalid_state')
        require(d['stopped'] is True and d['usage_known'] is True,'reconciliation_required');digest(d['evidence_sha256'])
        old=copy.deepcopy(s['usage'][actor]);s['usage'][actor]['usage_known']=True
        _record_usage(s,actor,d)
        require(all(s['usage'][actor][key] is not None and (old[key] is None or s['usage'][actor][key]>=old[key]) for key in ('tokens','cost_micros')),'usage_regression')
    elif k=='result_submitted':
        fields(d,{'subject','evidence_sha256','checks','usage_known','tokens','cost_micros','stopped'})
        require(receiver and status=='started','invalid_state')
        require(isinstance(d['subject'],str) and COMMIT.fullmatch(d['subject']));digest(d['evidence_sha256'])
        require(d['stopped'] is True,'reconciliation_required')
        require(type(d['checks']) is dict and 1<=len(d['checks'])<=32)
        for key,value in d['checks'].items():
            ident(key);require(value in ('PASS','FAIL','NOT_RUN'))
        _record_usage(s,actor,d);s['result']=d;s['status']='result_submitted'
    elif k=='accepted':
        fields(d,{'subject','evidence_sha256','independent'})
        require(sender and status=='result_submitted','invalid_state')
        require(d['independent'] is True and d['subject']==s['result']['subject'],'verification_required')
        digest(d['evidence_sha256']);s['status']='accepted'
    elif k=='rework_requested':
        fields(d,{'evidence_sha256'});require(sender and status=='result_submitted','invalid_state')
        digest(d['evidence_sha256']);s['status']='rework_requested'
        # A new reviewed offer/attempt is required; a start event cannot replay this one.
    elif k=='cancel_requested':
        fields(d,set());require(sender or receiver,'forbidden');s['status']='cancel_requested'
    elif k=='cancelled':
        fields(d,{'stopped','usage_known','tokens','cost_micros','evidence_sha256'})
        require(status=='cancel_requested' and actor==s['owner'],'invalid_state')
        require(d['stopped'] is True,'reconciliation_required');digest(d['evidence_sha256'])
        _record_usage(s,actor,d);s['status']='cancelled'
    elif k=='expired':
        fields(d,set());require(sender and now>=s['offer']['expires_at'] and status in ('requested','assigned','plan_proposed'),'invalid_state');s['status']='expired'
    else:
        raise ShareError('unknown_event')
    s['updated_at']=now;s['events'][event['event_id']]=fingerprint
    s['history'].append(dict(event_id=event['event_id'],kind=k,actor=actor,at=now,
                             assignment_generation=s['assignment_generation'],attempt_id=s['attempt_id']))
    require(len(canonical(s))<=24000,'capacity_exhausted')
    return s


def _record_usage(s, actor, data):
    current={key:data[key] for key in ('usage_known','tokens','cost_micros')};usage(current)
    old=s['usage'].get(actor)
    if old:
        for key in ('tokens','cost_micros'):
            if current[key] is None and old[key] is not None:
                current[key]=old[key]
            require(old[key] is None or current[key] is None or current[key]>=old[key], 'usage_regression')
        require(old['usage_known'] or current['usage_known'] is False,'usage_reconciliation_required')
    if actor==s['receiver']:
        cap=s['offers'][s['selected_offer']]['limits']
        if any(current[key] is not None and current[key]>cap[key] for key in ('tokens','cost_micros')):
            require(data.get('stopped') is True,'budget_exhausted')
    s['usage'][actor]=current
