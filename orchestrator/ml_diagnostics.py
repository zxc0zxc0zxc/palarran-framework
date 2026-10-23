"""Versioned private training diagnostics; no model/provider calls or second cost ledger."""
from contextlib import nullcontext
import hashlib
import html
import json
import math
import os
from pathlib import Path
import random
import re
import time
import uuid

from scripts import ml_data as data

SHA = re.compile(r'[0-9a-f]{64}')
KINDS = ('metric','generation','nonfinite')
PROFILES = ('causal_lm','classification','regression','retrieval','custom')


def validate_policy(p):
    data.fields(p, ('version','profile','metrics','rules','probes','decoding','required_generations',
                    'max_bytes','max_events','max_gap_seconds','preprint'))
    data.require(type(p['version']) is int and p['version']==1 and p['profile'] in PROFILES)
    for key in ('required_generations','preprint'):
        data.require(type(p[key]) is bool)
    data.integer(p['max_bytes'],1024,8*1024**2); data.integer(p['max_events'],1,10000)
    data.integer(p['max_gap_seconds'],1,86400)
    data.require(isinstance(p['metrics'],dict) and 1<=len(p['metrics'])<=32)
    for name,m in p['metrics'].items():
        data.text(name,64); data.fields(m,('kind','direction','required'))
        data.require(m['kind'] in ('nll','ratio','gauge') and m['direction'] in ('min','max') and type(m['required']) is bool)
        data.require(m['kind']!='nll' or p['profile']=='causal_lm')
    data.require(isinstance(p['rules'],list) and len(p['rules'])<=32)
    seen=set()
    for rule in p['rules']:
        data.fields(rule,('id','metric','mode','threshold','min_support','warmup','patience','action','owner','rationale','calibration'),('split','slice'))
        data.text(rule['id'],64); data.require(rule['id'] not in seen); seen.add(rule['id'])
        for field in ('owner','rationale','calibration'): data.text(rule[field],512)
        data.require(rule['metric'] in p['metrics'] and rule['mode'] in ('above','below','plateau','regression'))
        data.require(rule.get('split','validation') in ('train','validation','test'))
        if 'slice' in rule: data.text(rule['slice'],128)
        finite(rule['threshold']); data.require(rule['threshold']>=0)
        data.integer(rule['min_support'],1); data.integer(rule['warmup']); data.integer(rule['patience'],1,1000)
        data.require(rule['action'] in ('observe','block_acceptance','stop_training'))
    data.require(isinstance(p['probes'],list) and len(p['probes'])<=64 and isinstance(p['decoding'],dict))
    data.require(len(data.canonical(p['decoding']).encode())<=16384)
    seen=set()
    for probe in p['probes']:
        data.fields(probe,('id','prompt','split','validator')); data.text(probe['id'],64)
        data.require(probe['id'] not in seen and probe['split']=='diagnostic'); seen.add(probe['id'])
        data.require(isinstance(probe['prompt'],str) and 0<len(probe['prompt'])<=16384 and probe['validator'] in ('none','json'))
    data.require(not p['required_generations'] or bool(p['probes']))
    return p


def finite(n):
    data.require(type(n) in (int,float) and math.isfinite(n))
    return n


def nll_statistics(log_probs, labels, attention):
    """Unshifted causal labels; caller supplies actual log probabilities, not logits."""
    data.require(len(log_probs)==len(labels)==len(attention))
    total,count=0.0,0
    for probs,targets,mask in zip(log_probs,labels,attention):
        data.require(len(probs)==len(targets)==len(mask))
        for i in range(1,len(targets)):
            if mask[i] and targets[i]!=-100:
                data.integer(targets[i],0,len(probs[i-1])-1)
                total-=finite(probs[i-1][targets[i]]); count+=1
    data.require(total>=0 and count>0)
    return dict(numerator=total,denominator=count)


