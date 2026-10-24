"""Single-run cross-repository feature metadata; execution stays in Dispatcher.

Trusted coordinator API, not an authentication layer. No tool/model/controller calls
are made here. External processes are launched only by explicitly authorized bindings.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import time

from .dispatcher import _canonical, _identifier, _integer, _path, _text

_HASH = re.compile(r'[a-f0-9]{64}\Z')
_SHA = re.compile(r'(?:[a-f0-9]{40}|[a-f0-9]{64})\Z')
_VERDICTS = {'PASS', 'FAIL', 'INCONCLUSIVE', 'NOT_RUN'}


def digest(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _pin(value, git=False):
    if not isinstance(value, str) or not (_SHA if git else _HASH).fullmatch(value):
        raise ValueError('Exact feature pin required')
    return value


def _bounded(value):
    raw = _canonical(value)
    if len(raw.encode()) > 1024 * 1024:
        raise ValueError('Feature metadata exceeds bounded byte limit')
    return json.loads(raw)


def admission_allowed(db, run_id, task):
    """Read within the dispatcher's admission transaction; no nested ledger."""
    row = db.execute('SELECT state FROM features WHERE run=?', (run_id,)).fetchone()
    if row is None:
        return True
    state = json.loads(row['state'])
    passport = state['passport']
    if any(not item['resolved'] for item in passport['business_invariants']):
        return False
    # External checks/controllers use their own immutable criteria pins.
    if task.get('dispatch_mode') == 'external':
        release_slots = {s['task_id'] for s in passport['release_plan']['steps']}
        if task['task_id'] in release_slots:
            # Release slots cannot be admitted by an ordinary worker claim before
            # the trusted coordinator has persisted exact authorized intent.
            return any(op['composition_id'] == state['current_composition'] and op['state'] == 'releasing'
                       and any(entry['task_id'] == task['task_id'] and entry['state'] == 'unknown'
                               and entry['attempt_id'] is None for entry in op['steps'].values())
                       for op in state['releases'].values())
        return True
    for contract in passport['contracts']:
        service_repos = {s['repository_id'] for s in passport['services']
                         if s['service_id'] in [contract['producer'], *contract['consumers']]}
        if task.get('repository_id') in service_repos:
            expected = {'revision': contract['revision'], 'schema_sha256': contract['schema_sha256'],
                        'semantics_sha256': contract['semantics_sha256']}
            if task['contracts'].get(contract['contract_id']) != expected:
                return False
    return True


def check_binding_allowed(db, run_id, task_id, binding):
    """Validate a gate against current authority inside the budget reservation tx."""
    if type(binding) is not dict or set(binding) != {'composition_id','check_id','criteria_sha256'}:
        return False
    row = db.execute('SELECT state FROM features WHERE run=?',(run_id,)).fetchone()
    if row is None: return False
    state = json.loads(row['state']); key = state['current_composition']
    if binding['composition_id'] != key: return False
    composition = state['compositions'].get(key)
    if composition is None or composition['passport_sha256'] != state['passport_sha256']: return False
    check = next((c for c in state['passport']['acceptance_protocol']['checks']
                  if c['check_id'] == binding['check_id']),None)
    return (check is not None and check['criteria_sha256'] == binding['criteria_sha256']
            and task_id in [check['task_id'], *check.get('repair_task_ids',[])])


