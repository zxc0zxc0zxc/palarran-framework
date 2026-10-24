"""Single-run cross-repository feature metadata; execution stays in Dispatcher.

Trusted coordinator API, not an authentication layer. No tool/model/controller calls
are made here. External processes are launched only by explicitly authorized bindings.
"""
import json
import math
from pathlib import Path
import time
from .feature_validation import digest, _pin, _bounded, validate_passport
from .primitives import canonical, identifier, integer, text
from .ledger import SQLiteLedger
from .states import CheckVerdict, FeatureState, TaskState
_VERDICTS = {item.value for item in CheckVerdict}


def _release_slot_has_intent(state, task_id):
    """Ordinary workers cannot launch a controller without durable exact intent."""
    for operation in state['releases'].values():
        if operation['composition_id'] != state['current_composition']:
            continue
        if operation['state'] != FeatureState.RELEASING.value:
            continue
        for entry in operation['steps'].values():
            if (entry['task_id'] == task_id
                    and entry['state'] == TaskState.UNKNOWN.value
                    and entry['attempt_id'] is None):
                return True
    return False


def admission_allowed(db, run_id, task):
    """Read inside the dispatcher's admission transaction; no nested ledger."""
    row = db.execute('SELECT state FROM features WHERE run=?', (run_id,)).fetchone()
    if row is None:
        return True
    state = json.loads(row['state'])
    passport = state['passport']
    if any(not item['resolved'] for item in passport['business_invariants']):
        return False
    # External checks use their frozen criteria; controllers also require intent.
    if task.get('dispatch_mode') == 'external':
        release_slots = {step['task_id'] for step in passport['release_plan']['steps']}
        if task['task_id'] in release_slots:
            return _release_slot_has_intent(state, task['task_id'])
        return True
    for contract in passport['contracts']:
        participants = [contract['producer'], *contract['consumers']]
        service_repos = {
            service['repository_id'] for service in passport['services']
            if service['service_id'] in participants
        }
        if task.get('repository_id') in service_repos:
            expected = {
                'revision': contract['revision'],
                'schema_sha256': contract['schema_sha256'],
                'semantics_sha256': contract['semantics_sha256'],
            }
            if task['contracts'].get(contract['contract_id']) != expected:
                return False
    return True


def check_binding_allowed(db, run_id, task_id, binding):
    """Validate a gate against current authority inside the budget reservation tx."""
    if (
        type(binding) is not dict
        or set(binding) != {'composition_id', 'check_id', 'criteria_sha256'}
    ):
        return False
    row = db.execute('SELECT state FROM features WHERE run=?', (run_id,)).fetchone()
    if row is None:
        return False
    state = json.loads(row['state'])
    key = state['current_composition']
    if binding['composition_id'] != key:
        return False
    composition = state['compositions'].get(key)
    if composition is None or composition['passport_sha256'] != state['passport_sha256']:
        return False
    check = next(
        (
            c for c in state['passport']['acceptance_protocol']['checks'] if c['check_id'] == binding['check_id']
        ),
        None
    )
    return (
        check is not None
        and check['criteria_sha256'] == binding['criteria_sha256']
        and (task_id in [check['task_id'], *check.get('repair_task_ids', [])])
    )


