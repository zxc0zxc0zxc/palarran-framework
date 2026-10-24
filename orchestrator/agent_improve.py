"""Reviewed skill improvement packets and paired native eval evidence. No dispatch."""
import argparse
import copy
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

from . import agent_eval as ev
from .accounting import nano, usd

SELF=Path(__file__).resolve()
SIDES=('baseline','candidate')
OUTCOMES={'PASS','FAIL'}


def require(value):
    if not value:raise ValueError('Improvement contract rejected')


def path(value):
    p=Path(value);require(p.is_absolute() and p.resolve(strict=True)==p)
    require(not any(x.is_symlink() for x in (p,)+tuple(p.parents)));return p


def text(value,limit=4096):
    require(isinstance(value,str) and 0<len(value)<=limit and not any(ord(c)<32 and c not in '\n\t' for c in value))


def ident(value):ev.identifier(value);require(len(value)<=24)


def sha(value):return hashlib.sha256(value).hexdigest()


def file_digest(name):
    import os
    import stat
    p=path(name);h=hashlib.sha256();size=0
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode))
        while True:
            raw=stream.read(1048576)
            if not raw:break
            size+=len(raw);require(size<=512*1048576);h.update(raw)
    return h.hexdigest()


def write(p,raw):
    with p.open('xb') as stream:stream.write(raw)
    p.chmod(0o600)


def transformed(template,side,case,packet,skills):
    suite=copy.deepcopy(template);suite['candidate']=side
    suite['id']='improve_'+template['id']+'_'+case['id']
    c=copy.deepcopy(case);task=c['task'];adapter=task.get('adapter','command')
    if adapter=='command':
        require(isinstance(task.get('argv'),list) and task['argv'].count('{skill}')==1)
        task['argv']=[str(packet/(side+'.txt')) if a=='{skill}' else a for a in task['argv']]
        require(not any('{skill}' in a for a in task['argv']))
    else:
        require(isinstance(task.get('prompt'),str) and task['prompt'].count('{skill}')==1)
        task['prompt']=task['prompt'].replace('{skill}',skills[side])
    suite['cases']=[c]
    # Native per-stage budgets retain the same original cap for the selected case.
    if 'usage_policy' in suite:
        suite['usage_policy']['stages']={case['id']:suite['usage_policy']['stages'][case['id']]}
    return suite


def prepare(source,target,output):
    source=path(source);target=path(target);require(target.is_dir())
    out=Path(output).absolute();require(out.parent.resolve(strict=True)==out.parent and not out.exists() and not out.is_symlink())
    require(not ev.inside(out,target) and not ev.inside(target,out))
    v=ev.load(source)
    ev.fields(v,('version','id','incident','baseline_skill','candidate_skill','regression_cases','control_cases','suite'))
    require(type(v['version']) is int and v['version']==1);ident(v['id'])
    incident=v['incident'];ev.fields(incident,('summary','feedback','evidence'))
    text(incident['summary']);text(incident['feedback']);require(isinstance(incident['evidence'],list) and 1<=len(incident['evidence'])<=32)
    evidence_ids=set()
    for e in incident['evidence']:
        ev.fields(e,('id','kind','sha256','summary'));ident(e['id']);require(e['id'] not in evidence_ids);evidence_ids.add(e['id']);text(e['summary'])
        require(e['kind'] in ('user_report','sanitized_trace','tool_result'))
        require((e['sha256'] is None and e['kind']=='user_report') or (isinstance(e['sha256'],str) and bool(re.fullmatch('[0-9a-f]{64}',e['sha256']))))
    reg=v['regression_cases'];controls=v['control_cases']
    for group in (reg,controls):
        require(isinstance(group,list) and bool(group))
        for c in group:ident(c)
    ids=reg+controls;require(len(ids)==len(set(ids)) and len(ids)<=20)
    template=v['suite'];ident(template['id'])
    require(len(template['cases'])==len(ids) and {c['id'] for c in template['cases']}==set(ids))
    for c in template['cases']:ident(c['id'])
    require(len({c['task'].get('adapter','command')=='command' for c in template['cases']})==1)
    skills={s:ev.regular_bytes(path(v[s+'_skill']),65536).decode('utf-8') for s in SIDES}
    require(all(skills.values()) and skills['baseline']!=skills['candidate'])
    artifacts={s+'.txt':skills[s].encode() for s in SIDES}
    lines=difflib.unified_diff(skills['baseline'].splitlines(True),skills['candidate'].splitlines(True),fromfile='baseline/SKILL.md',tofile='candidate/SKILL.md')
    artifacts['candidate.diff']=''.join(line if line.endswith('\n') else line+'\n\\ No newline at end of file\n' for line in lines).encode()
    require(bool(artifacts['candidate.diff']))
    pins={str(SELF):sha(ev.regular_bytes(SELF)),ev.HARNESS:sha(ev.regular_bytes(ev.HARNESS))}
    suites={}
    for side in SIDES:
        suites[side]={}
        for c in template['cases']:
            suite=transformed(template,side,c,out,skills)
            normalized=ev.normalize(suite,target,out/'unused-state')
            ev.workflow(normalized,out/'admission.json','0'*64)
            for check in normalized['cases'][0]['checks']:
                if check['kind']=='command':pins.update(check['pins'])
            task=suite['cases'][0]['task']
            refs=task.get('argv',[])+[task['executable']] if 'executable' in task else task.get('argv',[])
            refs+=suite['policy']['executables']
            for ref in refs:
                if isinstance(ref,str) and Path(ref).is_absolute() and Path(ref).is_file():
                    pins[str(path(ref))]=file_digest(ref)
            name=side+'-'+c['id']+'.json';artifacts[name]=(ev.canonical(suite)+'\n').encode();suites[side][c['id']]=name
    hashes={k:sha(raw) for k,raw in artifacts.items()}
    manifest=dict(version=1,id=v['id'],target=str(target),input_sha256=sha(ev.regular_bytes(source)),incident=incident,
                  regression_cases=reg,control_cases=controls,suites=suites,artifacts=hashes,pins=pins)
    manifest['sha256']=ev.digest(manifest)
    raw=(ev.canonical(manifest)+'\n').encode();require(len(raw)+sum(map(len,artifacts.values()))<=2097152)
    out.mkdir(mode=0o700)
    for name,content in artifacts.items():write(out/name,content)
    write(out/'packet.json',raw)
    return dict(packet=str(out),packet_sha256=manifest['sha256'],cases=len(ids),model_calls=0)