def metric_value(spec,payload):
    if spec['kind']=='gauge':
        data.fields(payload,('metric','value','support'),('slice','eval_id'))
        return finite(payload['value']),data.integer(payload['support'],1),None
    data.fields(payload,('metric','numerator','denominator'),('slice','eval_id'))
    numerator=finite(payload['numerator']); denominator=data.integer(payload['denominator'],1)
    data.require(numerator>=0)
    if spec['kind']=='ratio': data.require(numerator<=denominator)
    value=numerator/denominator
    return value,denominator,(numerator,denominator)


def event_valid(event, packet):
    data.fields(event,('version','pipeline_id','task_id','attempt','sequence','kind','step','split','subject','policy_sha256','payload','at'))
    data.require(type(event['version']) is int and event['version']==1 and event['kind'] in KINDS)
    for key in ('pipeline_id','task_id','attempt','policy_sha256'): data.require(event[key]==packet[key])
    data.integer(event['sequence'],1); data.integer(event['step']); finite(event['at'])
    data.require(event['split'] in ('train','validation','test','diagnostic'))
    data.require(isinstance(event['subject'],str) and bool(SHA.fullmatch(event['subject'])))
    payload=event['payload']; p=packet['policy']
    if event['kind']=='metric':
        data.require(isinstance(payload,dict) and payload.get('metric') in p['metrics'])
        metric_value(p['metrics'][payload['metric']],payload)
        if event['split'] in ('validation','test'): data.text(payload.get('eval_id'),128)
        if 'slice' in payload: data.text(payload['slice'],128)
    elif event['kind']=='generation':
        data.fields(payload,('probe_id','decoding_sha256','output','token_ids','finish_cause'))
        data.require(event['split']=='diagnostic' and payload['probe_id'] in {x['id'] for x in p['probes']})
        data.require(payload['decoding_sha256']==data.digest(p['decoding']))
        data.require(isinstance(payload['output'],str) and len(payload['output'].encode())<=512*1024)
        data.require(isinstance(payload['token_ids'],list) and len(payload['token_ids'])<=32768)
        for token in payload['token_ids']: data.integer(token,0,2**32-1)
        data.require(payload['finish_cause'] in ('eos','configured_stop','token_limit','cancelled','error','unknown'))
    else:
        data.fields(payload,('reason',)); data.require(payload['reason'] in ('objective','gradient','parameter','derived_metric'))


class Writer:
    """One trusted writer per task attempt; framework state guard belongs to the trainer."""
    def __init__(self, packet):
        self.packet=packet; self.sequence=0
        validate_policy(packet['policy'])
        self.path=Path(packet['directory'])/'events.jsonl'
        data.require(not self.path.exists() and self.path.parent.resolve()==self.path.parent)
        self.path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.path.touch(mode=0o600,exist_ok=False)
    def emit(self,kind,step,split,subject,payload):
        event=dict(version=1,pipeline_id=self.packet['pipeline_id'],task_id=self.packet['task_id'],attempt=self.packet['attempt'],
                   sequence=self.sequence+1,kind=kind,step=step,split=split,subject=subject,
                   policy_sha256=self.packet['policy_sha256'],payload=payload,at=time.time())
        event_valid(event,self.packet)
        raw=(data.canonical(event)+'\n').encode()
        data.require(len(raw)<=data.MAX_LINE and self.sequence<self.packet['policy']['max_events'])
        data.require(self.path.stat().st_size+len(raw)<=self.packet['policy']['max_bytes'])
        with open(self.path,'ab') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        self.sequence+=1
        return event
    def metric(self,step,split,subject,metric,**values):
        return self.emit('metric',step,split,subject,dict(metric=metric,**values))
    def snapshot(self,step,model_bytes,generate,*,state_guard=None):
        data.require(type(model_bytes) is bytes)
        subject=data.sha(model_bytes); rng=random.getstate()
        try:
            with state_guard if state_guard is not None else nullcontext():
                for probe in self.packet['policy']['probes']:
                    result=generate(model_bytes,probe['prompt'],dict(self.packet['policy']['decoding']))
                    self.emit('generation',step,'diagnostic',subject,dict(probe_id=probe['id'],
                        decoding_sha256=data.digest(self.packet['policy']['decoding']),**result))
        finally: random.setstate(rng)


