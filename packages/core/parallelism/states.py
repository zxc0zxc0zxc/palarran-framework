"""Named wire states, compatible with Python 3.9 and existing SQLite rows."""
from enum import Enum


class WireState(str, Enum):
    def __str__(self):
        return self.value


class TaskState(WireState):
    PENDING = 'pending'
    READY = 'ready'
    RUNNING = 'running'
    SUBMITTED = 'submitted'
    VERIFIED = 'verified'
    BLOCKED = 'blocked'
    FAILED = 'failed'
    CANCEL_REQUESTED = 'cancel_requested'
    CANCELLED = 'cancelled'
    UNKNOWN = 'unknown'
    HANDOFF_PENDING = 'handoff_pending'


class FeatureState(WireState):
    DRAFT = 'draft'
    CONTRACTS_READY = 'contracts_ready'
    IMPLEMENTING = 'implementing'
    INTEGRATING = 'integrating'
    VERIFYING = 'verifying'
    RELEASE_READY = 'release_ready'
    RELEASING = 'releasing'
    OBSERVING = 'observing'
    ACCEPTED = 'accepted'
    BLOCKED = 'blocked'
    FAILED = 'failed'
    UNKNOWN = 'unknown'
    CANCEL_REQUESTED = 'cancel_requested'
    CANCELLED = 'cancelled'


class CheckVerdict(WireState):
    PASS = 'PASS'
    FAIL = 'FAIL'
    INCONCLUSIVE = 'INCONCLUSIVE'
    NOT_RUN = 'NOT_RUN'