def frozen(packet):
    packet=path(packet);m=ev.load(packet/'packet.json')
    require(m['sha256']==ev.digest({k:v for k,v in m.items() if k!='sha256'}))
    for name,h in m['artifacts'].items():
        require(Path(name).name==name and sha(ev.regular_bytes(packet/name))==h)
    for name,h in m['pins'].items():require(file_digest(name)==h)
    return m


def without_carry(suite):
    value=copy.deepcopy(suite)
    if 'usage_policy' in value:value['usage_policy'].pop('carry',None)
    return value


def contexts(report):
    return [{k:c[k] for k in ('task_id','mode','retrieval','scopes','refs','packet_sha256')} for c in report['context']]


def accounting(reports,cap):
    # Native current observed costs exclude carry. Keep each historical source once.
    carries={};unknown=False;observed_tokens=observed_cost=reserved_tokens=reserved_cost=0
    sources={};all_model=bool(reports) and all(r['sample_kind']=='model' for r in reports)
    for r in reports:
        u=r['usage'];key='agent-improve/'+r['run_id']
        if r['sample_kind']!='model':continue
        sources[key]=dict(source=key,observed_tokens=u.get('total_tokens'),observed_cost_usd=u.get('cost_usd'),
            reserved_tokens=u['reserved_total_tokens']-sum(x['reserved_tokens'] for x in u.get('carry',[])),
            reserved_cost_usd=usd(nano(u['reserved_total_cost_usd'])-sum(nano(x['reserved_cost_usd']) for x in u.get('carry',[]))),unknown=not u['complete'])
        observed_tokens+=u['observed_tokens'];observed_cost+=nano(u['observed_cost_usd'])
        reserved_tokens+=sources[key]['reserved_tokens'];reserved_cost+=nano(sources[key]['reserved_cost_usd'])
        unknown|=not u['complete']
        for entry in u.get('carry',[]):
            old=carries.get(entry['source']);require(old is None or old==entry);carries[entry['source']]=entry
    for name,e in carries.items():
        if name in sources:require(e==sources[name]);continue
        reserved_tokens+=e['reserved_tokens'];reserved_cost+=nano(e['reserved_cost_usd']);unknown|=e['unknown']
    safe=None if not all_model else (not unknown and reserved_tokens<=cap['max_tokens'] and reserved_cost<=nano(cap['max_cost_usd']))
    return dict(complete=all_model and not unknown,budget_safe=safe,observed_tokens=observed_tokens if all_model else None,
                observed_cost_usd=usd(observed_cost) if all_model else None,reserved_total_tokens=reserved_tokens if all_model else None,
                reserved_total_cost_usd=usd(reserved_cost) if all_model else None,carry_sources=len(carries),invoice_usd=None)


