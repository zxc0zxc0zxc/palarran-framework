"""Trusted local bridge into the existing exact-subject integration queue."""
import json, os, pathlib, subprocess, sys, signal
STOP_REQUESTED=False
def request_stop(signum,frame):
    global STOP_REQUESTED
    STOP_REQUESTED=True
signal.signal(signal.SIGTERM,request_stop)
signal.signal(signal.SIGINT,request_stop)
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from packages.core.parallelism.integration import IntegrationQueue

class RootBudget:
    def __init__(self,manifest):self.manifest=manifest
    def rpc(self,command,**values):
        m=self.manifest
        payload=dict(parent=m['parent'],run_id=m['run_id'],**values)
        result=subprocess.run([m['node'],m['supervisor'],'rpc','--state',m['state_path']],input=json.dumps(dict(version=1,command=command,payload=payload)),text=True,capture_output=True,timeout=10,env={'PATH':'/usr/bin:/bin','NODE_NO_WARNINGS':'1'})
        return json.loads(result.stdout)
    def reserve(self,run_id,phase,item_id):
        result=self.rpc('phase_admit',kind=phase)
        return result.get('ticket') if result.get('status')=='ADMITTED' else None
    def heartbeat(self,ticket):
        return not STOP_REQUESTED and self.rpc('status').get('status') not in ('CANCELLED','CANCELLING','ATTENTION','BUDGET_OVERRUN')
    def settle(self,ticket,outcome):
        result=self.rpc('phase_complete',ticket=ticket,outcome=outcome['status'])
        return {'status':'verified' if result.get('status')=='RECORDED' and outcome['status']=='known' else 'unknown'}

def main():
    raw=sys.stdin.buffer.read(262145)
    if len(raw)>262144:raise ValueError('input_limit')
    m=json.loads(raw);queue=IntegrationQueue(m['queue_path'],gate_registry=m['gate_registry'],budget_binding=RootBudget(m),git_identity={'name':'Palarran Worker','email':'palarran@localhost'})
    try:
        items=[]
        for row in m['items']:
            items.append({k:row[k] for k in ('item_id','task_id','owner','source_commit','task_receipt_sha256','receipt_file','gates','impacts')})
        queue.create(m['run_id'],m['repository'],m['base_commit'],m['branch'],m['workspace'],items,m['required_gates'])
        queue.prepare()
        for _ in items:
            report=queue.advance()
            if report['status'] in ('blocked','unknown'):break
        else:report=queue.finalize()
        print(json.dumps(report,sort_keys=True))
    finally:queue.db.close()
if __name__=='__main__':
    try:main()
    except Exception:
        print(json.dumps({'status':'UNKNOWN','code':'integration_requires_reconciliation','hint':'Inspect the existing integration journal and exact Git head; do not replay.'}));sys.exit(2)
