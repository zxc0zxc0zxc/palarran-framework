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
    PLANNING = 'planning'
    IMPLEMENTING = 'implementing'
    VERIFYING = 'verifying'
    RELEASE_READY = 'release_ready'
    RELEASING = 'releasing'
    RELEASED = 'released'
    BLOCKED = 'blocked'
    UNKNOWN = 'unknown'


class CheckVerdict(WireState):
    PASS = 'PASS'
    FAIL = 'FAIL'
    INCONCLUSIVE = 'INCONCLUSIVE'
    NOT_RUN = 'NOT_RUN'