class FeatureAuthority:
    """One feature per existing root run, with durable immutable compositions."""
    def __init__(self, dispatcher, run_id):
        if not callable(getattr(dispatcher, '_transaction', None)):
            raise ValueError('Coordinator Dispatcher required; remote fallback forbidden')
        self.dispatcher, self.run_id = dispatcher, _identifier(run_id)
        with dispatcher._transaction() as db:
            dispatcher._run(db, run_id)
            db.execute('CREATE TABLE IF NOT EXISTS features(run TEXT PRIMARY KEY, state TEXT NOT NULL)')

    def _load(self, db):
        row = db.execute('SELECT state FROM features WHERE run=?', (self.run_id,)).fetchone()
        if row is None:
            raise ValueError('Feature passport missing')
        return json.loads(row['state'])

    def _save(self, db, state):
        state = _bounded(state)
        db.execute('UPDATE features SET state=? WHERE run=?', (_canonical(state), self.run_id))

    def _passport(self, passport, db):
        p = _bounded(passport)
        required = {'feature_id', 'spec_revision', 'plan_revision', 'coordinator', 'repositories',
                    'services', 'owners', 'contracts', 'business_invariants', 'task_graph', 'budget',
                    'acceptance_protocol', 'release_plan'}
        if set(p) != required:
            raise ValueError('Invalid feature passport fields')
        _identifier(p['feature_id']); _identifier(p['coordinator'])
        _integer(p['spec_revision'], 'spec revision', 1); _integer(p['plan_revision'], 'plan revision', 1)
        _, manifest = self.dispatcher._run(db, self.run_id)
        if not manifest.get('repositories') or p['repositories'] != manifest['repositories'] or p['budget'] != manifest['budget']:
            raise ValueError('Passport must bind exact root repositories and budget')
        if type(p['owners']) is not list or not p['owners'] or len(p['owners']) > 64 or len(set(p['owners'])) != len(p['owners']):
            raise ValueError('Invalid feature owners')
        for owner in p['owners']: _identifier(owner)
        if p['coordinator'] not in p['owners']:
            raise ValueError('Coordinator must be an owner')
        repos = {r['repository_id'] for r in p['repositories']}
        services = p['services']
        if type(services) is not list or not 1 <= len(services) <= 64:
            raise ValueError('Invalid services')
        service_ids = set()
        for service in services:
            if set(service) != {'service_id', 'repository_id', 'owner'}:
                raise ValueError('Invalid service fields')
            key = _identifier(service['service_id'])
            if key in service_ids or service['repository_id'] not in repos or service['owner'] not in p['owners']:
                raise ValueError('Invalid service ownership')
            service_ids.add(key)
        if any(r['owner'] not in p['owners'] for r in p['repositories']):
            raise ValueError('Repository owner missing')
        if type(p['contracts']) is not list or len(p['contracts']) > 128:
            raise ValueError('Invalid contracts')
        contract_ids = set()
        service_owners = {s['service_id']: s['owner'] for s in services}
        for contract in p['contracts']:
            if set(contract) != {'contract_id', 'revision', 'producer', 'consumers', 'owners', 'schema_sha256', 'semantics_sha256'}:
                raise ValueError('Invalid contract fields')
            key = _identifier(contract['contract_id']); _integer(contract['revision'], 'contract revision', 1)
            _pin(contract['schema_sha256']); _pin(contract['semantics_sha256'])
            if key in contract_ids or contract['producer'] not in service_ids or type(contract['consumers']) is not list or not contract['consumers'] or not set(contract['consumers']) <= service_ids:
                raise ValueError('Invalid contract boundaries')
            contract_ids.add(key)
            needed = {service_owners[s] for s in [contract['producer'], *contract['consumers']]}
            if type(contract['owners']) is not list or not needed <= set(contract['owners']) or not set(contract['owners']) <= set(p['owners']):
                raise ValueError('Every producer/consumer owner must own the contract')
        rows = db.execute('SELECT id,packet FROM tasks WHERE run=?', (self.run_id,)).fetchall()
        tasks = {r['id']: json.loads(r['packet']) for r in rows}
        if type(p['task_graph']) is not list or len(set(p['task_graph'])) != len(p['task_graph']) or set(p['task_graph']) != set(tasks):
            raise ValueError('Feature DAG must match root tasks')
        protocol = p['acceptance_protocol']
        if set(protocol) != {'checks'} or type(protocol['checks']) is not list or not 4 <= len(protocol['checks']) <= 128:
            raise ValueError('Frozen acceptance protocol required')
        check_ids, slots, kinds = set(), set(), set()
        for check in protocol['checks']:
            if set(check) - {'check_id', 'kind', 'owner', 'task_id', 'criteria_sha256', 'repair_task_ids'} or not {'check_id', 'kind', 'owner', 'task_id', 'criteria_sha256'} <= set(check):
                raise ValueError('Invalid check fields')
            key = _identifier(check['check_id']); _pin(check['criteria_sha256'])
            task = tasks.get(check['task_id'])
            if key in check_ids or check['owner'] not in p['owners'] or check['kind'] not in {'local','contract','business','transition'} or task is None or task.get('dispatch_mode') != 'external' or task.get('budget_phase') not in {'integration','verification'} or check['task_id'] in slots:
                raise ValueError('Checks require unique frozen external root slots')
            repairs = check.get('repair_task_ids', [])
            if type(repairs) is not list or len(repairs) > 16 or len(set(repairs)) != len(repairs):
                raise ValueError('Invalid spare check slots')
            for repair in repairs:
                spare = tasks.get(repair)
                if repair in slots or repair == check['task_id'] or spare is None or spare.get('dispatch_mode') != 'external' or spare.get('budget_phase') not in {'integration','verification'}:
                    raise ValueError('Invalid spare verification slot')
                slots.add(repair)
            check_ids.add(key); slots.add(check['task_id']); kinds.add(check['kind'])
        if kinds != {'local','contract','business','transition'}:
            raise ValueError('All four acceptance levels required')
        if type(p['business_invariants']) is not list or not p['business_invariants'] or len(p['business_invariants']) > 128:
            raise ValueError('Business invariants required')
        invariant_ids = set()
        for invariant in p['business_invariants']:
            if set(invariant) != {'invariant_id','owner','check_id','resolved'} or invariant['owner'] not in p['owners'] or invariant['check_id'] not in check_ids or type(invariant['resolved']) is not bool or _identifier(invariant['invariant_id']) in invariant_ids:
                raise ValueError('Invalid business invariant')
            invariant_ids.add(invariant['invariant_id'])
        release = p['release_plan']
        if set(release) != {'environment','initial_versions','allowed_matrices','steps','observation_seconds','thresholds','initial_state_sha256','allowed_states'}:
            raise ValueError('Invalid release plan')
        _identifier(release['environment']); _integer(release['observation_seconds'], 'observation window', 1)
        def matrix(value):
            if type(value) is not dict or set(value) != service_ids:
                raise ValueError('Full version matrix required')
            for sha in value.values(): _pin(sha, True)
        matrix(release['initial_versions']); _pin(release['initial_state_sha256'])
        if type(release['allowed_matrices']) is not list or not 1 <= len(release['allowed_matrices']) <= 128:
            raise ValueError('Allowed intermediate version matrices required')
        for value in release['allowed_matrices']: matrix(value)
        if release['initial_versions'] not in release['allowed_matrices']:
            raise ValueError('Initial matrix not approved')
        if type(release['allowed_states']) is not list or not 1 <= len(release['allowed_states']) <= 128:
            raise ValueError('Exact migration/flag/config prefix states required')
        for prefix in release['allowed_states']:
            if type(prefix) is not dict or set(prefix) != {'versions','state_sha256'}:
                raise ValueError('Invalid release prefix state')
            matrix(prefix['versions']); _pin(prefix['state_sha256'])
            if prefix['versions'] not in release['allowed_matrices']:
                raise ValueError('Prefix version matrix not approved')
        if {'versions':release['initial_versions'],'state_sha256':release['initial_state_sha256']} not in release['allowed_states']:
            raise ValueError('Initial environment state not approved')
        if type(release['steps']) is not list or not 1 <= len(release['steps']) <= 64:
            raise ValueError('Release steps required')
        step_ids = set()
        for step in release['steps']:
            if set(step) != {'step_id','owner','task_id','versions','kind','recovery','irreversible','reversibility','state_sha256'}:
                raise ValueError('Invalid release step fields')
            key = _identifier(step['step_id']); matrix(step['versions'])
            task = tasks.get(step['task_id'])
            if key in step_ids or step['owner'] not in p['owners'] or step['kind'] not in {'migration','deploy','flag','compensation'} or task is None or task.get('dispatch_mode') != 'external' or step['task_id'] in slots or type(step['irreversible']) is not bool:
                raise ValueError('Release requires unique external root slots')
            _text(step['recovery'], 'release recovery'); _pin(step['state_sha256'])
            if type(step['reversibility']) is not dict or set(step['reversibility']) != {'code','schema','data','external'} or any(type(v) is not bool for v in step['reversibility'].values()):
                raise ValueError('Separate code/schema/data/external reversibility required')
            if step['irreversible'] != (not all(step['reversibility'].values())):
                raise ValueError('Irreversibility contradicts recovery dimensions')
            if {'versions':step['versions'],'state_sha256':step['state_sha256']} not in release['allowed_states']:
                raise ValueError('Unsafe intermediate migration/flag/config state')
            if step['versions'] not in release['allowed_matrices']:
                raise ValueError('Unsafe intermediate release matrix')
            step_ids.add(key); slots.add(step['task_id'])
        if type(release['thresholds']) is not list or not release['thresholds'] or len(release['thresholds']) > 64:
            raise ValueError('Observation stop thresholds required')
        metrics = set()
        for threshold in release['thresholds']:
            if set(threshold) - {'metric','min','max'} or 'metric' not in threshold or not ({'min','max'} & set(threshold)) or _identifier(threshold['metric']) in metrics:
                raise ValueError('Invalid threshold')
            for key in ('min','max'):
                if key in threshold and (type(threshold[key]) not in (int,float) or not math.isfinite(threshold[key])):
                    raise ValueError('Numeric finite threshold required')
            if threshold.get('min', -math.inf) > threshold.get('max', math.inf):
                raise ValueError('Contradictory threshold')
            metrics.add(threshold['metric'])
        return p

    def create(self, passport):
        with self.dispatcher._transaction() as db:
            p = self._passport(passport, db)
            row = db.execute('SELECT state FROM features WHERE run=?', (self.run_id,)).fetchone()
            if row:
                if json.loads(row['state'])['passport'] != p:
                    raise ValueError('Feature already bound to another passport')
            else:
                if db.execute('SELECT 1 FROM tasks WHERE run=? AND attempt>0',(self.run_id,)).fetchone():
                    raise ValueError('Freeze feature passport before execution')
                state = {'passport':p, 'passport_sha256':digest(p), 'revisions':[], 'compositions':{},
                         'current_composition':None, 'checks':{}, 'releases':{}, 'stage':'draft'}
                db.execute('INSERT INTO features VALUES(?,?)', (self.run_id, _canonical(state)))
        return self.report()

    def update_passport(self, passport, *, approvals, task_contracts=None):
        with self.dispatcher._transaction() as db:
            state = self._load(db); old = state['passport']; p = self._passport(passport, db)
            if p == old: return self.report_from(db, state)
            if p['feature_id'] != old['feature_id'] or p['plan_revision'] <= old['plan_revision'] or p['spec_revision'] < old['spec_revision']:
                raise ValueError('Feature revision must advance')
            if any(op['state'] in {'releasing','observing','unknown'} for op in state['releases'].values()):
                raise ValueError('Cannot revise active release')
            if db.execute("SELECT 1 FROM tasks WHERE run=? AND state IN ('running','submitted','unknown','cancel_requested','handoff_pending')", (self.run_id,)).fetchone():
                raise ValueError('Stop and reconcile active work before revising contracts')
            affected = {old['coordinator'], p['coordinator']}
            before = {c['contract_id']:c for c in old['contracts']}; after = {c['contract_id']:c for c in p['contracts']}
            for key in set(before) | set(after):
                if before.get(key) != after.get(key):
                    affected.update(before.get(key, {}).get('owners', [])); affected.update(after.get(key, {}).get('owners', []))
                    if key in before and key in after and after[key]['revision'] <= before[key]['revision']:
                        raise ValueError('Changed contract must advance revision')
            for field, key in (('services','service_id'),('business_invariants','invariant_id')):
                old_items={item[key]:item for item in old[field]}; new_items={item[key]:item for item in p[field]}
                for item_id in set(old_items)|set(new_items):
                    if old_items.get(item_id)!=new_items.get(item_id):
                        affected.update(item['owner'] for item in (old_items.get(item_id),new_items.get(item_id)) if item)
            if old['acceptance_protocol']!=p['acceptance_protocol']:
                affected.update(c['owner'] for c in old['acceptance_protocol']['checks']+p['acceptance_protocol']['checks'])
            if old['release_plan']!=p['release_plan']:
                affected.update(step['owner'] for step in old['release_plan']['steps']+p['release_plan']['steps'])
            if type(approvals) is not list or not affected <= set(approvals):
                raise ValueError('Affected boundary owner approval required')
            if len(state['revisions']) >= 64: raise ValueError('Revision bound reached')
            previous_packets = {}
            if task_contracts is not None:
                if type(task_contracts) is not dict or len(task_contracts) > 100:
                    raise ValueError('Invalid pending task pins')
                for task_id, contracts in task_contracts.items():
                    row = db.execute('SELECT * FROM tasks WHERE run=? AND id=?', (self.run_id, task_id)).fetchone()
                    if row is None or row['attempt'] != 0 or row['state'] not in {'pending','ready'} or type(contracts) is not dict or len(_canonical(contracts)) > 8192:
                        raise ValueError('Only unattempted pending task pins may change')
                    packet = json.loads(row['packet']); previous_packets[task_id] = packet
                    packet = dict(packet, contracts=contracts)
                    db.execute('UPDATE tasks SET packet=? WHERE run=? AND id=?', (_canonical(packet), self.run_id, task_id))
            state['revisions'].append({'passport':old,'passport_sha256':state['passport_sha256'],'previous_task_packets':previous_packets})
            state.update(passport=p, passport_sha256=digest(p), current_composition=None, stage='draft')
            self._save(db,state)
        return self.report()

    def compose(self, components, *, test_suite_sha256, environment_sha256, flags_sha256=None, data_sha256=None):
        with self.dispatcher._transaction() as db:
            state=self._load(db); p=state['passport']; components=_bounded(components)
            if set(components) != {s['service_id'] for s in p['services']}:
                raise ValueError('Composition must include every service')
            for component in components.values():
                if type(component) is not dict or set(component)-{'commit','image_digest','migration','flags_sha256'} or 'commit' not in component:
                    raise ValueError('Invalid component identity')
                _pin(component['commit'],True)
                for key in ('image_digest','flags_sha256'):
                    if key in component: _pin(component[key])
                if 'migration' in component: _text(component['migration'],'migration',256)
            for value in (test_suite_sha256,environment_sha256): _pin(value)
            for value in (flags_sha256,data_sha256):
                if value is not None: _pin(value)
            previous = state['compositions'].get(state['current_composition'])
            comparison = {'components':components,'test_suite_sha256':test_suite_sha256,'environment_sha256':environment_sha256,'flags_sha256':flags_sha256,'data_sha256':data_sha256}
            if previous and previous['passport_sha256']==state['passport_sha256'] and all(previous[k]==v for k,v in comparison.items()):
                return dict(previous,composition_id=state['current_composition'])
            composition={'composition_revision':len(state['compositions'])+1,'feature_id' :p['feature_id'],'run_id':self.run_id,'spec_revision':p['spec_revision'],
                         'plan_revision':p['plan_revision'],'passport_sha256':state['passport_sha256'],
                         'components':components,'test_suite_sha256':test_suite_sha256,
                         'environment_sha256':environment_sha256,'flags_sha256':flags_sha256,'data_sha256':data_sha256}
            key=digest(composition)
            if len(state['compositions'])>=128 and key not in state['compositions']: raise ValueError('Composition bound reached')
            if any(op['state'] in {'releasing','observing','unknown'} for op in state['releases'].values()) and state['current_composition'] != key:
                raise ValueError('Active release composition immutable')
            state['compositions'][key]=composition; state['current_composition']=key; state['stage']='integrating'
            self._save(db,state)
            return dict(composition,composition_id=key)

    def link_pr(self, repository_id, platform, number, commit, state='unknown', evidence_sha256=None):
        """Keep historical platform observations; never fetch, publish or approve."""
        _identifier(repository_id); _integer(number, 'pull request number', 1); _pin(commit, True)
        if platform not in {'github','gitlab'} or state not in {'unknown','open','closed','merged'}:
            raise ValueError('Invalid pull request reference')
        if evidence_sha256 is not None: _pin(evidence_sha256)
        if state != 'unknown' and evidence_sha256 is None:
            raise ValueError('Known platform observation requires pinned evidence')
        item = dict(repository_id=repository_id,platform=platform,number=number,commit=commit,
                    state=state,evidence_sha256=evidence_sha256)
        with self.dispatcher._transaction() as db:
            snapshot = self._load(db)
            if repository_id not in {r['repository_id'] for r in snapshot['passport']['repositories']}:
                raise ValueError('Unknown feature repository')
            history = snapshot.setdefault('pull_requests', [])
            if item not in history:
                if len(history) >= 128: raise ValueError('Pull request history bound reached')
                history.append(item); self._save(db,snapshot)
            return self.report_from(db,snapshot)

    def _composition(self,state,key):
        _pin(key)
        composition=state['compositions'].get(key)
        if composition is None or state['current_composition']!=key or composition['passport_sha256']!=state['passport_sha256']:
            raise ValueError('Stale feature composition')
        return composition

    def _root_slot(self,db,task_id,subject, *, require_verified=True):
        row=db.execute('SELECT * FROM tasks WHERE run=? AND id=?',(self.run_id,task_id)).fetchone()
        if row is None: raise ValueError('Unknown root slot')
        packet=json.loads(row['packet'])
        receipt=json.loads(row['receipt']) if row['receipt'] else {}
        if packet.get('dispatch_mode')!='external' or (require_verified and (row['state']!='verified' or receipt.get('subject')!=subject or not row['usage_known'])):
            raise ValueError('Exact independently verified root slot required')
        return row

    def record_check(self,composition_id,check_id,receipt,*,verifier):
        receipt=_bounded(receipt)
        with self.dispatcher._transaction() as db:
            state=self._load(db); self._composition(state,composition_id)
            check=next((c for c in state['passport']['acceptance_protocol']['checks'] if c['check_id']==check_id),None)
            if check is None: raise ValueError('Unknown frozen check')
            slot = receipt.get('task_id', check['task_id'])
            if slot not in [check['task_id'], *check.get('repair_task_ids', [])]: raise ValueError('Check slot not frozen')
            self._root_slot(db,slot,composition_id)
        proof=_bounded(verifier(_bounded(check),_bounded(receipt)))
        if type(proof) is not dict or proof.get('independent') is not True or proof.get('subject')!=composition_id or proof.get('verdict') not in _VERDICTS or proof.get('criteria_sha256')!=check['criteria_sha256']:
            raise ValueError('Independent frozen-check verdict required')
        _identifier(proof.get('verifier_id')); _pin(proof.get('evidence_sha256'))
        if proof['verifier_id']==check['owner']:
            raise ValueError('Check owner cannot independently verify own work')
        evidence={k:proof[k] for k in ('independent','subject','verdict','criteria_sha256','verifier_id','evidence_sha256')}
        evidence['task_id'] = slot
        with self.dispatcher._transaction() as db:
            state=self._load(db); self._composition(state,composition_id)
            self._root_slot(db,slot,composition_id)
            key=composition_id+':'+check_id
            if key in state['checks'] and state['checks'][key]!=evidence:
                raise ValueError('Check receipt immutable; use new composition/slot')
            state['checks'][key]=evidence; state['stage']='verifying'; self._save(db,state)
        return self.report()

    def _authorization(self,p,composition_id,environment,authorization,owner=None):
        if type(authorization) is not dict or set(authorization)!={'confirmed','actor','environment','composition_id'} or authorization.get('confirmed') is not True or authorization.get('actor') not in ({owner} if owner else set(p['owners'])) or authorization.get('environment')!=environment or authorization.get('composition_id')!=composition_id:
            raise ValueError('Explicit exact environment authorization required')

    def begin_release(self,composition_id,environment,*,authorization,observed_versions,observed_state_sha256):
        with self.dispatcher._transaction() as db:
            state=self._load(db); composition=self._composition(state,composition_id); p=state['passport']
            self._authorization(p,composition_id,environment,authorization,p['coordinator'])
            key=digest({'composition_id':composition_id,'environment':environment})
            if key in state['releases']: return state['releases'][key]
            if self.report_from(db,state)['status']!='release_ready': raise ValueError('Feature not release ready')
            release=p['release_plan']
            if environment!=release['environment'] or observed_state_sha256!=release['initial_state_sha256'] or observed_versions!=release['initial_versions'] or release['steps'][-1]['versions']!={k:v['commit'] for k,v in composition['components'].items()}:
                raise ValueError('Release environment/version drift')
            key=digest({'composition_id':composition_id,'environment':environment})
            if key not in state['releases']:
                state['releases'][key]={'operation_id':key,'composition_id':composition_id,'environment':environment,'state':'releasing','versions':observed_versions,'state_sha256':observed_state_sha256,'steps':{},'observation_started':None}
                state['stage']='releasing'; self._save(db,state)
            return state['releases'][key]

    def begin_step(self,operation_id,step_id,*,authorization,observed_versions,observed_state_sha256):
        # Intent before admission: a crash cannot launch a second process. Incomplete
        # intent is unknown and needs explicit root reconciliation; never replay.
        with self.dispatcher._transaction() as db:
            state=self._load(db); op=state['releases'].get(operation_id)
            if op is None: raise ValueError('Unknown release')
            self._composition(state,op['composition_id']); p=state['passport']; steps=p['release_plan']['steps']
            step=next((s for s in steps if s['step_id']==step_id),None)
            if step is None: raise ValueError('Unknown release step')
            self._authorization(p,op['composition_id'],op['environment'],authorization,step['owner'])
            if step_id in op['steps']: return dict(op['steps'][step_id],launch_allowed=False)
            if self.report_from(db, state)['blockers']:
                raise ValueError('Root authority blocks release step')
            index=steps.index(step)
            if op['state']!='releasing' or observed_state_sha256!=op['state_sha256'] or observed_versions!=op['versions'] or any(op['steps'].get(s['step_id'],{}).get('state')!='completed' for s in steps[:index]):
                raise ValueError('Release ordering/version drift')
            op['steps'][step_id]={'state':'unknown','task_id':step['task_id'],'attempt_id':None,'subject':op['composition_id'],'versions':step['versions'],'state_sha256':step['state_sha256']}
            self._save(db,state)
        task=self.dispatcher.claim_task(self.run_id,step['task_id'])
        with self.dispatcher._transaction() as db:
            state=self._load(db); entry=state['releases'][operation_id]['steps'][step_id]
            if task is None:
                entry['state']='blocked'; self._save(db,state); return dict(entry,launch_allowed=False)
            # Cancellation/authority may change between intent and root claim.
            run, _ = self.dispatcher._run(db, self.run_id)
            row = db.execute('SELECT state,attempt FROM tasks WHERE run=? AND id=?',(self.run_id,step['task_id'])).fetchone()
            report = self.report_from(db, state)
            unsafe = set(report['blockers']) - {'root_work_active'}
            other_active = any(t['task_id'] != step['task_id'] and t['state'] in {'running', 'submitted'}
                               for t in report['tasks'])
            if unsafe or other_active or run['cancel'] or row['state'] != 'running' or row['attempt'] != task['attempt_id']:
                entry.update(state='unknown',attempt_id=task['attempt_id']); state['releases'][operation_id]['state']='unknown'
                self._save(db,state); return dict(entry,launch_allowed=False)
            entry.update(state='running',attempt_id=task['attempt_id']); self._save(db,state)
            return dict(entry,launch_allowed=True,task=task)

    def finish_step(self,operation_id,step_id,receipt,*,verifier):
        receipt=_bounded(receipt)
        with self.dispatcher._transaction() as db:
            state=self._load(db); op=state['releases'].get(operation_id)
            if op is None or step_id not in op['steps']: raise ValueError('Unknown release intent')
            entry=op['steps'][step_id]
            if entry['state']=='completed': return dict(entry)
            step=next(s for s in state['passport']['release_plan']['steps'] if s['step_id']==step_id)
        proof=_bounded(verifier(_bounded(step),_bounded(receipt)))
        if type(proof) is not dict or proof.get('independent') is not True or proof.get('subject')!=op['composition_id']:
            raise ValueError('Independent release outcome required')
        _pin(proof.get('evidence_sha256'))
        with self.dispatcher._transaction() as db:
            state=self._load(db); op=state['releases'][operation_id]; self._composition(state,op['composition_id']); entry=op['steps'][step_id]
            row=self._root_slot(db,step['task_id'],op['composition_id'],require_verified=False)
            run, _ = self.dispatcher._run(db,self.run_id)
            if run['cancel']:
                entry['state']='cancelled' if row['usage_known'] and row['state'] not in {'running','submitted','unknown','cancel_requested'} else 'unknown'
                op['state']=entry['state']
            elif entry['attempt_id']!=row['attempt'] or row['state'] in {'running','submitted','unknown','cancel_requested'} or not row['usage_known']:
                entry['state']='unknown'; op['state']='unknown'
            elif proof.get('verdict')=='PASS' and proof.get('versions')==step['versions'] and proof.get('state_sha256')==step['state_sha256'] and row['state']=='verified' and json.loads(row['receipt'])['subject']==op['composition_id']:
                entry.update(state='completed',evidence_sha256=proof['evidence_sha256']); op['versions']=step['versions']; op['state_sha256']=step['state_sha256']; op['state']='releasing'
                if all(op['steps'].get(s['step_id'],{}).get('state')=='completed' for s in state['passport']['release_plan']['steps']):
                    op.update(state='observing',observation_started=time.time())
            else:
                entry['state']='failed'; op['state']='failed'
            state['stage']=op['state']; self._save(db,state)
            return dict(entry)


    def reconcile_step(self,operation_id,step_id,receipt,*,verifier):
        """Close an orphan intent after root reconciliation; never resumes action.

        Successful work needs a new explicitly authorized plan/slot after an unknown
        process was reconciled failed. Reconciliation is not deployment acceptance.
        """
        receipt=_bounded(receipt)
        with self.dispatcher._transaction() as db:
            state=self._load(db); op=state['releases'].get(operation_id)
            if op is None or step_id not in op['steps']: raise ValueError('Unknown release intent')
            entry=op['steps'][step_id]
            step=next(s for s in state['passport']['release_plan']['steps'] if s['step_id']==step_id)
        proof=_bounded(verifier(_bounded(step),_bounded(receipt)))
        if type(proof) is not dict or proof.get('independent') is not True or proof.get('subject')!=op['composition_id'] or proof.get('stopped') is not True:
            raise ValueError('Independent stopped reconciliation proof required')
        _pin(proof.get('evidence_sha256'))
        with self.dispatcher._transaction() as db:
            state=self._load(db); op=state['releases'][operation_id]; entry=op['steps'][step_id]
            row=self._root_slot(db,step['task_id'],op['composition_id'],require_verified=False)
            if row['state'] in {'running','submitted','unknown','cancel_requested'} or not row['usage_known']:
                raise ValueError('Reconcile root outcome and usage first')
            if row['attempt']==0 and proof.get('not_started') is not True:
                raise ValueError('Unstarted intent needs no-launch proof')
            if entry['state']=='completed': return dict(entry)
            run,_=self.dispatcher._run(db,self.run_id)
            entry.update(state='cancelled' if run['cancel'] else 'failed',attempt_id=row['attempt'],evidence_sha256=proof['evidence_sha256'])
            op['state']=entry['state']; state['stage']=op['state']; self._save(db,state)
            return dict(entry)

    def observe(self,operation_id,receipt,*,verifier):
        receipt=_bounded(receipt)
        with self.dispatcher._transaction() as db:
            state=self._load(db); op=state['releases'].get(operation_id)
            if op is None or op['state'] not in {'observing','accepted'}: raise ValueError('Release not observing')
            self._composition(state,op['composition_id']); plan=state['passport']['release_plan']
        proof=_bounded(verifier(_bounded(plan),_bounded(receipt)))
        if type(proof) is not dict or proof.get('independent') is not True or proof.get('subject')!=op['composition_id'] or proof.get('versions')!=op['versions'] or proof.get('state_sha256')!=op['state_sha256']:
            raise ValueError('Independent observation proof required')
        _pin(proof.get('evidence_sha256'))
        seconds=proof.get('observed_seconds'); metrics=proof.get('metrics',{})
        if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<plan['observation_seconds'] or time.time()-op['observation_started']<plan['observation_seconds']:
            raise ValueError('Observation window incomplete')
        passed=proof.get('verdict')=='PASS'
        for threshold in plan['thresholds']:
            value=metrics.get(threshold['metric'])
            if type(value) not in (int,float) or not math.isfinite(value): raise ValueError('Observed numeric metric missing')
            passed=passed and threshold.get('min',-math.inf)<=value<=threshold.get('max',math.inf)
        with self.dispatcher._transaction() as db:
            state=self._load(db); op=state['releases'][operation_id]; self._composition(state,op['composition_id'])
            report = self.report_from(db, state)
            if report['blockers']:
                raise ValueError('Root authority blocks observation acceptance')
            observation={'evidence_sha256':proof['evidence_sha256'],'metrics':metrics,'observed_seconds':seconds,'state_sha256':proof['state_sha256']}
            if 'observation' in op:
                if op['observation'] != observation: raise ValueError('Observation receipt immutable')
                return self.report_from(db,state)
            op.update(state='accepted' if passed else 'failed',observation=observation)
            state['stage']=op['state']; self._save(db,state)
        return self.report()

    def report_from(self,db,state):
        run,manifest=self.dispatcher._run(db,self.run_id)
        rows=db.execute('SELECT * FROM tasks WHERE run=?',(self.run_id,)).fetchall()
        p=state['passport']; key=state['current_composition']; composition=state['compositions'].get(key)
        checks=[]; blockers=[]
        if any(not i['resolved'] for i in p['business_invariants']): blockers.append('unresolved_business_invariants')
        for check in p['acceptance_protocol']['checks']:
            proof=state['checks'].get(str(key)+':'+check['check_id']) if composition and composition['passport_sha256']==state['passport_sha256'] else None
            if proof:
                try: self._root_slot(db,proof['task_id'],key)
                except ValueError: proof=None
            checks.append(dict(check,verdict=proof['verdict'] if proof else 'NOT_RUN',evidence=proof,**({k:proof[k] for k in ('subject','criteria_sha256','verifier_id','evidence_sha256')} if proof else {})))
        if not composition: blockers.append('composition_missing')
        if any(c['verdict']!='PASS' for c in checks): blockers.append('acceptance_incomplete')
        if any(r['state'] in {'unknown','cancel_requested'} or not r['usage_known'] for r in rows): blockers.append('root_outcome_unknown')
        if any(r['state'] in {'running','submitted'} for r in rows): blockers.append('root_work_active')
        if run['cancel']: blockers.append('root_cancelled')
        if any(r['state']=='failed' for r in rows): blockers.append('root_task_failed')
        implementation=[r for r in rows if json.loads(r['packet']).get('dispatch_mode','auto')=='auto']
        if any(r['state']!='verified' for r in implementation): blockers.append('implementation_incomplete')
        if any(not admission_allowed(db,self.run_id,json.loads(r['packet'])) for r in implementation): blockers.append('contract_task_pins_stale')
        if composition and p['release_plan']['steps'][-1]['versions']!={k:v['commit'] for k,v in composition['components'].items()}: blockers.append('release_final_matrix_mismatch')
        status=state['stage']
        releases=list(state['releases'].values())
        current=[o for o in releases if o['composition_id']==key]
        if current: status=current[-1]['state']
        elif not blockers: status='release_ready'
        elif any(c['verdict']=='FAIL' for c in checks): status='failed'
        elif 'root_outcome_unknown' in blockers: status='unknown'
        elif 'root_cancelled' in blockers: status='cancel_requested' if any(r['state'] in {'running','unknown','cancel_requested'} for r in rows) else 'cancelled'
        elif 'unresolved_business_invariants' in blockers or 'contract_task_pins_stale' in blockers: status='blocked'
        elif not composition: status='implementing' if any(r['attempt'] for r in implementation) else 'contracts_ready'
        else: status='verifying' if any(c['verdict']!='NOT_RUN' for c in checks) else 'integrating'
        # Global liabilities/cancellation fence every business phase, including
        # previously accepted releases; read-only reports never erase new risk.
        if 'root_task_failed' in blockers: status='failed'
        if 'root_outcome_unknown' in blockers: status='unknown'
        if 'root_cancelled' in blockers:
            status='cancel_requested' if any(r['state'] in {'running','unknown','cancel_requested'} for r in rows) else 'cancelled'
        repo_commits = {}
        if composition:
            for service in p['services']:
                repo_commits.setdefault(service['repository_id'], set()).add(composition['components'][service['service_id']]['commit'])
        pull_requests = [dict(item,current=item['commit'] in repo_commits.get(item['repository_id'], set()))
                         for item in state.get('pull_requests', [])]
        return {'feature_id':p['feature_id'],'run_id':self.run_id,'backend':run['backend'],'status':status,
                'spec_revision':p['spec_revision'],'plan_revision':p['plan_revision'],'passport_sha256':state['passport_sha256'],
                'passport':p,'composition_id':key,'composition':dict(composition,composition_id=key) if composition else None,'checks':checks,'blockers':blockers,
                'plan_sha256':run['digest'],'budget':manifest['budget'],'repositories':p['repositories'],'services':p['services'],'contracts':p['contracts'],
                'release':current[-1] if current else None,'release_ready':status=='release_ready','accepted':status=='accepted','human_actions':blockers,
                'steps':[dict(s,status=(current[-1]['steps'].get(s['step_id'],{}).get('state','pending') if current else 'pending')) for s in p['release_plan']['steps']],
                'releases':releases,'revisions':state['revisions'],
                'usage':{'tokens':sum(r['tokens'] for r in rows),'cost_micros':sum(r['cost'] for r in rows),'reserved_tokens':sum(r['reserve_tokens'] for r in rows),'reserved_cost_micros':sum(r['reserve_cost'] for r in rows),'known':all(r['usage_known'] for r in rows)},
                'pull_requests':pull_requests,'tasks':[self.dispatcher._task_report(r) for r in rows]}

    def report(self):
        with self.dispatcher._transaction() as db:
            return self.report_from(db,self._load(db))

    def export_progress(self,plan_path):
        path=Path(plan_path).absolute()
        if any(p.is_symlink() for p in (path,*path.parents)): raise ValueError('Source plan links forbidden')
        if not path.is_file() or path.stat().st_size>1024*1024: raise ValueError('Bounded existing source plan required')
        report=self.report(); begin='<!-- palarran-feature-progress:start -->'; end='<!-- palarran-feature-progress:end -->'
        text=path.read_text(); section=begin+'\n```json\n'+json.dumps(report,indent=2,sort_keys=True)+'\n```\n'+end
        if text.count(begin)!=text.count(end) or text.count(begin)>1: raise ValueError('Ambiguous source progress markers')
        if begin in text:
            start=text.index(begin); stop=text.index(end,start)+len(end); text=text[:start]+section+text[stop:]
        else: text=text.rstrip()+'\n\n'+section+'\n'
        path.write_text(text)
        return report