def compare(packet,proofs):
    packet=path(packet);m=frozen(packet);links=ev.load(path(proofs));ev.fields(links,SIDES)
    ids=m['regression_cases']+m['control_cases'];seen=set();rows=[];reports={s:[] for s in SIDES};suites=[];missing=False
    for side in SIDES:require(isinstance(links[side],dict) and set(links[side])<=set(ids))
    for cid in ids:
        row=dict(id=cid,group='regression' if cid in m['regression_cases'] else 'control');pair=[]
        for side in SIDES:
            ref=links[side].get(cid)
            if ref is None:row[side]='NOT_RUN';missing=True;continue
            ev.fields(ref,('state','run'));state=path(ref['state']);ev.identifier(ref['run'])
            require(not ev.inside(state,Path(m['target'])) and not ev.inside(Path(m['target']),state))
            require(ref['run'] not in seen);seen.add(ref['run'])
            _,_,bundle=ev.binding(state,ref['run']);r=ev.report(state,ref['run'])
            expected=ev.normalize(ev.load(packet/m['suites'][side][cid]),Path(m['target']),state)
            require(without_carry(bundle['suite'])==without_carry(expected))
            # Carry can grow but never remove or alter the original historical entries.
            original=expected.get('usage_policy',{}).get('carry',[]);actual=bundle['suite'].get('usage_policy',{}).get('carry',[])
            require(all(e in actual for e in original))
            require(r['total_cases']==1 and r['cases'][0]['id']==cid)
            row[side]=r['cases'][0]['verdict'];row[side+'_run']=r['run_id']
            u=r['usage']
            row[side+'_measurement']=dict(subject=r['subject'],attempts=r['cases'][0]['attempts'],execution_seconds=r['execution_seconds'],grader_seconds=r['grader_seconds'],
                sample_kind=r['sample_kind'],usage={k:u.get(k) for k in ('complete','total_tokens','cost_usd','cost_source','observed_tokens','observed_cost_usd','observed_counters')})
            reports[side].append(r);suites.append(expected);pair.append(r)
        comparable=len(pair)==2 and all(r['cases'][0]['verdict'] in OUTCOMES for r in pair)
        if comparable:
            comparable=all(pair[0][key]==pair[1][key] for key in ('environment','harness_sha256','baseline','requested_profiles','sample_kind')) and contexts(pair[0])==contexts(pair[1])
        row['comparable']=comparable
        if not comparable:missing=True
        rows.append(row)
    all_reports=reports['baseline']+reports['candidate']
    model=bool(all_reports) and all(r['sample_kind']=='model' for r in all_reports)
    cap=next((s['usage_policy'] for s in suites if 'usage_policy' in s),None)
    usage=accounting(all_reports,cap)
    baseline_pass=sum(r['baseline']=='PASS' for r in rows);candidate_pass=sum(r['candidate']=='PASS' for r in rows)
    regressions=[r['id'] for r in rows if r['baseline']=='PASS' and r['candidate']=='FAIL']
    fixes=[r['id'] for r in rows if r['baseline']=='FAIL' and r['candidate']=='PASS']
    reg_fixed=all(r['baseline']=='FAIL' and r['candidate']=='PASS' for r in rows if r['group']=='regression')
    controls_ok=all(r['baseline']==r['candidate']=='PASS' for r in rows if r['group']=='control')
    recommendation='insufficient_evidence'
    if not missing:
        if regressions or not reg_fixed or not controls_ok:recommendation='rejected'
        elif model and usage['budget_safe']:recommendation='review_candidate'
        elif not model:recommendation='review_fixture'
    delta=None
    if not missing and model and usage['complete'] and usage['budget_safe']:
        delta=dict(tokens=sum(r['usage']['total_tokens'] for r in reports['candidate'])-sum(r['usage']['total_tokens'] for r in reports['baseline']),
                   cost_nano_usd=sum(nano(r['usage']['cost_usd']) for r in reports['candidate'])-sum(nano(r['usage']['cost_usd']) for r in reports['baseline']))
    frozen(packet)
    return dict(version=1,packet_sha256=m['sha256'],sample_kind='model' if model else 'fixture' if all_reports else 'not_run',recommendation=recommendation,
        baseline_skill_sha256=m['artifacts']['baseline.txt'],candidate_skill_sha256=m['artifacts']['candidate.txt'],diff_sha256=m['artifacts']['candidate.diff'],
        compared_cases=sum(r['comparable'] for r in rows),coverage=sum(r['comparable'] for r in rows)/len(rows),
        trials_per_case=1,quality_scope='declared_grader_only',cases=rows,total_cases=len(ids),baseline_pass=baseline_pass,candidate_pass=candidate_pass,
        quality_delta=candidate_pass-baseline_pass if not missing else None,fixes=fixes,regressions=regressions,usage=usage,efficiency_delta=delta,
        execution_seconds={s:sum(r['execution_seconds'] for r in reports[s]) for s in SIDES},
        grader_seconds={s:sum(r['grader_seconds'] for r in reports[s]) for s in SIDES},model_calls_launched=0)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--input',type=Path,required=True);p.add_argument('--target',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('compare');p.add_argument('--packet',type=Path,required=True);p.add_argument('--proofs',type=Path,required=True)
    a=parser.parse_args(argv)
    try:
        result=prepare(a.input,a.target,a.output) if a.command=='prepare' else compare(a.packet,a.proofs)
        print(ev.canonical(result));return 0
    except (ValueError,OSError,KeyError,TypeError,UnicodeError,IndexError):
        parser.exit(2,'Improvement packet/evidence rejected; inspect approved private inputs.\n')

if __name__=='__main__':raise SystemExit(main())
