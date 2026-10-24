"""Independently frozen cross-repository feature regressions; no paid calls."""
import copy
from pathlib import Path
import tempfile
import threading
import unittest

from packages.core.parallelism.dispatcher import Dispatcher, validate
from test_parallel_dispatcher import FakeAdapter, manifest, verify


def multi_repository_manifest(root, *, workers=2):
    value, _ = feature_fixture(root)
    value['max_workers'] = workers
    return value


class CrossRepositoryDispatcherRegressions(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.dispatcher = Dispatcher(self.root / 'private/root.sqlite3')

    def tearDown(self):
        self.temporary.cleanup()

    def create(self, value):
        from packages.core.parallelism.feature import FeatureAuthority
        self.dispatcher.create_run(value)
        _, passport = feature_fixture(self.root)
        passport.update(repositories=copy.deepcopy(value['repositories']),
                        budget=copy.deepcopy(value['budget']),
                        task_graph=[task['task_id'] for task in value['tasks']])
        FeatureAuthority(self.dispatcher, value['run_id']).create(passport)

    def test_same_relative_file_in_different_repositories_really_overlaps(self):
        value = multi_repository_manifest(self.root)
        self.create(value)
        adapter = FakeAdapter(delay=0.04)
        report = self.dispatcher.run_local(value['run_id'], adapter, verify)
        self.assertEqual(adapter.peak, 2)
        self.assertTrue(all(task['state'] == 'verified' for task in report['tasks'][:2]))
        self.assertEqual(report['usage']['tokens'], 20)

    def test_same_repository_file_stays_exclusive(self):
        value = multi_repository_manifest(self.root)
        value['tasks'][1].update(repository_id='auth', base_commit='a' * 40)
        self.create(value)
        adapter = FakeAdapter(delay=0.03)
        self.dispatcher.run_local(value['run_id'], adapter, verify)
        self.assertEqual(adapter.peak, 1)
        self.assertEqual(len(adapter.calls), 2)

    def test_child_cannot_move_to_other_repository_or_reset_budget(self):
        value = multi_repository_manifest(self.root)
        child = copy.deepcopy(value['tasks'][0])
        child.update(task_id='child', parent_task_id='task-0',
                     repository_id='ledger', base_commit='b' * 40)
        value['tasks'].append(child)
        with self.assertRaises(ValueError):
            validate(value)
        value['tasks'][-1].update(repository_id='auth', base_commit='a' * 40,
                                 limits=dict(tokens=101, cost_micros=100, seconds=5))
        with self.assertRaises(ValueError):
            validate(value)

    def test_task_cannot_use_unlisted_repository_or_wrong_commit_or_file_scope(self):
        for change in ({'repository_id': 'unknown'}, {'base_commit': 'c' * 40},
                       {'files': ['outside']}):
            with self.subTest(change=change):
                value = multi_repository_manifest(self.root)
                value['tasks'][0].update(change)
                with self.assertRaises(ValueError):
                    validate(value)

    def test_shared_root_unknown_survives_restart_and_blocks_second_repository(self):
        value = multi_repository_manifest(self.root)
        value['budget'].update(tokens=450, integration_tokens=100, verification_tokens=100, handoff_tokens=100)
        self.create(value)
        adapter = FakeAdapter(receipt=dict(status='unknown', tokens=10,
            cost_micros=10, usage_known=False, stopped=False))
        self.dispatcher.execute_task(value['run_id'], 'task-0', adapter, verify)
        restarted = Dispatcher(self.root / 'private/root.sqlite3')
        restarted.execute_task(value['run_id'], 'task-0', adapter, verify)
        restarted.execute_task(value['run_id'], 'task-1', adapter, verify)
        report = restarted.get_run(value['run_id'])
        self.assertEqual(adapter.calls, [('task-0', 1)])
        self.assertEqual(report['status'], 'unknown')
        self.assertEqual(report['usage']['tokens'], 10)
        self.assertEqual(report['usage']['reserved_tokens'], 90)
        self.assertFalse(report['usage']['known'])

    def test_cancel_unknown_keeps_observed_spend_and_liability(self):
        value = multi_repository_manifest(self.root)
        self.create(value)
        adapter = FakeAdapter(receipt=dict(status='unknown', tokens=13,
            cost_micros=17, usage_known=False, stopped=False))
        self.dispatcher.execute_task(value['run_id'], 'task-0', adapter, verify)
        before = self.dispatcher.get_run(value['run_id'])
        self.dispatcher.cancel(value['run_id'])
        report = Dispatcher(self.root / 'private/root.sqlite3').get_run(value['run_id'])
        self.assertEqual(report['usage'], before['usage'])
        self.assertFalse(report['usage']['known'])
        self.assertGreater(report['usage']['reserved_tokens'], 0)

    def test_registered_descendant_spends_original_root_ledger(self):
        value = multi_repository_manifest(self.root)
        self.create(value)
        parent = self.dispatcher.claim_task(value['run_id'], 'task-0')
        child = copy.deepcopy(value['tasks'][0])
        child_root = self.root / 'child-worktree'
        child_root.mkdir()
        child.update(task_id='child', parent_task_id='task-0', files=['src/child'],
                     worktree=str(child_root), owner='child-owner')
        self.dispatcher.add_tasks(value['run_id'], 'task-0', [child])
        self.dispatcher.finish_task(value['run_id'], 'task-0', parent['attempt_id'],
            dict(status='submitted', subject='parent-output', tokens=7, cost_micros=11,
                 usage_known=True, stopped=True), verify)
        adapter = FakeAdapter()
        report = self.dispatcher.run_local(value['run_id'], adapter, verify)
        self.assertEqual(set(task for task, _ in adapter.calls), {'task-1', 'child'})
        self.assertEqual(report['usage']['tokens'], 27)
        self.assertEqual(report['usage']['cost_micros'], 31)
        self.assertEqual(report['budget'], value['budget'])


def feature_fixture(root):
    value = manifest(root, count=9)
    value['budget'].update(tokens=10000, cost_micros=10000,
        integration_tokens=1000, verification_tokens=1000, handoff_tokens=100)
    value['repositories'] = [dict(repository_id=repo, default_branch='main',
        base_commit=commit, files=['src'], owner=owner)
        for repo, commit, owner in (('auth', 'a' * 40, 'owner-auth'),
                                    ('ledger', 'b' * 40, 'owner-ledger'))]
    contract = dict(contract_id='referral', revision=1, producer='auth',
        consumers=['ledger'], owners=['owner-auth', 'owner-ledger'],
        schema_sha256='1' * 64, semantics_sha256='2' * 64)
    pins = {'referral': {k: contract[k] for k in ('revision', 'schema_sha256', 'semantics_sha256')}}
    for index, task in enumerate(value['tasks']):
        repo = value['repositories'][index % 2]
        task.update(repository_id=repo['repository_id'], base_commit=repo['base_commit'],
                    files=['src'], contracts=copy.deepcopy(pins))
        if index >= 2:
            task.update(dispatch_mode='external', budget_phase='verification' if index < 6 else 'integration',
                        depends_on=['task-0', 'task-1'])
    value['tasks'][8].update(required_for_completion=False, files=[])
    initial = {'auth': 'a' * 40, 'ledger': 'b' * 40}
    intermediate = {'auth': 'c' * 40, 'ledger': 'b' * 40}
    final = {'auth': 'c' * 40, 'ledger': 'd' * 40}
    passport = dict(feature_id='referral', spec_revision=1, plan_revision=1,
        coordinator='coordinator', repositories=copy.deepcopy(value['repositories']),
        services=[dict(service_id=repo['repository_id'], repository_id=repo['repository_id'], owner=repo['owner'])
                  for repo in value['repositories']],
        owners=['coordinator', 'owner-auth', 'owner-ledger'], contracts=[contract],
        business_invariants=[dict(invariant_id='no-double-credit', owner='owner-ledger',
                                 check_id='business', resolved=True)],
        task_graph=[task['task_id'] for task in value['tasks']], budget=copy.deepcopy(value['budget']),
        acceptance_protocol={'checks': [dict(check_id=kind, kind=kind,
            owner='owner-auth', task_id='task-' + str(index + 2), criteria_sha256=str(index + 3) * 64)
            for index, kind in enumerate(('local', 'contract', 'business', 'transition'))]},
        release_plan=dict(environment='staging', initial_versions=initial,
            allowed_matrices=[initial, intermediate, final], observation_seconds=1,
            thresholds=[dict(metric='error-rate', max=0.01)], steps=[
                dict(step_id='auth-deploy', owner='owner-auth', task_id='task-6',
                     versions=intermediate, kind='deploy', recovery='rollback auth', irreversible=False),
                dict(step_id='ledger-deploy', owner='owner-ledger', task_id='task-7',
                     versions=final, kind='deploy', recovery='rollback ledger', irreversible=False)]))
    release = passport['release_plan']
    release['initial_state_sha256'] = 'a' * 64
    release['allowed_states'] = [dict(versions=versions, state_sha256=state * 64)
        for versions, state in ((initial, 'a'), (intermediate, 'b'), (final, 'c'))]
    for step, state in zip(release['steps'], ('b', 'c')):
        step.update(state_sha256=state * 64,
                    reversibility=dict(code=True, schema=True, data=True, external=True))
    return value, passport


class CrossRepositoryFeatureRegressions(unittest.TestCase):
    def setUp(self):
        from packages.core.parallelism.feature import FeatureAuthority
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.dispatcher = Dispatcher(self.root / 'private/root.sqlite3')
        self.value, self.passport = feature_fixture(self.root)
        self.dispatcher.create_run(self.value)
        self.authority = FeatureAuthority(self.dispatcher, self.value['run_id'])
        self.authority.create(self.passport)

    def tearDown(self):
        self.temporary.cleanup()

    def compose(self, **kwargs):
        return self.authority.compose(kwargs.pop('components', {
            'auth': {'commit': 'c' * 40}, 'ledger': {'commit': 'd' * 40}}),
            test_suite_sha256='7' * 64, environment_sha256='8' * 64, **kwargs)

    def build(self):
        adapter = FakeAdapter()
        self.dispatcher.run_local(self.value['run_id'], adapter, verify)
        self.assertEqual(set(task for task, _ in adapter.calls), {'task-0', 'task-1'})

    def settle_slot(self, slot, composition):
        task = self.dispatcher.claim_task(self.value['run_id'], slot)
        self.assertIsNotNone(task)
        result = self.dispatcher.finish_task(self.value['run_id'], slot, task['attempt_id'],
            dict(status='submitted', subject=composition['composition_id'],
                 tokens=2, cost_micros=3, usage_known=True, stopped=True), verify)
        self.assertEqual(result['status'], 'verified')

    def check(self, composition, kind, verdict='PASS', **overrides):
        check = next(c for c in self.passport['acceptance_protocol']['checks'] if c['check_id'] == kind)
        self.settle_slot(check['task_id'], composition)
        proof = dict(independent=True, subject=composition['composition_id'], verdict=verdict,
                     criteria_sha256=check['criteria_sha256'], verifier_id='independent-reviewer',
                     evidence_sha256='9' * 64)
        proof.update(overrides)
        return self.authority.record_check(composition['composition_id'], kind,
            {'task_id': check['task_id']}, verifier=lambda *_: proof)

    def ready(self):
        self.build()
        composition = self.compose()
        for kind in ('local', 'contract', 'business', 'transition'):
            self.check(composition, kind)
        self.assertEqual(self.authority.report()['status'], 'release_ready')
        return composition

    def test_unresolved_business_rule_blocks_real_task_admission(self):
        revised = copy.deepcopy(self.passport)
        revised['plan_revision'] = 2
        revised['business_invariants'][0]['resolved'] = False
        self.authority.update_passport(revised, approvals=self.passport['owners'])
        adapter = FakeAdapter()
        self.dispatcher.run_local(self.value['run_id'], adapter, verify)
        self.assertEqual(adapter.calls, [])
        self.assertEqual(self.authority.report()['status'], 'blocked')

    def test_contract_change_needs_both_boundary_owners_and_fences_old_tasks(self):
        revised = copy.deepcopy(self.passport)
        revised['plan_revision'] = 2
        revised['contracts'][0].update(revision=2, semantics_sha256='a' * 64)
        with self.assertRaises(ValueError):
            self.authority.update_passport(revised, approvals=['coordinator', 'owner-auth'])
        self.assertEqual(self.authority.report()['plan_revision'], 1)
        self.authority.update_passport(revised,
            approvals=['coordinator', 'owner-auth', 'owner-ledger'])
        adapter = FakeAdapter()
        self.dispatcher.run_local(self.value['run_id'], adapter, verify)
        self.assertEqual(adapter.calls, [])
        self.assertIn('contract_task_pins_stale', self.authority.report()['blockers'])

    def test_all_local_ci_can_pass_while_business_scenario_rejects_feature(self):
        self.build()
        composition = self.compose()
        for kind in ('local', 'contract', 'transition'):
            self.check(composition, kind)
        report = self.check(composition, 'business', verdict='FAIL')
        self.assertEqual(report['status'], 'failed')
        self.assertIn('acceptance_incomplete', report['blockers'])

    def test_commit_change_invalidates_every_old_acceptance_and_rejects_stale_proof(self):
        composition = self.ready()
        changed = self.compose(components={'auth': {'commit': 'e' * 40}, 'ledger': {'commit': 'd' * 40}})
        self.assertNotEqual(changed['composition_id'], composition['composition_id'])
        report = self.authority.report()
        self.assertNotEqual(report['status'], 'release_ready')
        self.assertTrue(all(check['verdict'] == 'NOT_RUN' for check in report['checks']))
        with self.assertRaises(ValueError):
            self.authority.record_check(composition['composition_id'], 'business', {}, verifier=lambda *_: {})

    def test_unmatched_check_criteria_and_self_verification_are_rejected(self):
        self.build()
        composition = self.compose()
        self.settle_slot('task-2', composition)
        check = self.passport['acceptance_protocol']['checks'][0]
        base = dict(independent=True, subject=composition['composition_id'], verdict='PASS',
            criteria_sha256=check['criteria_sha256'], verifier_id='independent-reviewer', evidence_sha256='9' * 64)
        for change in ({'criteria_sha256': '0' * 64}, {'subject': 'f' * 64},
                       {'independent': False}, {'verifier_id': check['owner']}):
            proof = dict(base, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.authority.record_check(composition['composition_id'], 'local', {},
                                            verifier=lambda *_: proof)
        self.assertEqual(self.authority.report()['checks'][0]['verdict'], 'NOT_RUN')

    def test_unsafe_old_new_prefix_matrix_is_rejected_before_release(self):
        revised = copy.deepcopy(self.passport)
        revised['plan_revision'] = 2
        revised['release_plan']['allowed_matrices'].pop(1)
        with self.assertRaises(ValueError):
            self.authority.update_passport(revised, approvals=['coordinator', 'owner-auth', 'owner-ledger'])

    def test_source_plan_contains_same_exact_feature_state_without_rewriting_prose(self):
        self.build()
        self.compose()
        plan = self.root / 'plan.md'
        plan.write_text('# Independent source plan\n\nKeep this rationale.\n')
        report = self.authority.export_progress(plan)
        self.assertTrue(plan.read_text().startswith('# Independent source plan\n\nKeep this rationale.'))
        import json
        body = plan.read_text().split('```json\n', 1)[1].split('\n```', 1)[0]
        persisted = json.loads(body)
        for key in ('feature_id', 'run_id', 'plan_revision', 'composition_id', 'usage', 'blockers', 'status'):
            self.assertEqual(persisted[key], report[key])

    def authorization(self, composition, actor='coordinator'):
        return dict(confirmed=True, actor=actor, environment='staging',
                    composition_id=composition['composition_id'])

    def release(self, composition):
        return self.authority.begin_release(composition['composition_id'], 'staging',
            authorization=self.authorization(composition),
            observed_versions=self.passport['release_plan']['initial_versions'],
            observed_state_sha256=self.passport['release_plan']['initial_state_sha256'])

    def test_release_unknown_restart_preserves_reservation_and_never_relaunches(self):
        composition = self.ready()
        operation = self.release(composition)
        kwargs = dict(authorization=self.authorization(composition, 'owner-auth'),
                      observed_versions=self.passport['release_plan']['initial_versions'],
            observed_state_sha256=self.passport['release_plan']['initial_state_sha256'])
        first = self.authority.begin_step(operation['operation_id'], 'auth-deploy', **kwargs)
        self.assertTrue(first['launch_allowed'])
        task = first['task']
        self.dispatcher.finish_task(self.value['run_id'], 'task-6', task['attempt_id'],
            dict(status='unknown', subject=composition['composition_id'], tokens=5,
                 cost_micros=7, usage_known=False, stopped=False), verify)
        self.authority.finish_step(operation['operation_id'], 'auth-deploy', {}, verifier=lambda *_: dict(
            independent=True, subject=composition['composition_id'], verdict='INCONCLUSIVE',
            evidence_sha256='9' * 64))
        from packages.core.parallelism.feature import FeatureAuthority
        reopened = FeatureAuthority(Dispatcher(self.root / 'private/root.sqlite3'), self.value['run_id'])
        repeated = reopened.begin_step(operation['operation_id'], 'auth-deploy', **kwargs)
        self.assertFalse(repeated['launch_allowed'])
        report = reopened.report()
        self.assertEqual(report['status'], 'unknown')
        self.assertFalse(report['usage']['known'])
        self.assertEqual(report['usage']['reserved_tokens'], 95)
        self.assertEqual(report['usage']['reserved_cost_micros'], 93)
        self.assertEqual(next(t for t in report['tasks'] if t['task_id'] == 'task-6')['attempt_id'], 1)

    def test_wrong_release_environment_and_stale_initial_versions_are_rejected(self):
        composition = self.ready()
        for environment, observed in (('production', self.passport['release_plan']['initial_versions']),
                                      ('staging', {'auth': 'e' * 40, 'ledger': 'b' * 40})):
            with self.subTest(environment=environment, observed=observed), self.assertRaises(ValueError):
                self.authority.begin_release(composition['composition_id'], environment,
                    authorization=self.authorization(composition), observed_versions=observed,
                    observed_state_sha256=self.passport['release_plan']['initial_state_sha256'])
        self.assertEqual(self.authority.report()['status'], 'release_ready')

    def complete_release(self, composition, *, late_spare=False):
        operation = self.release(composition)
        observed = self.passport['release_plan']['initial_versions']
        observed_state = self.passport['release_plan']['initial_state_sha256']
        for step in self.passport['release_plan']['steps']:
            admitted = self.authority.begin_step(operation['operation_id'], step['step_id'],
                authorization=self.authorization(composition, step['owner']), observed_versions=observed,
                observed_state_sha256=observed_state)
            task = admitted['task']
            if late_spare and step['step_id'] == 'ledger-deploy':
                self._spare_task = self.dispatcher.claim_task(self.value['run_id'], 'task-8')
                self.assertIsNotNone(self._spare_task)
            self.dispatcher.finish_task(self.value['run_id'], step['task_id'], task['attempt_id'],
                dict(status='submitted', subject=composition['composition_id'], tokens=1,
                     cost_micros=1, usage_known=True, stopped=True), verify)
            self.authority.finish_step(operation['operation_id'], step['step_id'], {}, verifier=lambda *_: dict(
                independent=True, subject=composition['composition_id'], verdict='PASS',
                versions=step['versions'], state_sha256=step['state_sha256'], evidence_sha256='9' * 64))
            observed = step['versions']
            observed_state = step['state_sha256']
        return operation

    def test_cancellation_is_not_hidden_by_observing_release_status(self):
        composition = self.ready()
        self.complete_release(composition)
        self.assertEqual(self.authority.report()['status'], 'observing')
        self.dispatcher.cancel(self.value['run_id'])
        report = self.authority.report()
        self.assertIn(report['status'], {'cancel_requested', 'cancelled'})
        self.assertIn('root_cancelled', report['blockers'])

    def test_switching_away_and_back_does_not_silently_revive_old_readiness(self):
        self.ready()
        self.compose(components={'auth': {'commit': 'e' * 40}, 'ledger': {'commit': 'd' * 40}})
        try:
            self.compose()
        except ValueError:
            return  # Rejecting stale composition reuse is safe.
        report = self.authority.report()
        self.assertNotEqual(report['status'], 'release_ready')
        self.assertTrue(all(check['verdict'] == 'NOT_RUN' for check in report['checks']))

    def test_passport_cannot_change_under_running_or_unknown_worker(self):
        claimed = self.dispatcher.claim_task(self.value['run_id'], 'task-0')
        self.assertIsNotNone(claimed)
        revised = copy.deepcopy(self.passport)
        revised['plan_revision'] = 2
        revised['contracts'][0].update(revision=2, semantics_sha256='a' * 64)
        approvals = ['coordinator', 'owner-auth', 'owner-ledger']
        with self.assertRaises(ValueError):
            self.authority.update_passport(revised, approvals=approvals)
        self.dispatcher.finish_task(self.value['run_id'], 'task-0', claimed['attempt_id'],
            dict(status='unknown', tokens=5, cost_micros=5, usage_known=False, stopped=False), verify)
        with self.assertRaises(ValueError):
            self.authority.update_passport(revised, approvals=approvals)
        self.assertEqual(self.authority.report()['plan_revision'], 1)

    def test_remote_worker_cannot_revise_feature_or_claim_other_repository(self):
        import hashlib
        from packages.core.parallelism.authority import authority_server, RemoteDispatcher
        token = 'a' * 64
        credential = self.root / 'worker.token'
        credential.write_text(token)
        credential.chmod(0o600)
        server = authority_server(self.dispatcher, verify, {
            hashlib.sha256(token.encode()).hexdigest(): dict(
                runs=[self.value['run_id']], tasks=['task-0'], control=False)})
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = RemoteDispatcher('http://127.0.0.1:' + str(server.server_port), credential)
            report = client.get_feature(self.value['run_id'])
            self.assertEqual(report['feature_id'], 'referral')
            adapter = FakeAdapter()
            with self.assertRaises(ValueError):
                client.execute_task(self.value['run_id'], 'task-1', adapter)
            with self.assertRaises(ValueError):
                client.feature_event(self.value['run_id'], 'compose', {},
                                     passport_sha256=report['passport_sha256'])
            self.assertEqual(adapter.calls, [])
            self.assertIsNone(self.authority.report()['composition_id'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_environment_fingerprint_is_required_even_when_commits_match(self):
        composition = self.ready()
        with self.assertRaises(ValueError):
            self.authority.begin_release(composition['composition_id'], 'staging',
                authorization=self.authorization(composition),
                observed_versions=self.passport['release_plan']['initial_versions'],
                observed_state_sha256='0' * 64)
        self.assertEqual(self.authority.report()['status'], 'release_ready')

    def test_observation_rechecks_cancellation_after_verifier_callback(self):
        import time
        from unittest.mock import patch
        composition = self.ready()
        operation = self.complete_release(composition)
        def proof(plan, receipt):
            self.dispatcher.cancel(self.value['run_id'])
            return dict(independent=True, subject=composition['composition_id'], verdict='PASS',
                versions=plan['steps'][-1]['versions'], state_sha256=plan['steps'][-1]['state_sha256'],
                observed_seconds=2, metrics={'error-rate': 0}, evidence_sha256='9' * 64)
        with patch('packages.core.parallelism.feature.time.time', return_value=time.time() + 2):
            with self.assertRaises(ValueError):
                self.authority.observe(operation['operation_id'], {}, verifier=proof)
        self.assertNotEqual(self.authority.report()['status'], 'accepted')

    def test_observation_needs_real_elapsed_window_and_every_numeric_metric(self):
        import time
        from unittest.mock import patch
        composition = self.ready()
        operation = self.complete_release(composition)
        plan = self.passport['release_plan']
        proof = dict(independent=True, subject=composition['composition_id'], verdict='PASS',
            versions=plan['steps'][-1]['versions'], state_sha256=plan['steps'][-1]['state_sha256'],
            observed_seconds=2, metrics={'error-rate': 0}, evidence_sha256='9' * 64)
        with self.assertRaises(ValueError):
            self.authority.observe(operation['operation_id'], {}, verifier=lambda *_: proof)
        with patch('packages.core.parallelism.feature.time.time', return_value=time.time() + 2):
            for metrics in ({}, {'error-rate': float('nan')}, {'error-rate': True}):
                invalid = dict(proof, metrics=metrics)
                with self.subTest(metrics=metrics), self.assertRaises(ValueError):
                    self.authority.observe(operation['operation_id'], {}, verifier=lambda *_: invalid)
        self.assertEqual(self.authority.report()['status'], 'observing')

    def test_repaired_check_cannot_hide_a_failed_mandatory_root_operation(self):
        from packages.core.parallelism.feature import FeatureAuthority
        root = self.root / 'mandatory-failure'
        root.mkdir()
        value, passport = feature_fixture(root)
        repair = copy.deepcopy(value['tasks'][2])
        repair.update(task_id='local-repair', required_for_completion=False)
        value['tasks'].append(repair)
        passport['task_graph'].append('local-repair')
        passport['acceptance_protocol']['checks'][0]['repair_task_ids'] = ['local-repair']
        dispatcher = Dispatcher(root / 'private/root.sqlite3')
        dispatcher.create_run(value)
        authority = FeatureAuthority(dispatcher, value['run_id'])
        authority.create(passport)
        dispatcher.run_local(value['run_id'], FakeAdapter(), verify)
        composition = authority.compose({'auth': {'commit': 'c' * 40}, 'ledger': {'commit': 'd' * 40}},
            test_suite_sha256='7' * 64, environment_sha256='8' * 64)
        failed = dispatcher.claim_task(value['run_id'], 'task-2')
        dispatcher.finish_task(value['run_id'], 'task-2', failed['attempt_id'],
            dict(status='failed', tokens=1, cost_micros=1, usage_known=True, stopped=True), verify)
        for check in passport['acceptance_protocol']['checks']:
            slot = 'local-repair' if check['check_id'] == 'local' else check['task_id']
            admitted = dispatcher.claim_task(value['run_id'], slot)
            self.assertIsNotNone(admitted)
            dispatcher.finish_task(value['run_id'], slot, admitted['attempt_id'],
                dict(status='submitted', subject=composition['composition_id'], tokens=1,
                     cost_micros=1, usage_known=True, stopped=True), verify)
            proof = dict(independent=True, subject=composition['composition_id'], verdict='PASS',
                criteria_sha256=check['criteria_sha256'], verifier_id='independent-reviewer', evidence_sha256='9' * 64)
            authority.record_check(composition['composition_id'], check['check_id'], {'task_id': slot},
                                   verifier=lambda *_: proof)
        root_report = dispatcher.get_run(value['run_id'])
        self.assertEqual(next(t for t in root_report['tasks'] if t['task_id'] == 'task-2')['state'], 'failed')
        self.assertNotEqual(authority.report()['status'], 'release_ready')

    def fail_spare(self):
        task = getattr(self, '_spare_task', None) or self.dispatcher.claim_task(self.value['run_id'], 'task-8')
        self.assertIsNotNone(task)
        self.dispatcher.finish_task(self.value['run_id'], 'task-8', task['attempt_id'],
            dict(status='failed', tokens=1, cost_micros=1, usage_known=True, stopped=True), verify)

    def test_failed_root_operation_blocks_new_release_step_intent(self):
        composition = self.ready()
        operation = self.release(composition)
        self.fail_spare()
        with self.assertRaises(ValueError):
            self.authority.begin_step(operation['operation_id'], 'auth-deploy',
                authorization=self.authorization(composition, 'owner-auth'),
                observed_versions=self.passport['release_plan']['initial_versions'],
                observed_state_sha256=self.passport['release_plan']['initial_state_sha256'])
        self.assertEqual(next(t for t in self.authority.report()['tasks'] if t['task_id'] == 'task-6')['attempt_id'], 0)

    def test_failed_root_operation_after_claim_cannot_authorize_controller_launch(self):
        from unittest.mock import patch
        composition = self.ready()
        operation = self.release(composition)
        original_claim = self.dispatcher.claim_task
        def race(run_id, task_id):
            task = original_claim(run_id, task_id)
            if task_id == 'task-6':
                with patch.object(self.dispatcher, 'claim_task', original_claim):
                    self.fail_spare()
            return task
        with patch.object(self.dispatcher, 'claim_task', race):
            result = self.authority.begin_step(operation['operation_id'], 'auth-deploy',
                authorization=self.authorization(composition, 'owner-auth'),
                observed_versions=self.passport['release_plan']['initial_versions'],
                observed_state_sha256=self.passport['release_plan']['initial_state_sha256'])
        self.assertFalse(result['launch_allowed'])
        self.assertGreater(self.authority.report()['usage']['reserved_tokens'], 0)

    def test_observation_cannot_persist_acceptance_after_failed_root_operation(self):
        import time
        from unittest.mock import patch
        composition = self.ready()
        operation = self.complete_release(composition, late_spare=True)
        def proof(plan, receipt):
            self.fail_spare()
            return dict(independent=True, subject=composition['composition_id'], verdict='PASS',
                versions=plan['steps'][-1]['versions'], state_sha256=plan['steps'][-1]['state_sha256'],
                observed_seconds=2, metrics={'error-rate': 0}, evidence_sha256='9' * 64)
        with patch('packages.core.parallelism.feature.time.time', return_value=time.time() + 2):
            with self.assertRaises(ValueError):
                self.authority.observe(operation['operation_id'], {}, verifier=proof)
        self.assertNotEqual(self.authority.report()['release']['state'], 'accepted')
