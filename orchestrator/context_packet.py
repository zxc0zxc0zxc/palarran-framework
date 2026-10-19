"""Deterministic source-grounded stage packets; no LLM summaries or new market facts."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from .product_artifacts import STAGES, canonical_sha, load_json, pipeline_dir, read_bytes, safe_path, validate_stage


def packet(root, pipeline, stage, context_sha, skills_root, route):
    root=Path(root).resolve();skills_root=Path(skills_root).resolve()
    directory=pipeline_dir(root,pipeline);relative=directory.relative_to(root).as_posix()
    if stage not in STAGES[1:]: raise ValueError('Packet requires saved hypothesis')
    prefix=STAGES[:STAGES.index(stage)]
    validate_stage(root,pipeline,prefix[-1],context_sha,skills_root)
    profiles=[stage if stage!='mvp' else 'define']
    if route not in ('b2b','b2c'):raise ValueError('Explicit buyer route required')
    if stage=='acquisition':profiles += [route]
    sources=set()
    for profile in profiles:
        skill=skills_root/'skills'/('product-'+profile)/'SKILL.md';sources.add(skill)
        for link in re.findall(r'(?<!!)\[[^\]]*\]\(([^)\s]+)\)',skill.read_text()):
            if link.startswith(('https:', 'http:', '#')):continue
            source=(skill.parent/link.split('#',1)[0]).resolve()
            if not source.is_relative_to(skills_root) or source.suffix!='.md':raise ValueError('Unsafe source guide')
            if '/skills/product-' in str(source) and source!=skill:continue
            sources.add(source)
    text=['# Verified materialized context: '+stage,
          'Complete pinned mandatory source guides below: read this packet once; do not reread identical guides. Canonical original files remain authoritative.',
          'Upstream index preserves claims/classifications/IDs/source URLs. Before extending an inherited numeric claim, inspect its full original evidence record on demand. Do not promote hypotheses or regenerate the chosen product.',
          'Existing define is immutable. Web research is read-only. No apps/outreach/ads/accounts/build. Minimize tool rounds: batch related source queries and file reads; keep report concise.']
    for source in sorted(sources):
        name=source.relative_to(skills_root).as_posix();data=read_bytes(skills_root,name,262144)
        text += ['\n## Source '+name+' SHA256 '+hashlib.sha256(data).hexdigest(), data.decode()]
    index=[]
    for name in prefix:
        manifest=load_json(root,relative+'/stages/'+name+'/stage.json')
        index.append(dict(stage=name,manifest_sha256=canonical_sha(manifest),report=manifest['report'],
            claims=manifest['claims'],unknowns=manifest['unknowns'],decisions=manifest['decisions'],
            evidence=[{k:e[k] for k in ('id','claim','classification','source_url','retrieved_at','confidence','value_or_range','unit','input_ids')} for e in manifest['evidence']]))
    text+=['\n## Canonical prefix index (full records on demand)',json.dumps(index,ensure_ascii=False,indent=2)]
    text+=['\n## Chosen product brief (exact saved report)',read_bytes(root,relative+'/stages/define/report.md',262144).decode()]
    data=('\n'.join(text)+'\n').encode()
    if len(data)>196608:raise ValueError('Context packet too large; narrow scope explicitly')
    return relative+'/capsules/'+stage+'.md',data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('root','pipeline','stage','context-sha','skills-root'):parser.add_argument('--'+key,required=True)
    parser.add_argument('--route',choices=('b2b','b2c'),required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    try:
        name,data=packet(args.root,args.pipeline,args.stage,args.context_sha,args.skills_root,args.route)
        path=safe_path(args.root,name)
        if args.check:
            if read_bytes(args.root,name,196608)!=data:raise ValueError('Packet drift')
        elif path.exists():
            if path.read_bytes()!=data:raise ValueError('Existing packet differs')
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    except (OSError,ValueError,KeyError,TypeError):
        parser.exit(2,'Product context packet: FAIL\n')
    print('PASS '+hashlib.sha256(data).hexdigest())


if __name__=='__main__':main()
