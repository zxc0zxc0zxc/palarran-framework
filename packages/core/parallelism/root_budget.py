"""Integration/verification stages consume predeclared tasks in the same root ledger."""
import uuid


class DispatcherBudgetBinding:
    """Coordinator-owned slot map; the queue cannot invent tasks or new limits.

    slots maps (run_id, phase, item_key) to an already approved root task_id.
    The separately configured verifier binds each stage to exact evidence.
    """
    def __init__(self, dispatcher, slots, verifier):
        if not callable(verifier) or type(slots) is not dict:
            raise ValueError('Reviewed slot mapping and independent verifier required')
        self.dispatcher, self.slots, self.verifier = dispatcher, dict(slots), verifier
        with dispatcher.ledger.transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS parallel_budget_tickets(
                ticket TEXT PRIMARY KEY, run TEXT NOT NULL, task TEXT NOT NULL,
                attempt INTEGER NOT NULL, state TEXT NOT NULL)''')

    def reserve(self, run_id, phase, item_id):
        if phase not in ('integration', 'verification'):
            raise ValueError('Unsupported integration budget phase')
        task_id = self.slots.get((run_id, phase, item_id))
        if task_id is None:
            return None
        report = self.dispatcher.get_run(run_id)
        registered = next((t for t in report['tasks'] if t['task_id'] == task_id), None)
        if registered is None or registered['budget_phase'] != phase or registered['dispatch_mode'] != 'external':
            raise ValueError('Stage must use a matching predeclared root allocation')
        packet = self.dispatcher.claim_task(run_id, task_id)
        if packet is None:
            return None
        ticket = uuid.uuid4().hex
        with self.dispatcher.ledger.transaction() as db:
            db.execute('INSERT INTO parallel_budget_tickets VALUES(?,?,?,?,?)', (ticket, run_id, task_id, packet['attempt_id'], 'open'))
        return ticket

    def heartbeat(self, ticket):
        with self.dispatcher.ledger.transaction() as db:
            row = db.execute('SELECT * FROM parallel_budget_tickets WHERE ticket=?', (ticket,)).fetchone()
            if row is None or row['state'] != 'open':
                return False
            run, task, attempt = row['run'], row['task'], row['attempt']
        return self.dispatcher.heartbeat(run, task, attempt)

    def settle(self, ticket, outcome):
        if type(outcome) is not dict or outcome.get('status') not in ('known', 'unknown'):
            raise ValueError('Explicit stage outcome required')
        for field in ('tokens', 'cost_micros'):
            value = outcome.get(field, 0)
            if type(value) is not int or value < 0:
                raise ValueError('Invalid stage usage')
        with self.dispatcher.ledger.transaction() as db:
            row = db.execute('SELECT * FROM parallel_budget_tickets WHERE ticket=?', (ticket,)).fetchone()
            if row is None:
                raise ValueError('Unknown root reservation')
            if row['state'] != 'open':
                return {'status': 'reconciliation_required'}
            db.execute("UPDATE parallel_budget_tickets SET state='settling' WHERE ticket=?", (ticket,))
            run, task, attempt = row['run'], row['task'], row['attempt']
        known = outcome['status'] == 'known' and outcome.get('stopped') is True
        # A known negative gate is a completed, independently checked operation.
        # Business acceptance belongs to the separate final/acceptance task.
        receipt = {'status': 'submitted' if known else 'unknown',
                   'tokens': outcome.get('tokens', 0), 'cost_micros': outcome.get('cost_micros', 0),
                   'usage_known': known, 'stopped': known}
        subject = outcome.get('subject')
        if isinstance(subject, str) and subject:
            receipt['subject'] = subject
        result = self.dispatcher.finish_task(run, task, attempt, receipt, self.verifier)
        with self.dispatcher.ledger.transaction() as db:
            db.execute("UPDATE parallel_budget_tickets SET state=? WHERE ticket=?", ('settled' if known else 'unknown', ticket))
        return result