def install(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS ml_diagnostic_attempts (
      run_id TEXT, task_id TEXT, attempt INTEGER, packet TEXT NOT NULL,
      started REAL NOT NULL, last_event REAL NOT NULL, byte_count INTEGER NOT NULL DEFAULT 0,
      stream_sha256 TEXT NOT NULL, error TEXT, PRIMARY KEY(run_id,task_id,attempt));
    CREATE TABLE IF NOT EXISTS ml_diagnostic_events (
      run_id TEXT, task_id TEXT, attempt INTEGER, sequence INTEGER, payload TEXT NOT NULL,
      PRIMARY KEY(run_id,task_id,attempt,sequence));
    ''')


def atomic(path, raw):
    path=Path(path); data.require(path.parent.resolve()==path.parent and not path.is_symlink())
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'wb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        if temp.exists(): temp.unlink()


def start(store,run,task,attempt):
    record=store.get(run); flow=json.loads(record['workflow']); policy=flow['ml_policy']
    if 'diagnostics' not in policy: return None
    root=Path(policy['artifact_root'])/'diagnostics'/task/('attempt-'+str(attempt))
    data.require(not root.exists()); root.mkdir(mode=0o700,parents=True)
    packet=dict(version=1,directory=str(root),pipeline_id=policy['pipeline_id'],task_id=task,attempt=attempt,
                policy=policy['diagnostics'],policy_sha256=data.digest(policy['diagnostics']))
    atomic(root/'manifest.json',(data.canonical(packet)+'\n').encode())
    store.db.execute('INSERT INTO ml_diagnostic_attempts VALUES(?,?,?,?,?,?,?,?,?)',
                     (run,task,attempt,data.canonical(packet),time.time(),time.time(),0,data.sha(b''),None))
    return packet


def all_events(store,run,task=None):
    query='SELECT payload FROM ml_diagnostic_events WHERE run_id=?'
    params=[run]
    if task is not None: query+=' AND task_id=?'; params.append(task)
    return [data.parse(r['payload']) for r in store.db.execute(query+' ORDER BY task_id,attempt,sequence',params)]


def analyze(p,events):
    """Window observations are producer aggregates; eval IDs/slices identify disjoint measurements."""
    metrics=[]; rules=[]; generations=[]; errors=[]; seen_eval=set();seen_generations=set()
    for e in events:
        v=e['payload']
        if e['kind']=='nonfinite':
            errors.append('nonfinite_'+v['reason']); continue
        if e['kind']=='generation':
            identity=(e['task_id'],e['attempt'],e['step'],e['subject'],v['probe_id'])
            data.require(identity not in seen_generations);seen_generations.add(identity)
            probe=next(x for x in p['probes'] if x['id']==v['probe_id'])
            valid=None
            if probe['validator']=='json':
                try: data.parse(v['output']); valid=True
                except (ValueError,TypeError): valid=False
            generations.append(dict(e,validation=dict(format_valid=valid,complete=v['finish_cause'] in ('eos','configured_stop'))))
            continue
        value,support,stats=metric_value(p['metrics'][v['metric']],v)
        if 'eval_id' in v:
            key=(e['task_id'],e['attempt'],v['metric'],e['split'],v.get('slice','all'),v['eval_id'])
            data.require(key not in seen_eval); seen_eval.add(key)
        entry=dict(metric=v['metric'],step=e['step'],split=e['split'],subject=e['subject'],value=value,support=support,
                   slice=v.get('slice','all'),task_id=e['task_id'],attempt=e['attempt'],sequence=e['sequence'])
        if stats:
            entry.update(numerator=stats[0],denominator=stats[1])
        if p['metrics'][v['metric']]['kind']=='nll':
            entry['perplexity']=math.exp(value) if value<=math.log(float.fromhex('0x1.fffffffffffffp+1023')) else None
            entry['perplexity_status']='observed' if entry['perplexity'] is not None else 'overflow'
        metrics.append(entry)
    for spec in p['rules']:
        direction=p['metrics'][spec['metric']]['direction']; best=None; failures=0; state='missing'; evidence=None
        for m in metrics:
            if m['metric']!=spec['metric'] or m['split']!=spec.get('split','validation') or m['slice']!=spec.get('slice','all'): continue
            evidence=m
            if m['step']<spec['warmup']: state='warming_up'; continue
            if m['support']<spec['min_support']: state='insufficient_data'; continue
            v=m['value']; improvement=(best-v if direction=='min' else v-best) if best is not None else None
            if spec['mode']=='above': bad=v>spec['threshold']
            elif spec['mode']=='below': bad=v<spec['threshold']
            elif spec['mode']=='plateau': bad=best is not None and improvement<=spec['threshold']
            else: bad=best is not None and improvement < -spec['threshold']
            failures=failures+1 if bad else 0
            state='triggered' if failures>=spec['patience'] else ('suspect' if bad else 'ok')
            if best is None or (v<best if direction=='min' else v>best): best=v
            if state=='triggered': break
        rules.append(dict(id=spec['id'],state=state,action=spec['action'],metric=spec['metric'],threshold=spec['threshold'],
                          evidence=evidence,owner=spec['owner'],rationale=spec['rationale'],calibration=spec['calibration']))
    return dict(metrics=metrics,rules=rules,generations=generations,errors=errors)


def ingest(store,run,task,token,raw,*,terminal=False):
    """Accept only a monotonic append-only prefix under the current fenced lease."""
    record=store.get(run); row=next(t for t in store.tasks(run) if t['id']==task)
    if record['status']!='running' or row['status']!='running' or row['token']!=token or row['lease_until']<=time.time(): return False
    attempt=row['attempts']
    old=store.db.execute('SELECT * FROM ml_diagnostic_attempts WHERE run_id=? AND task_id=? AND attempt=?',(run,task,attempt)).fetchone()
    packet=data.parse(old['packet']); p=packet['policy']
    try:
        data.require(type(raw) is bytes and len(raw)<=p['max_bytes'] and len(raw)>=old['byte_count'])
        data.require(data.sha(raw[:old['byte_count']])==old['stream_sha256'])
        end=raw.rfind(b'\n')+1
        data.require(not terminal or end==len(raw))
        lines=raw[old['byte_count']:end].splitlines(); previous=store.db.execute('SELECT COUNT(*) FROM ml_diagnostic_events WHERE run_id=? AND task_id=? AND attempt=?',(run,task,attempt)).fetchone()[0]
        data.require(previous+len(lines)<=p['max_events'])
        for i,line in enumerate(lines):
            data.require(len(line)<=data.MAX_LINE)
            event=data.parse(line); event_valid(event,packet); data.require(event['sequence']==previous+i+1)
            last=store.db.execute('SELECT payload FROM ml_diagnostic_events WHERE run_id=? AND task_id=? AND attempt=? ORDER BY sequence DESC LIMIT 1',(run,task,attempt)).fetchone()
            data.require(last is None or event['step']>=data.parse(last['payload'])['step'])
            store.db.execute('INSERT INTO ml_diagnostic_events VALUES(?,?,?,?,?)',(run,task,attempt,event['sequence'],data.canonical(event)))
        store.db.execute('UPDATE ml_diagnostic_attempts SET byte_count=?,stream_sha256=?,last_event=? WHERE run_id=? AND task_id=? AND attempt=?',
                         (end,data.sha(raw[:end]),time.time() if lines else old['last_event'],run,task,attempt))
        result=analyze(p,[e for e in all_events(store,run,task) if e['attempt']==attempt])
        stops=[x for x in result['rules'] if x['state']=='triggered' and x['action']=='stop_training']
        hard=any(e!='nonfinite_derived_metric' for e in result['errors'])
        if hard or stops:
            store.fail_run(run,'ml_diagnostics_stop'); return False
        if not terminal and time.time()-(time.time() if lines else old['last_event'])>p['max_gap_seconds']:
            store.fail_run(run,'ml_diagnostics_stale'); return False
        return True
    except (ValueError,KeyError,TypeError,UnicodeError):
        store.db.execute('UPDATE ml_diagnostic_attempts SET error=? WHERE run_id=? AND task_id=? AND attempt=?',('invalid_stream',run,task,attempt))
        store.fail_run(run,'ml_diagnostics_invalid'); return False


def poll(store,run,task,token,*,terminal=False,raw=None):
    with store.transaction():
        row=next(t for t in store.tasks(run) if t['id']==task)
        attempt=store.db.execute('SELECT packet FROM ml_diagnostic_attempts WHERE run_id=? AND task_id=? AND attempt=?',(run,task,row['attempts'])).fetchone()
        if attempt is None: return True
        packet=data.parse(attempt['packet'])
        remote=raw is not None
        if raw is None:
            path=Path(packet['directory'])/'events.jsonl'
            if path.exists():
                with data.regular(path) as stream: raw=stream.read(packet['policy']['max_bytes']+1)
            else: raw=b''
        result=ingest(store,run,task,token,raw,terminal=terminal)
        if remote and (result or store.get(run)['reason']=='ml_diagnostics_stop'):
            atomic(Path(packet['directory'])/'events.jsonl',raw)
        return result


def stream_subject(policy,task='ml-fit',checkpoint=None):
    """Verifier reconstructs raw stream, never trusts a JSON PASS flag."""
    if 'diagnostics' not in policy: return None
    roots=sorted((Path(policy['artifact_root'])/'diagnostics'/task).glob('attempt-*'),key=lambda p:int(p.name[8:]))
    data.require(bool(roots)); root=roots[-1]
    packet=data.load(root/'manifest.json'); p=validate_policy(policy['diagnostics'])
    data.require(packet['policy']==p and packet['policy_sha256']==data.digest(p) and packet['pipeline_id']==policy['pipeline_id'])
    events,raw_sha,_=data.rows(root/'events.jsonl')
    data.require(len(events)<=p['max_events'] and (root/'events.jsonl').stat().st_size<=p['max_bytes'])
    data.require(packet['task_id']==task and packet['attempt']==int(root.name[8:]))
    for i,e in enumerate(events):
        event_valid(e,packet); data.require(e['sequence']==i+1 and (i==0 or e['step']>=events[i-1]['step']))
    result=analyze(p,events)
    data.require(not result['errors'] and not any(x['state'] in ('triggered','missing','warming_up','insufficient_data') and x['action']!='observe' for x in result['rules']))
    for metric,spec in p['metrics'].items():
        if spec['required']:
            data.require(any(m['metric']==metric and m['split']=='validation' and m['slice']=='all' and (checkpoint is None or m['subject']==checkpoint) for m in result['metrics']))
    if p['required_generations']:
        for probe in p['probes']:
            matches=[g for g in result['generations'] if g['payload']['probe_id']==probe['id']]
            data.require(any(g['step']==0 for g in matches))
            data.require(any(g['subject']==checkpoint and g['validation']['complete'] and g['validation']['format_valid'] is not False for g in matches))
    return data.digest(dict(policy=data.digest(p),stream=raw_sha))


def report_info(policy):
    root=Path(policy['artifact_root'])/'reports'
    try:
        pointer=data.load(root/'latest.json'); digest=pointer['report_sha256']
        data.require(isinstance(digest,str) and bool(SHA.fullmatch(digest)))
        directory=root/digest
        manifest=data.load(directory/'manifest.json')
        data.require(set(('report.json','report.md','metrics.csv','plot.svg','generations.jsonl','gallery.md')).issubset(manifest['files']))
        for name,checksum in manifest['files'].items():
            data.require(not Path(name).is_absolute() and '..' not in Path(name).parts)
            with data.regular(directory/name) as stream: raw=stream.read(data.MAX_BYTES+1)
            data.require(len(raw)<=data.MAX_BYTES and data.sha(raw)==checksum)
        report=data.load(directory/'report.json',data.MAX_BYTES)
        data.require(report['report_sha256']==digest==data.digest({k:v for k,v in report.items() if k!='report_sha256'}))
        return dict(status=report['report_status'],path=str(directory/'report.json'),report_sha256=digest,
                    training_outcome=report['training_outcome'],preprint=str(directory/'preprint/main.tex') if (directory/'preprint/main.tex').exists() else None)
    except FileNotFoundError: return dict(status='not_available')
    except (OSError,ValueError,KeyError,TypeError): return dict(status='stale')


def refresh(store,run):
    record=store.get(run);flow=json.loads(record['workflow']); policy=flow.get('ml_policy')
    if not policy: return None
    from .ml_resources import report as resource_report
    from .accounting import usage_report
    p=policy.get('diagnostics'); events=all_events(store,run)
    analyses=[]
    for row in store.db.execute('SELECT * FROM ml_diagnostic_attempts WHERE run_id=? ORDER BY task_id,attempt',(run,)):
        selected=[e for e in events if e['task_id']==row['task_id'] and e['attempt']==row['attempt']]
        try:
            result=analyze(p,selected) if p else dict(metrics=[],rules=[],generations=[],errors=[])
        except (ValueError,KeyError,TypeError):
            result=dict(metrics=[],rules=[],generations=[],errors=['invalid_committed_events'])
        if row['error']:result['errors'].append(row['error'])
        packet=data.parse(row['packet']); path=Path(packet['directory'])/'events.jsonl'
        try:
            with data.regular(path) as stream: raw=stream.read(packet['policy']['max_bytes']+1)
            if len(raw)!=row['byte_count'] or data.sha(raw)!=row['stream_sha256']: result['errors'].append('uncommitted_or_changed_stream')
        except OSError: result['errors'].append('missing_stream')
        analyses.append(dict(task_id=row['task_id'],attempt=row['attempt'],started=row['started'],last_event=row['last_event'],**result))
    tasks=store.tasks(run); fit=next(t for t in tasks if t['id']=='ml-fit')
    expired=any(t['status']=='running' and (t['lease_until'] or 0)<time.time() for t in tasks)
    resources=resource_report(store,record,flow)
    resource_unknown=any(x['state'] not in ('complete','awaiting_billing') for x in resources['attempts'])
    outcome='completed' if fit['status']=='verified' else ('not_started' if fit['attempts']==0 else
            ('unknown' if expired or resource_unknown else ('failed' if record['status']=='failed' else
            ('stopped' if record['status']=='cancelled' else 'unknown'))))
    missing=[]
    if p:
        for name,spec in p['metrics'].items():
            if spec['required'] and not any(m['metric']==name and m['split']=='validation' for a in analyses for m in a['metrics']):missing.append('metric:'+name)
        if p['required_generations']:
            for probe in p['probes']:
                if not any(g['payload']['probe_id']==probe['id'] for a in analyses for g in a['generations']):missing.append('generation:'+probe['id'])
    else: missing.append('diagnostics_not_configured')
    errors=[e for a in analyses for e in a['errors']]
    verification=('stale' if errors else 'verified') if record['status']=='verified' else 'not_run'
    if p and fit['status']=='verified':
        try:
            from .ml_artifacts import checkpoint_hash
            stream_subject(policy,checkpoint=checkpoint_hash(policy))
        except (OSError,ValueError,KeyError,TypeError):errors.append('diagnostic_subject_changed');verification='stale'
    evaluation=None
    if any(t['id']=='ml-evaluate' and t['status']=='verified' for t in tasks):
        try:
            from .ml_artifacts import evaluation as evaluate
            evaluation=evaluate(record['workspace'],policy)
        except (OSError,ValueError,KeyError,TypeError): errors.append('evaluation_changed');verification='stale'
    terminal=record['status'] in ('verified','failed','cancelled','needs_input') or expired
    lineage={}; prefix_digest=None
    if all(next(t for t in tasks if t['id']=='ml-'+stage)['status']=='verified' for stage in ('hypotheses','plan','model','data','cost','train','benchmark')):
        try:
            from .ml_artifacts import validate_prefix
            prefix=validate_prefix(record['workspace'],policy);lineage=prefix['lineage'];prefix_digest=prefix['digest']
        except (OSError,ValueError,KeyError,TypeError):errors.append('planning_lineage_changed');verification='stale'
    checkpoint_summary=dict(last_verified=None,best_selected=None)
    if fit['status']=='verified':
        from .ml_artifacts import checkpoint_hash
        try: checkpoint_summary['last_verified']=checkpoint_hash(policy)
        except (OSError,ValueError,KeyError,TypeError): errors.append('checkpoint_changed')
    report=dict(lineage=lineage,prefix_sha256=prefix_digest,checkpoints=checkpoint_summary,diagnostics_policy=p,schema_version=1,artifact_type='ml-training-report',pipeline_id=policy['pipeline_id'],run_id=run,
        context_sha256=policy['context_sha256'],diagnostics_sha256=data.digest(p) if p else None,
        training_outcome=outcome,run_status=record['status'],reason='expired_lease_unknown_outcome' if expired else record['reason'],
        report_status='complete' if terminal and not missing and not errors and not resource_unknown else 'partial',
        verification_status=verification,terminal=terminal,started=record['created'],
        benchmark_verdict=evaluation['verdict'] if evaluation else 'not_run',evaluation=evaluation,
        metrics=[m for a in analyses for m in a['metrics']],heuristics=[dict(x,task_id=a['task_id'],attempt=a['attempt']) for a in analyses for x in a['rules']],
        generations=[g for a in analyses for g in a['generations']],attempts=analyses,missing=missing,errors=errors,
        costs=dict(resources=resources,ai=usage_report(flow,store.usage_rows(run),tasks)),
        limitations=['Task metrics are declared trainer observations; semantic quality requires independent evaluation.',
                     'Synthetic fixtures are not LLM quality or operational SLA.', 'Missing final generation does not trigger a paid rerun.'])
    digest=data.digest(report);report['report_sha256']=digest
    root=Path(policy['artifact_root'])/'reports'; root.mkdir(mode=0o700,exist_ok=True)
    directory=root/digest
    if not directory.exists():
        completed=directory
        directory=root/(digest+'.partial-'+uuid.uuid4().hex)
        directory.mkdir(mode=0o700)
        try:
            outputs=render(report)
            data.require(sum(len(v) for v in outputs.values())<=data.MAX_BYTES)
            for name,content in outputs.items(): atomic(directory/name,content)
            if p and p['preprint'] and terminal:
                from scripts.science_preprint import build
                build(directory/'report.json',directory/'preprint',title='Experiment '+policy['pipeline_id'])
                for child in (directory/'preprint').iterdir(): outputs[child.relative_to(directory).as_posix()]=data.read_bytes(child)
            atomic(directory/'manifest.json',(data.canonical(dict(files={k:data.sha(v) for k,v in outputs.items()}))+'\n').encode())
            if not completed.exists(): directory.rename(completed)
            directory=completed
        except Exception:
            # Preserve partial outputs; no latest pointer is published for an incomplete revision.
            raise
    data.require((directory/'manifest.json').is_file())
    atomic(root/'latest.json',(data.canonical(dict(report_sha256=digest))+'\n').encode())
    return report_info(policy)


def render(report):
    rows=['metric,task,attempt,step,split,slice,value,support,perplexity,perplexity_status']
    for m in report['metrics']:
        import csv,io
        stream=io.StringIO();csv.writer(stream).writerow([m['metric'],m['task_id'],m['attempt'],m['step'],m['split'],m['slice'],m['value'],m['support'],m.get('perplexity'),m.get('perplexity_status')])
        rows.append(stream.getvalue().strip())
    md=['# Training / validation report','', 'Outcome: '+report['training_outcome'],
        'Run: '+report['run_status']+'; reason: '+report['reason'], 'Report: '+report['report_status']+'; verification: '+report['verification_status'],
        'Benchmark: '+report['benchmark_verdict'],'','## Metrics','',
        '| Metric | Phase/attempt | Step | Split/slice | Value | Support | PPL | PPL status |','| --- | --- | --- | --- | --- | --- | --- | --- |']
    for m in report['metrics']:
        md.append('| '+ ' | '.join(str(v).replace('|','&#124;').replace('\n',' ') for v in [m['metric'],m['task_id']+'/'+str(m['attempt']),m['step'],m['split']+'/'+m['slice'],m['value'],m['support'],m.get('perplexity'),m.get('perplexity_status')])+' |')
    md+=['','## Heuristics','']+[x['id']+': '+x['state']+'; action='+x['action'] for x in report['heuristics']]
    md+=['','## Missing / errors','',str(report['missing']),str(report['errors']),'','## Cost / budget','',
         'Authoritative receipts: report.json costs; estimates/provider reports/invoices remain separate. No budget reset.','',
         '## Behavior snapshots','',str(len(report['generations']))+' full private outputs in generations.jsonl and gallery.md.',
         '','## Limitations','']+report['limitations']
    gallery=['# Private paired generation snapshots','']
    for g in report['generations']:
        content=g['payload']['output']; runs=[len(x) for x in re.findall(r'`+',content)]; fence='`'*max([3]+[x+1 for x in runs])
        gallery += [g['payload']['probe_id']+' / step '+str(g['step'])+' / '+g['subject'],
                    'finish='+g['payload']['finish_cause']+' / '+data.canonical(g['validation']),fence,content,fence,'']
    # Separate polyline per metric/split/attempt; gaps are never filled with invented zeros.
    series={}
    for m in report['metrics']:
        series.setdefault((m['metric'],m['split'],m['task_id'],m['attempt']),[]).append(m)
        if m.get('perplexity') is not None:
            series.setdefault((m['metric']+'.ppl',m['split'],m['task_id'],m['attempt']),[]).append(dict(m,value=m['perplexity']))
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="'+str(max(150,150*len(series)))+'">']
    for i,(key,points) in enumerate(series.items()):
        lo=min(x['value'] for x in points);hi=max(x['value'] for x in points);xmax=max(1,max(x['step'] for x in points))
        coords=' '.join(str(40+700*m['step']/xmax)+','+str(130+i*150-90*(m['value']-lo)/(hi-lo or 1)) for m in points)
        svg += ['<text x="20" y="'+str(20+i*150)+'">'+html.escape(str(key))+'</text>',
                '<polyline fill="none" stroke="#2563eb" points="'+coords+'"/>',
                '<text x="20" y="'+str(145+i*150)+'">step; range '+html.escape(str(lo)+'..'+str(hi))+'</text>']
    svg.append('</svg>')
    return {'report.json':(data.canonical(report)+'\n').encode(),'report.md':('\n'.join(md)+'\n').encode(),
            'metrics.csv':('\n'.join(rows)+'\n').encode(),'plot.svg':''.join(svg).encode(),
            'generations.jsonl':''.join(data.canonical(g)+'\n' for g in report['generations']).encode(),
            'gallery.md':('\n'.join(gallery)+'\n').encode()}
