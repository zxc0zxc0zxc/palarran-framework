"""Bounded provider metadata observations, never a transcript or billing oracle."""
from __future__ import annotations
import hashlib
import json
from packages.core.orchestration.runtime.usage import UsageStream

_TERMINAL = {'completed', 'errored', 'shutdown', 'stopped', 'failed'}


def _identity(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 256:
        raise ValueError('Invalid provider identity')
    return hashlib.sha256(value.encode()).hexdigest()[:24]


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate metadata field')
        result[key] = value
    return result


class TeamObserver:
    """Only lifecycle/usage fields survive; text, prompts and reasoning are dropped.

    Codex child usage needs thread-tagged turn events. Missing descendant usage is
    unknown, not an inferred zero. Claude final modelUsage/cost is used once for
    the top-level session; nested assistant usage is never added a second time.
    """
    def __init__(self, adapter, maximum, publish, usage, partial_tokens=None):
        self.adapter, self.maximum = adapter, maximum
        self.publish, self.usage_callback = publish, usage
        self.partial_tokens = partial_tokens
        self.messages = {}
        self.buffer = bytearray()
        self.children = {}
        self.streams = {'root': UsageStream(adapter)}
        self.snapshots = {}
        self.root_id = None
        self.lines = 0
        self.failed = False
        self.over_limit = False
        self.activity = "starting"
        self.needs_human = False
        self.aggregate_scope = 'provider_session_report' if adapter == 'claude' else 'observed_thread_streams'

    def report(self):
        return dict(activity=self.activity,needs_human=self.needs_human,
                    cost_kind='provider_report' if self.adapter=='claude' else 'price_card_estimate',
                    children=[dict(agent_id=k, state=v) for k,v in sorted(self.children.items())],
                    observed_active=sum(v in ('running', 'requested') for v in self.children.values()),
                    discovered=len(self.children), capacity=self.maximum,
                    count_scope='observed_lower_bound', observation_complete=False,
                    usage_scope=self.aggregate_scope, telemetry_failed=self.failed,
                    capacity_exceeded=self.over_limit)

    def _child(self, identity, state):
        key = _identity(identity)
        if key not in self.children and len(self.children) >= 256:
            raise ValueError('Lifetime child observation bound')
        old = self.children.get(key)
        # Do not revive completed agents from repeated/stale observations.
        if old not in _TERMINAL:
            self.children[key] = state
        if sum(v in ('running','requested') for v in self.children.values()) > self.maximum:
            self.over_limit = True
        return key

    def _line(self, raw):
        self.lines += 1
        if self.lines > 10000:
            raise ValueError('Event count bound')
        record = json.loads(raw, object_pairs_hook=_pairs)
        if not isinstance(record, dict):
            raise ValueError('Event object required')
        kind = record.get('type')
        parent = record.get('parent_tool_use_id')
        if self.adapter == 'codex':
            if kind == 'thread.started' and self.root_id is None:
                self.root_id = record.get('thread_id')
            item = record.get('item', {})
            if isinstance(item, dict) and kind in ('item.started','item.updated','item.completed'):
                activities={'command_execution':'command','file_change':'editing','web_search':'research','collab_tool_call':'delegating'}
                if item.get('type') in activities:
                    self.activity=activities[item['type']] if kind!='item.completed' else 'working'
            if kind in ('item.started','item.updated','item.completed') and isinstance(item, dict) and item.get('type') == 'collab_tool_call':
                for identity, state in item.get('agents_states', {}).items():
                    status = state.get('status') if isinstance(state, dict) else state
                    if status in ('running','pending_init','completed','errored','shutdown'):
                        self._child(identity, 'requested' if status == 'pending_init' else status)
            identity = record.get('thread_id')
            key = 'root' if identity is None or identity == self.root_id else _identity(identity)
            if key != 'root':
                self._child(identity, self.children.get(key, 'running'))
            if kind in ('thread.started','turn.started','turn.completed','turn.failed','error'):
                stream = self.streams.setdefault(key, UsageStream('codex'))
                for snapshot in stream.feed(raw+b'\n'):
                    self.snapshots[key] = snapshot
        else:
            if parent:
                self._child(parent, 'running')
            message = record.get('message', {})
            if kind == 'assistant' and isinstance(message, dict) and message.get('id') and isinstance(message.get('usage'), dict):
                usage = message['usage']
                counts = [usage.get(k,0) for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens')]
                if any(type(v) is not int or not 0<=v<=10**12 for v in counts):
                    raise ValueError('Invalid partial usage')
                message_id = _identity(message['id'])
                if message_id not in self.messages and len(self.messages)>=10000:
                    raise ValueError('Partial usage message bound')
                self.messages[message_id] = max(self.messages.get(message_id,0),sum(counts))
                if self.partial_tokens and self.partial_tokens(sum(self.messages.values())) is False:
                    return False
            if kind in ('assistant','user') and isinstance(message, dict):
                content = message.get('content', [])
                for block in content if isinstance(content, list) else []:
                    if not isinstance(block, dict):continue
                    if block.get('type') == 'tool_use':
                        activities={'Read':'reading','Edit':'editing','Write':'editing','Bash':'command','Agent':'delegating','Task':'delegating','AskUserQuestion':'needs_human'}
                        self.activity=activities.get(block.get('name'),'working')
                        self.needs_human=self.needs_human or self.activity=='needs_human'
                    if block.get('type') == 'tool_use' and block.get('name') in ('Agent','Task'):
                        self._child(block.get('id'), 'requested')
                    elif block.get('type') == 'tool_result':
                        key = _identity(block.get('tool_use_id'))
                        if key in self.children:self.children[key] = 'completed'
            if not parent:
                for snapshot in self.streams['root'].feed(raw+b'\n'):
                    self.snapshots['root'] = snapshot
        self.publish(self.report())
        return not self.over_limit and not self.needs_human and self.usage_callback(list(self.snapshots.values())) is not False

    def feed(self, chunk):
        if self.failed:return False
        try:
            for part in chunk.splitlines(keepends=True):
                self.buffer.extend(part)
                if len(self.buffer)>1048576:raise ValueError('Event line bound')
                if self.buffer.endswith(b'\n'):
                    raw=bytes(self.buffer).strip();self.buffer.clear()
                    if raw and not self._line(raw):return False
            return True
        except (ValueError,TypeError,KeyError,AttributeError,RecursionError,OverflowError):
            self.failed=True;self.buffer.clear();self.publish(self.report());return False

    def finish(self):
        if self.failed or self.over_limit:return False
        try:
            if self.buffer:
                if not self._line(bytes(self.buffer)):return False
                self.buffer.clear()
            for stream in self.streams.values():stream.finish()
            if self.adapter == 'codex' and set(self.children)-set(self.snapshots):return False
            return 'root' in self.snapshots
        except (ValueError,TypeError,KeyError):return False
