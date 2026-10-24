#!/usr/bin/env python3
"""Export a self-contained evidence draft; never run training, a model or TeX commands."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import argparse
import csv
import io
import os
from pathlib import Path
import sys

if __package__ in (None,''): sys.path.insert(0,str(repository_root(__file__)))
from scripts import ml_data as data


def tex(value):
    replacements={'\\':r'\textbackslash{}','{':r'\{','}':r'\}','$':r'\$','&':r'\&','#':r'\#','%':r'\%','_':r'\_','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(replacements.get(c,c) for c in str(value) if ord(c)>=32 or c=='\n')


def build(report_path,output,*,title='Experiment report',author=None):
    raw=data.read_bytes(report_path)
    report=data.parse(raw)
    data.require(report['artifact_type']=='ml-training-report' and report['schema_version']==1)
    expected=report['report_sha256']
    data.require(expected==data.digest({k:v for k,v in report.items() if k!='report_sha256'}))
    data.text(title,512)
    if author is not None: data.text(author,512)
    output=Path(output).absolute()
    data.require(output.parent.resolve()==output.parent and not output.exists() and not output.is_symlink())
    metrics=report['metrics'];data.require(isinstance(metrics,list) and len(metrics)<=10000)
    # No arbitrary macros, paths, bibliography commands, samples or raw model outputs copied.
    lines=[r'\documentclass[11pt]{article}',r'\usepackage[utf8]{inputenc}',r'\usepackage[T1]{fontenc}',
           r'\usepackage{longtable}',r'\usepackage[margin=1in]{geometry}',r'\title{'+tex(title)+'}',
           r'\author{'+tex(author or 'Author metadata not provided')+'}',r'\date{}',r'\begin{document}',r'\maketitle',
           r'\begin{abstract}',tex('Evidence draft generated from one recorded experiment. Training outcome: '+report['training_outcome']+
             '; report completeness: '+report['report_status']+'. No claim of novelty, significance or peer review is made.'),r'\end{abstract}',
           r'\section{Question and hypothesis}', 'The research question and preregistered hypothesis must be supplied from the approved experiment specification.',
           r'\section{Methods and experimental setup}', 'Reported identifiers bind the observations to their source. The trainer and task-specific protocol require separate scientific review.',
           r'\begin{itemize}', r'\item Context digest: \texttt{'+tex(report['context_sha256'])+'}',
           r'\item Diagnostics digest: \texttt{'+tex(report.get('diagnostics_sha256') or 'not configured')+'}',r'\end{itemize}',
           r'\section{Results}',tex('Run status: '+report['run_status']+'; stop/failure reason: '+report['reason']+
             '; benchmark verdict: '+report['benchmark_verdict']+'; verification: '+report['verification_status']+'.'),
           r'\begin{longtable}{p{0.30\linewidth}p{0.15\linewidth}rr}',r'Metric / split & Step & Value & Support \\ \hline']
    evidence=[]; csv_stream=io.StringIO(); writer=csv.writer(csv_stream);writer.writerow(['metric','split','step','value','support','subject'])
    for i,m in enumerate(metrics):
        data.require(isinstance(m,dict))
        lines.append(tex(m['metric']+' / '+m['split'])+' & '+tex(m['step'])+' & '+tex(m['value'])+' & '+tex(m['support'])+r' \\')
        writer.writerow([m['metric'],m['split'],m['step'],m['value'],m['support'],m['subject']])
        evidence.append(dict(claim_id='RESULT-'+str(i+1),report_sha256=expected,source_pointer='/metrics/'+str(i),subject=m['subject']))
    lines += [r'\end{longtable}',r'\section{Training diagnostics and behavior}',
              tex(str(len(report['generations']))+' recorded generation observations. Private full outputs are not copied into this article. A permitted, paired example selection requires review.'),
              r'\section{Failure modes and limitations}',tex('Missing evidence: '+str(report['missing'])+'. Errors: '+str(report['errors'])+'.')]
    for limitation in report['limitations']: lines.append(tex(limitation))
    lines += [r'\section{Compute and reproducibility}',
              'Financial values retain their original estimated, provider-reported and unresolved accounting basis in the source report; no new training was performed for this export.',
              r'\section{Related work}', 'No references are fabricated. Verified primary references and their relationship to the experiment must be supplied before scientific release.',
              r'\section{Data availability and assistance disclosure}',
              'Source artifacts remain in approved private storage. This draft was generated automatically and requires author review, reference verification and an explicit data-sharing decision.',
              r'\appendix',r'\section{Evidence provenance}',r'\texttt{Report SHA256: '+tex(expected)+'}',r'\end{document}']
    outputs={'main.tex':('\n'.join(lines)+'\n').encode(),'metrics.csv':csv_stream.getvalue().encode(),
             'evidence.json':(data.canonical(dict(status='draft_requires_review',claims=evidence,report_sha256=expected,compiled='NOT_RUN'))+'\n').encode()}
    outputs['source-manifest.json']=(data.canonical(dict(version=1,report_sha256=expected,input_file_sha256=data.sha(raw),
        files={k:data.sha(v) for k,v in outputs.items()},scientific_verification='NOT_RUN',publication='NOT_RUN'))+'\n').encode()
    data.require(sum(len(v) for v in outputs.values())<=data.MAX_BYTES)
    output.mkdir(mode=0o700)
    for name,content in outputs.items():
        fd=os.open(output/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as stream: stream.write(content)
    return dict(status='draft_requires_review',directory=str(output),report_sha256=expected,compiled='NOT_RUN')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--title',default='Experiment report');parser.add_argument('--author')
    args=parser.parse_args()
    try:
        result=build(args.report,args.output,title=args.title,author=args.author)
        print(data.canonical(result))
    except (OSError,ValueError,KeyError,TypeError):parser.exit(2,'Preprint export rejected; inspect approved source evidence.\n')


if __name__=='__main__':main()
