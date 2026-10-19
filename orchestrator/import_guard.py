"""Check a workflow-pinned imported artifact map without writing to the target."""
import argparse
import hashlib
import json
from .product_artifacts import canonical_sha, read_bytes


def check(root, name, digest):
    raw=read_bytes(root,name,1048576)
    if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Import receipt changed')
    value=json.loads(raw)
    if not isinstance(value,dict) or not value or len(value)>1000:raise ValueError('Invalid import receipt')
    for path, expected in value.items():
        if not isinstance(expected,str) or hashlib.sha256(read_bytes(root,path,1048576)).hexdigest()!=expected:
            raise ValueError('Imported artifact changed')
    return hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('root','manifest','sha'):p.add_argument('--'+key,required=True)
    args=p.parse_args()
    try:result=check(args.root,args.manifest,args.sha)
    except (ValueError,OSError,TypeError):p.exit(2,'Import guard: FAIL\n')
    print('PASS '+result)


if __name__=='__main__':main()
