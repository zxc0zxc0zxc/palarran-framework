#!/usr/bin/env python3
"""Synthetic readiness-decision oracle, not a semantic data/model-quality grader."""
import json
import os
import stat
from pathlib import Path
import sys

EXPECTED={
 'long_input_short_target':('blocked','complete_solutions','target_mismatch',False,False),
 'goal_missing':('needs_clarification',None,'goal_undefined',False,False),
 'short_confirmation':('ready','confirmation','checked_target_support',True,False),
 'no_data_access':('not_run','complete_solutions','missing_actual_exposure',False,False),
 'preserved_ability':('ready','style','checked_target_support',True,True),
}


def pairs(items):
    result={}
    for k,v in items:
        if k in result:raise ValueError('duplicate')
        result[k]=v
    return result


def check(case,answer):
    expected=EXPECTED[case]
    if not isinstance(answer,dict) or set(answer)!={'decision','goal_id','basis','launch_ready','preservation_tests'}:return False
    if type(answer['launch_ready']) is not bool or type(answer['preservation_tests']) is not bool:return False
    return tuple(answer[k] for k in ('decision','goal_id','basis','launch_ready','preservation_tests'))==expected


def main():
    try:
        if len(sys.argv)!=3:return 2
        p=Path(sys.argv[2]).absolute()
        if p.is_symlink() or any(x.is_symlink() for x in p.parents):return 2
        fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):return 2
            raw=stream.read(65537)
        if len(raw)>65536:return 2
        value=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
        return 0 if check(sys.argv[1],value) else 1
    except (OSError,ValueError,KeyError,TypeError):return 2

if __name__=='__main__':raise SystemExit(main())