class FeatureAuthority:
    """One feature per existing root run, with durable immutable compositions."""

    def __init__(self, dispatcher, run_id):
        self.dispatcher = dispatcher
        self.run_id = identifier(run_id)
        if not callable(getattr(getattr(dispatcher, 'ledger', None), 'transaction', None)):
            raise ValueError('Coordinator Dispatcher required; remote fallback forbidden')
        with self.ledger.transaction() as db:
            self.ledger.read_run(db, self.run_id)
            db.execute(
                'CREATE TABLE IF NOT EXISTS features(run TEXT PRIMARY KEY, state TEXT NOT NULL)'
            )

    @property
    def ledger(self):
        """Feature queries and writes share the dispatcher's atomic authority."""
        return getattr(self, '_ledger', None) or self.dispatcher.ledger

    @classmethod
    def read_only(cls, dispatcher, run_id):
        """Open an existing feature without schema creation or write authority."""
        authority = cls.__new__(cls)
        authority.dispatcher = dispatcher
        authority.run_id = identifier(run_id)
        authority._ledger = SQLiteLedger(dispatcher.path, read_only=True, timeout=2)
        with authority.ledger.transaction() as db:
            authority.ledger.read_run(db, authority.run_id)
        return authority

    def _require_writable(self):
        if getattr(self.ledger, 'read_only', False):
            raise ValueError('Read-only feature authority cannot mutate state')

    def _load(self, db):
        row = db.execute('SELECT state FROM features WHERE run=?', (self.run_id,)).fetchone()
        if row is None:
            raise ValueError('Feature passport missing')
        return json.loads(row['state'])

    def _save(self, db, state):
        state = _bounded(state)
        db.execute('UPDATE features SET state=? WHERE run=?', (canonical(state), self.run_id))

    def _passport(self, passport, db):
        (_, manifest) = self.ledger.read_run(db, self.run_id)
        tasks = {
            row['id']: json.loads(row['packet']) for row in self.ledger.read_tasks(db, self.run_id)
        }
        return validate_passport(passport, manifest=manifest, tasks=tasks)

    def create(self, passport):
        self._require_writable()
        with self.ledger.transaction() as db:
            p = self._passport(passport, db)
            row = db.execute('SELECT state FROM features WHERE run=?', (self.run_id,)).fetchone()
            if row:
                if json.loads(row['state'])['passport'] != p:
                    raise ValueError('Feature already bound to another passport')
            else:
                if any(row['attempt'] > 0 for row in self.ledger.read_tasks(db, self.run_id)):
                    raise ValueError('Freeze feature passport before execution')
                state = {
                    'passport': p,
                    'passport_sha256': digest(p),
                    'revisions': [],
                    'compositions': {},
                    'current_composition': None,
                    'checks': {},
                    'releases': {},
                    'stage': FeatureState.DRAFT.value
                }
                db.execute('INSERT INTO features VALUES(?,?)', (self.run_id, canonical(state)))
        return self.report()

    def update_passport(self, passport, *, approvals, task_contracts=None):
        self._require_writable()
        with self.ledger.transaction() as db:
            state = self._load(db)
            old = state['passport']
            p = self._passport(passport, db)
            if p == old:
                return self.report_from(db, state)
            if (
                p['feature_id'] != old['feature_id']
                or p['plan_revision'] <= old['plan_revision']
                or p['spec_revision'] < old['spec_revision']
            ):
                raise ValueError('Feature revision must advance')
            if (
                any(
                    (
                        op['state'] in {'releasing', 'observing', TaskState.UNKNOWN.value} for op in state['releases'].values()
                    )
                )
            ):
                raise ValueError('Cannot revise active release')
            if (
                any(
                    (
                        row['state'] in {
                            TaskState.RUNNING.value,
                            TaskState.SUBMITTED.value,
                            TaskState.UNKNOWN.value,
                            TaskState.CANCEL_REQUESTED.value,
                            TaskState.HANDOFF_PENDING.value
                        } for row in self.ledger.read_tasks(db, self.run_id)
                    )
                )
            ):
                raise ValueError('Stop and reconcile active work before revising contracts')
            affected = {old['coordinator'], p['coordinator']}
            before = {c['contract_id']: c for c in old['contracts']}
            after = {c['contract_id']: c for c in p['contracts']}
            for key in set(before) | set(after):
                if before.get(key) != after.get(key):
                    affected.update(before.get(key, {}).get('owners', []))
                    affected.update(after.get(key, {}).get('owners', []))
                    if (
                        key in before
                        and key in after
                        and (after[key]['revision'] <= before[key]['revision'])
                    ):
                        raise ValueError('Changed contract must advance revision')
            for (field, key) in (('services', 'service_id'), ('business_invariants', 'invariant_id')):
                old_items = {item[key]: item for item in old[field]}
                new_items = {item[key]: item for item in p[field]}
                for item_id in set(old_items) | set(new_items):
                    if old_items.get(item_id) != new_items.get(item_id):
                        affected.update(
                            (
                                item['owner'] for item in (old_items.get(item_id), new_items.get(item_id)) if item
                            )
                        )
            if old['acceptance_protocol'] != p['acceptance_protocol']:
                affected.update(
                    (
                        c['owner'] for c in old['acceptance_protocol']['checks'] + p['acceptance_protocol']['checks']
                    )
                )
            if old['release_plan'] != p['release_plan']:
                affected.update(
                    (
                        step['owner'] for step in old['release_plan']['steps'] + p['release_plan']['steps']
                    )
                )
            if type(approvals) is not list or not affected <= set(approvals):
                raise ValueError('Affected boundary owner approval required')
            if len(state['revisions']) >= 64:
                raise ValueError('Revision bound reached')
            previous_packets = {}
            if task_contracts is not None:
                previous_packets = self.ledger.update_task_contracts(db, self.run_id, task_contracts)
            state['revisions'].append(
                {
                    'passport': old,
                    'passport_sha256': state['passport_sha256'],
                    'previous_task_packets': previous_packets
                }
            )
            state.update(
                passport=p,
                passport_sha256=digest(p),
                current_composition=None,
                stage='draft'
            )
            self._save(db, state)
        return self.report()

    def compose(
        self,
        components,
        *,
        test_suite_sha256,
        environment_sha256,
        flags_sha256=None,
        data_sha256=None
    ):
        self._require_writable()
        with self.ledger.transaction() as db:
            state = self._load(db)
            p = state['passport']
            components = _bounded(components)
            if set(components) != {s['service_id'] for s in p['services']}:
                raise ValueError('Composition must include every service')
            for component in components.values():
                if (
                    type(component) is not dict
                    or set(component) - {'commit', 'image_digest', 'migration', 'flags_sha256'}
                    or 'commit' not in component
                ):
                    raise ValueError('Invalid component identity')
                _pin(component['commit'], True)
                for key in ('image_digest', 'flags_sha256'):
                    if key in component:
                        _pin(component[key])
                if 'migration' in component:
                    text(component['migration'], 'migration', 256)
            for value in (test_suite_sha256, environment_sha256):
                _pin(value)
            for value in (flags_sha256, data_sha256):
                if value is not None:
                    _pin(value)
            previous = state['compositions'].get(state['current_composition'])
            comparison = {
                'components': components,
                'test_suite_sha256': test_suite_sha256,
                'environment_sha256': environment_sha256,
                'flags_sha256': flags_sha256,
                'data_sha256': data_sha256
            }
            if (
                previous
                and previous['passport_sha256'] == state['passport_sha256']
                and all(previous[k] == v for (k, v) in comparison.items())
            ):
                return dict(previous, composition_id=state['current_composition'])
            composition = {
                'composition_revision': len(state['compositions']) + 1,
                'feature_id': p['feature_id'],
                'run_id': self.run_id,
                'spec_revision': p['spec_revision'],
                'plan_revision': p['plan_revision'],
                'passport_sha256': state['passport_sha256'],
                'components': components,
                'test_suite_sha256': test_suite_sha256,
                'environment_sha256': environment_sha256,
                'flags_sha256': flags_sha256,
                'data_sha256': data_sha256
            }
            key = digest(composition)
            if len(state['compositions']) >= 128 and key not in state['compositions']:
                raise ValueError('Composition bound reached')
            if (
                any(
                    (
                        op['state'] in {'releasing', 'observing', TaskState.UNKNOWN.value} for op in state['releases'].values()
                    )
                ) and state['current_composition'] != key
            ):
                raise ValueError('Active release composition immutable')
            state['compositions'][key] = composition
            state['current_composition'] = key
            state['stage'] = FeatureState.INTEGRATING.value
            self._save(db, state)
            return dict(composition, composition_id=key)

    def link_pr(
        self,
        repository_id,
        platform,
        number,
        commit,
        state='unknown',
        evidence_sha256=None
    ):
        """Keep historical platform observations; never fetch, publish or approve."""
        self._require_writable()
        identifier(repository_id)
        integer(number, 'pull request number', 1)
        _pin(commit, True)
        if (
            platform not in {'github', 'gitlab'}
            or state not in {'unknown', 'open', 'closed', 'merged'}
        ):
            raise ValueError('Invalid pull request reference')
        if evidence_sha256 is not None:
            _pin(evidence_sha256)
        if state != 'unknown' and evidence_sha256 is None:
            raise ValueError('Known platform observation requires pinned evidence')
        item = dict(
            repository_id=repository_id,
            platform=platform,
            number=number,
            commit=commit,
            state=state,
            evidence_sha256=evidence_sha256
        )
        with self.ledger.transaction() as db:
            snapshot = self._load(db)
            if (
                repository_id not in {r['repository_id'] for r in snapshot['passport']['repositories']}
            ):
                raise ValueError('Unknown feature repository')
            history = snapshot.setdefault('pull_requests', [])
            if item not in history:
                if len(history) >= 128:
                    raise ValueError('Pull request history bound reached')
                history.append(item)
                self._save(db, snapshot)
            return self.report_from(db, snapshot)

    def _composition(self, state, key):
        _pin(key)
        composition = state['compositions'].get(key)
        if (
            composition is None
            or state['current_composition'] != key
            or composition['passport_sha256'] != state['passport_sha256']
        ):
            raise ValueError('Stale feature composition')
        return composition

    def _root_slot(self, db, task_id, subject, *, require_verified=True):
        row = self.ledger.read_task(db, self.run_id, task_id)
        if row is None:
            raise ValueError('Unknown root slot')
        packet = json.loads(row['packet'])
        receipt = json.loads(row['receipt']) if row['receipt'] else {}
        if (
            packet.get('dispatch_mode') != 'external' or (
                require_verified and (
                    row['state'] != TaskState.VERIFIED.value
                    or receipt.get('subject') != subject
                    or (not row['usage_known'])
                )
            )
        ):
            raise ValueError('Exact independently verified root slot required')
        return row

    def record_check(self, composition_id, check_id, receipt, *, verifier):
        self._require_writable()
        receipt = _bounded(receipt)
        with self.ledger.transaction() as db:
            state = self._load(db)
            self._composition(state, composition_id)
            check = next(
                (
                    c for c in state['passport']['acceptance_protocol']['checks'] if c['check_id'] == check_id
                ),
                None
            )
            if check is None:
                raise ValueError('Unknown frozen check')
            slot = receipt.get('task_id', check['task_id'])
            if slot not in [check['task_id'], *check.get('repair_task_ids', [])]:
                raise ValueError('Check slot not frozen')
            self._root_slot(db, slot, composition_id)
        proof = _bounded(verifier(_bounded(check), _bounded(receipt)))
        if (
            type(proof) is not dict
            or proof.get('independent') is not True
            or proof.get('subject') != composition_id
            or (proof.get('verdict') not in _VERDICTS)
            or (proof.get('criteria_sha256') != check['criteria_sha256'])
        ):
            raise ValueError('Independent frozen-check verdict required')
        identifier(proof.get('verifier_id'))
        _pin(proof.get('evidence_sha256'))
        if proof['verifier_id'] == check['owner']:
            raise ValueError('Check owner cannot independently verify own work')
        evidence = {
            k: proof[k] for k in (
                'independent',
                'subject',
                'verdict',
                'criteria_sha256',
                'verifier_id',
                'evidence_sha256'
            )
        }
        evidence['task_id'] = slot
        with self.ledger.transaction() as db:
            state = self._load(db)
            self._composition(state, composition_id)
            self._root_slot(db, slot, composition_id)
            key = composition_id + ':' + check_id
            if key in state['checks'] and state['checks'][key] != evidence:
                raise ValueError('Check receipt immutable; use new composition/slot')
            state['checks'][key] = evidence
            state['stage'] = FeatureState.VERIFYING.value
            self._save(db, state)
        return self.report()

    def _authorization(self, p, composition_id, environment, authorization, owner=None):
        if (
            type(authorization) is not dict
            or set(authorization) != {'confirmed', 'actor', 'environment', 'composition_id'}
            or authorization.get('confirmed') is not True
            or (authorization.get('actor') not in ({owner} if owner else set(p['owners'])))
            or (authorization.get('environment') != environment)
            or (authorization.get('composition_id') != composition_id)
        ):
            raise ValueError('Explicit exact environment authorization required')

    def begin_release(
        self,
        composition_id,
        environment,
        *,
        authorization,
        observed_versions,
        observed_state_sha256
    ):
        self._require_writable()
        with self.ledger.transaction() as db:
            state = self._load(db)
            composition = self._composition(state, composition_id)
            p = state['passport']
            self._authorization(p, composition_id, environment, authorization, p['coordinator'])
            key = digest({'composition_id': composition_id, 'environment': environment})
            if key in state['releases']:
                return state['releases'][key]
            if self.report_from(db, state)['status'] != 'release_ready':
                raise ValueError('Feature not release ready')
            release = p['release_plan']
            if (
                environment != release['environment']
                or observed_state_sha256 != release['initial_state_sha256']
                or observed_versions != release['initial_versions']
                or (
                    release['steps'][-1]['versions'] != {k: v['commit'] for (k, v) in composition['components'].items()}
                )
            ):
                raise ValueError('Release environment/version drift')
            key = digest({'composition_id': composition_id, 'environment': environment})
            if key not in state['releases']:
                state['releases'][key] = {
                    'operation_id': key,
                    'composition_id': composition_id,
                    'environment': environment,
                    'state': 'releasing',
                    'versions': observed_versions,
                    'state_sha256': observed_state_sha256,
                    'steps': {},
                    'observation_started': None
                }
                state['stage'] = FeatureState.RELEASING.value
                self._save(db, state)
            return state['releases'][key]

    # Persist intent before admission. An interrupted intent is unknown and must
    # be reconciled; a retry never grants permission for a second process.
    def begin_step(
        self,
        operation_id,
        step_id,
        *,
        authorization,
        observed_versions,
        observed_state_sha256
    ):
        self._require_writable()
        with self.ledger.transaction() as db:
            state = self._load(db)
            op = state['releases'].get(operation_id)
            if op is None:
                raise ValueError('Unknown release')
            self._composition(state, op['composition_id'])
            p = state['passport']
            steps = p['release_plan']['steps']
            step = next((s for s in steps if s['step_id'] == step_id), None)
            if step is None:
                raise ValueError('Unknown release step')
            self._authorization(p, op['composition_id'], op['environment'], authorization, step['owner'])
            if step_id in op['steps']:
                return dict(op['steps'][step_id], launch_allowed=False)
            if self.report_from(db, state)['blockers']:
                raise ValueError('Root authority blocks release step')
            index = steps.index(step)
            if (
                op['state'] != 'releasing'
                or observed_state_sha256 != op['state_sha256']
                or observed_versions != op['versions']
                or any(
                    (
                        op['steps'].get(s['step_id'], {}).get('state') != 'completed' for s in steps[:index]
                    )
                )
            ):
                raise ValueError('Release ordering/version drift')
            op['steps'][step_id] = {
                'state': 'unknown',
                'task_id': step['task_id'],
                'attempt_id': None,
                'subject': op['composition_id'],
                'versions': step['versions'],
                'state_sha256': step['state_sha256']
            }
            self._save(db, state)
        task = self.dispatcher.claim_task(self.run_id, step['task_id'])
        with self.ledger.transaction() as db:
            state = self._load(db)
            entry = state['releases'][operation_id]['steps'][step_id]
            if task is None:
                entry['state'] = 'blocked'
                self._save(db, state)
                return dict(entry, launch_allowed=False)
            (run, _) = self.ledger.read_run(db, self.run_id)
            row = self.ledger.read_task(db, self.run_id, step['task_id'])
            report = self.report_from(db, state)
            unsafe = set(report['blockers']) - {'root_work_active'}
            other_active = any(
                (
                    t['task_id'] != step['task_id']
                    and t['state'] in {TaskState.RUNNING.value, TaskState.SUBMITTED.value} for t in report['tasks']
                )
            )
            if (
                unsafe
                or other_active
                or run['cancel']
                or (row['state'] != TaskState.RUNNING.value)
                or (row['attempt'] != task['attempt_id'])
            ):
                entry.update(state='unknown', attempt_id=task['attempt_id'])
                state['releases'][operation_id]['state'] = 'unknown'
                self._save(db, state)
                return dict(entry, launch_allowed=False)
            entry.update(state='running', attempt_id=task['attempt_id'])
            self._save(db, state)
            return dict(entry, launch_allowed=True, task=task)

    def finish_step(self, operation_id, step_id, receipt, *, verifier):
        self._require_writable()
        receipt = _bounded(receipt)
        with self.ledger.transaction() as db:
            state = self._load(db)
            op = state['releases'].get(operation_id)
            if op is None or step_id not in op['steps']:
                raise ValueError('Unknown release intent')
            entry = op['steps'][step_id]
            if entry['state'] == 'completed':
                return dict(entry)
            step = next(
                (
                    s for s in state['passport']['release_plan']['steps'] if s['step_id'] == step_id
                )
            )
        proof = _bounded(verifier(_bounded(step), _bounded(receipt)))
        if (
            type(proof) is not dict
            or proof.get('independent') is not True
            or proof.get('subject') != op['composition_id']
        ):
            raise ValueError('Independent release outcome required')
        _pin(proof.get('evidence_sha256'))
        with self.ledger.transaction() as db:
            state = self._load(db)
            op = state['releases'][operation_id]
            self._composition(state, op['composition_id'])
            entry = op['steps'][step_id]
            row = self._root_slot(db, step['task_id'], op['composition_id'], require_verified=False)
            (run, _) = self.ledger.read_run(db, self.run_id)
            if run['cancel']:
                entry['state'] = 'cancelled' if row['usage_known'] and row['state'] not in {
                    TaskState.RUNNING.value,
                    TaskState.SUBMITTED.value,
                    TaskState.UNKNOWN.value,
                    TaskState.CANCEL_REQUESTED.value
                } else 'unknown'
                op['state'] = entry['state']
            elif (
                entry['attempt_id'] != row['attempt'] or row['state'] in {
                    TaskState.RUNNING.value,
                    TaskState.SUBMITTED.value,
                    TaskState.UNKNOWN.value,
                    TaskState.CANCEL_REQUESTED.value
                } or (not row['usage_known'])
            ):
                entry['state'] = 'unknown'
                op['state'] = 'unknown'
            elif (
                proof.get('verdict') == 'PASS'
                and proof.get('versions') == step['versions']
                and (proof.get('state_sha256') == step['state_sha256'])
                and (row['state'] == TaskState.VERIFIED.value)
                and (json.loads(row['receipt'])['subject'] == op['composition_id'])
            ):
                entry.update(state='completed', evidence_sha256=proof['evidence_sha256'])
                op['versions'] = step['versions']
                op['state_sha256'] = step['state_sha256']
                op['state'] = 'releasing'
                if (
                    all(
                        (
                            op['steps'].get(s['step_id'], {}).get('state') == 'completed' for s in state['passport']['release_plan']['steps']
                        )
                    )
                ):
                    op.update(state='observing', observation_started=time.time())
            else:
                entry['state'] = 'failed'
                op['state'] = 'failed'
            state['stage'] = op['state']
            self._save(db, state)
            return dict(entry)

    def reconcile_step(self, operation_id, step_id, receipt, *, verifier):
        """Close an orphan intent after root reconciliation; never resumes action.

        Successful work needs a new explicitly authorized plan/slot after an unknown
        process was reconciled failed. Reconciliation is not deployment acceptance.
        """
        self._require_writable()
        receipt = _bounded(receipt)
        with self.ledger.transaction() as db:
            state = self._load(db)
            op = state['releases'].get(operation_id)
            if op is None or step_id not in op['steps']:
                raise ValueError('Unknown release intent')
            entry = op['steps'][step_id]
            step = next(
                (
                    s for s in state['passport']['release_plan']['steps'] if s['step_id'] == step_id
                )
            )
        proof = _bounded(verifier(_bounded(step), _bounded(receipt)))
        if (
            type(proof) is not dict
            or proof.get('independent') is not True
            or proof.get('subject') != op['composition_id']
            or (proof.get('stopped') is not True)
        ):
            raise ValueError('Independent stopped reconciliation proof required')
        _pin(proof.get('evidence_sha256'))
        with self.ledger.transaction() as db:
            state = self._load(db)
            op = state['releases'][operation_id]
            entry = op['steps'][step_id]
            row = self._root_slot(db, step['task_id'], op['composition_id'], require_verified=False)
            if (
                row['state'] in {
                    TaskState.RUNNING.value,
                    TaskState.SUBMITTED.value,
                    TaskState.UNKNOWN.value,
                    TaskState.CANCEL_REQUESTED.value
                } or not row['usage_known']
            ):
                raise ValueError('Reconcile root outcome and usage first')
            if row['attempt'] == 0 and proof.get('not_started') is not True:
                raise ValueError('Unstarted intent needs no-launch proof')
            if entry['state'] == 'completed':
                return dict(entry)
            (run, _) = self.ledger.read_run(db, self.run_id)
            entry.update(
                state='cancelled' if run['cancel'] else 'failed',
                attempt_id=row['attempt'],
                evidence_sha256=proof['evidence_sha256']
            )
            op['state'] = entry['state']
            state['stage'] = op['state']
            self._save(db, state)
            return dict(entry)

    def observe(self, operation_id, receipt, *, verifier):
        self._require_writable()
        receipt = _bounded(receipt)
        with self.ledger.transaction() as db:
            state = self._load(db)
            op = state['releases'].get(operation_id)
            if op is None or op['state'] not in {'observing', 'accepted'}:
                raise ValueError('Release not observing')
            self._composition(state, op['composition_id'])
            plan = state['passport']['release_plan']
        proof = _bounded(verifier(_bounded(plan), _bounded(receipt)))
        if (
            type(proof) is not dict
            or proof.get('independent') is not True
            or proof.get('subject') != op['composition_id']
            or (proof.get('versions') != op['versions'])
            or (proof.get('state_sha256') != op['state_sha256'])
        ):
            raise ValueError('Independent observation proof required')
        _pin(proof.get('evidence_sha256'))
        seconds = proof.get('observed_seconds')
        metrics = proof.get('metrics', {})
        if (
            type(seconds) not in (int, float)
            or not math.isfinite(seconds)
            or seconds < plan['observation_seconds']
            or (time.time() - op['observation_started'] < plan['observation_seconds'])
        ):
            raise ValueError('Observation window incomplete')
        passed = proof.get('verdict') == 'PASS'
        for threshold in plan['thresholds']:
            value = metrics.get(threshold['metric'])
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('Observed numeric metric missing')
            passed = passed and threshold.get('min', -math.inf) <= value <= threshold.get('max', math.inf)
        with self.ledger.transaction() as db:
            state = self._load(db)
            op = state['releases'][operation_id]
            self._composition(state, op['composition_id'])
            report = self.report_from(db, state)
            if report['blockers']:
                raise ValueError('Root authority blocks observation acceptance')
            observation = {
                'evidence_sha256': proof['evidence_sha256'],
                'metrics': metrics,
                'observed_seconds': seconds,
                'state_sha256': proof['state_sha256']
            }
            if 'observation' in op:
                if op['observation'] != observation:
                    raise ValueError('Observation receipt immutable')
                return self.report_from(db, state)
            op.update(state='accepted' if passed else 'failed', observation=observation)
            state['stage'] = op['state']
            self._save(db, state)
        return self.report()

    def _check_reports(self, db, state, composition, composition_id):
        checks = []
        for check in state['passport']['acceptance_protocol']['checks']:
            proof = None
            if composition and composition['passport_sha256'] == state['passport_sha256']:
                proof = state['checks'].get(str(composition_id) + ':' + check['check_id'])
            if proof:
                try:
                    self._root_slot(db, proof['task_id'], composition_id)
                except ValueError:
                    proof = None
            pins = {
                key: proof[key]
                for key in ('subject', 'criteria_sha256', 'verifier_id', 'evidence_sha256')
            } if proof else {}
            checks.append(dict(
                check,
                verdict=proof['verdict'] if proof else CheckVerdict.NOT_RUN.value,
                evidence=proof,
                **pins,
            ))
        return checks

    def _report_blockers(self, db, passport, composition, checks, rows, run):
        blockers = []
        if any(not item['resolved'] for item in passport['business_invariants']):
            blockers.append('unresolved_business_invariants')
        if not composition:
            blockers.append('composition_missing')
        if any(check['verdict'] != CheckVerdict.PASS.value for check in checks):
            blockers.append('acceptance_incomplete')
        if any(row['state'] in {TaskState.UNKNOWN.value, TaskState.CANCEL_REQUESTED.value}
               or not row['usage_known'] for row in rows):
            blockers.append('root_outcome_unknown')
        if any(row['state'] in {TaskState.RUNNING.value, TaskState.SUBMITTED.value}
               for row in rows):
            blockers.append('root_work_active')
        if run['cancel']:
            blockers.append('root_cancelled')
        if any(row['state'] == TaskState.FAILED.value for row in rows):
            blockers.append('root_task_failed')
        implementation = [
            row for row in rows
            if json.loads(row['packet']).get('dispatch_mode', 'auto') == 'auto'
        ]
        if any(row['state'] != TaskState.VERIFIED.value for row in implementation):
            blockers.append('implementation_incomplete')
        if any(not admission_allowed(db, self.run_id, json.loads(row['packet']))
               for row in implementation):
            blockers.append('contract_task_pins_stale')
        if composition:
            versions = {key: value['commit'] for key, value in composition['components'].items()}
            if passport['release_plan']['steps'][-1]['versions'] != versions:
                blockers.append('release_final_matrix_mismatch')
        return blockers, implementation

    @staticmethod
    def _report_status(state, current, checks, blockers, composition, implementation, rows):
        status = state['stage']
        unfinished = {TaskState.RUNNING.value, TaskState.UNKNOWN.value, TaskState.CANCEL_REQUESTED.value}
        cancellation = (
            FeatureState.CANCEL_REQUESTED.value
            if any(row['state'] in unfinished for row in rows)
            else FeatureState.CANCELLED.value
        )
        if current:
            status = current[-1]['state']
        elif not blockers:
            status = FeatureState.RELEASE_READY.value
        elif any(check['verdict'] == CheckVerdict.FAIL.value for check in checks):
            status = FeatureState.FAILED.value
        elif 'root_outcome_unknown' in blockers:
            status = FeatureState.UNKNOWN.value
        elif 'root_cancelled' in blockers:
            status = cancellation
        elif ('unresolved_business_invariants' in blockers
              or 'contract_task_pins_stale' in blockers):
            status = FeatureState.BLOCKED.value
        elif not composition:
            status = (
                FeatureState.IMPLEMENTING.value
                if any(row['attempt'] for row in implementation)
                else FeatureState.CONTRACTS_READY.value
            )
        else:
            status = (
                FeatureState.VERIFYING.value
                if any(check['verdict'] != CheckVerdict.NOT_RUN.value for check in checks)
                else FeatureState.INTEGRATING.value
            )
        # Global liabilities fence every phase, even a previously accepted release.
        if 'root_task_failed' in blockers:
            status = FeatureState.FAILED.value
        if 'root_outcome_unknown' in blockers:
            status = FeatureState.UNKNOWN.value
        if 'root_cancelled' in blockers:
            status = cancellation
        return status

    def report_from(self, db, state):
        run, manifest = self.ledger.read_run(db, self.run_id)
        rows = self.ledger.read_tasks(db, self.run_id)
        passport = state['passport']
        key = state['current_composition']
        composition = state['compositions'].get(key)
        checks = self._check_reports(db, state, composition, key)
        blockers, implementation = self._report_blockers(
            db, passport, composition, checks, rows, run)
        releases = list(state['releases'].values())
        current = [operation for operation in releases if operation['composition_id'] == key]
        status = self._report_status(
            state, current, checks, blockers, composition, implementation, rows)
        repo_commits = {}
        if composition:
            for service in passport['services']:
                commit = composition['components'][service['service_id']]['commit']
                repo_commits.setdefault(service['repository_id'], set()).add(commit)
        pull_requests = [
            dict(item, current=item['commit'] in repo_commits.get(item['repository_id'], set()))
            for item in state.get('pull_requests', [])
        ]
        steps = [
            dict(step, status=(
                current[-1]['steps'].get(step['step_id'], {}).get('state', 'pending')
                if current else 'pending'
            ))
            for step in passport['release_plan']['steps']
        ]
        return {
            'feature_id': passport['feature_id'],
            'run_id': self.run_id,
            'backend': run['backend'],
            'status': status,
            'spec_revision': passport['spec_revision'],
            'plan_revision': passport['plan_revision'],
            'passport_sha256': state['passport_sha256'],
            'passport': passport,
            'composition_id': key,
            'composition': dict(composition, composition_id=key) if composition else None,
            'checks': checks,
            'blockers': blockers,
            'plan_sha256': run['digest'],
            'budget': manifest['budget'],
            'repositories': passport['repositories'],
            'services': passport['services'],
            'contracts': passport['contracts'],
            'release': current[-1] if current else None,
            'release_ready': status == FeatureState.RELEASE_READY.value,
            'accepted': status == FeatureState.ACCEPTED.value,
            'human_actions': blockers,
            'steps': steps,
            'releases': releases,
            'revisions': state['revisions'],
            'usage': {
                'tokens': sum(row['tokens'] for row in rows),
                'cost_micros': sum(row['cost'] for row in rows),
                'reserved_tokens': sum(row['reserve_tokens'] for row in rows),
                'reserved_cost_micros': sum(row['reserve_cost'] for row in rows),
                'known': all(row['usage_known'] for row in rows),
            },
            'pull_requests': pull_requests,
            'tasks': [self.ledger.project_task(row) for row in rows],
        }

    def report(self):
        with self.ledger.transaction() as db:
            return self.report_from(db, self._load(db))

    def export_progress(self, plan_path):
        self._require_writable()
        path = Path(plan_path).absolute()
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('Source plan links forbidden')
        if not path.is_file() or path.stat().st_size > 1024 * 1024:
            raise ValueError('Bounded existing source plan required')
        report = self.report()
        begin = '<!-- palarran-feature-progress:start -->'
        end = '<!-- palarran-feature-progress:end -->'
        text = path.read_text()
        section = begin + '\n```json\n' + json.dumps(report, indent=2, sort_keys=True) + '\n```\n' + end
        if text.count(begin) != text.count(end) or text.count(begin) > 1:
            raise ValueError('Ambiguous source progress markers')
        if begin in text:
            start = text.index(begin)
            stop = text.index(end, start) + len(end)
            text = text[:start] + section + text[stop:]
        else:
            text = text.rstrip() + '\n\n' + section + '\n'
        path.write_text(text)
        return report
