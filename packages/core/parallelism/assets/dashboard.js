'use strict';
let paused=false, lastGood=null;
const el=id=>document.getElementById(id);
const value=v=>v===null||v===undefined?'Unknown':String(v);
const number=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0?v.toLocaleString('en-US'):'Unknown';
const money=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0?'$'+(v/1e6).toFixed(4):'Unknown';
const put=(id,text)=>{el(id).textContent=text;};
function node(tag,text){const n=document.createElement(tag);n.textContent=text;return n;}
function warning(text){el('warning').hidden=!text;put('warning',text);}
function render(s){
  lastGood=s;put('freshness',s.freshness.toUpperCase());
  warning(s.freshness!=='current'?'Authority '+s.freshness+'. Values below are the last observation; do not treat them as current.':'');
  if(!s.report){put('status','Unknown');return;}
  const r=s.report,u=r.usage,b=r.budget,known=u.known===true;
  put('run',r.run_id);put('status',value(r.status));put('meta',`${value(r.backend)} backend · plan ${value(r.plan_version)}${r.backend==='fixture'?' · DEMO FIXTURE':''}`);
  put('observed',`Observed ${new Date(s.observed_at*1000).toLocaleTimeString()} · ${Math.round(s.age_seconds)}s ago`);
  put('tokens',known?number(u.tokens):'Unknown total');put('cost',known?money(u.cost_micros):'Unknown total');
  put('token-reserve',`Reserved ${number(u.reserved_tokens)} / cap ${number(b.tokens)}${known?'':` · reported ${number(u.tokens)}`}`);
  put('cost-reserve',`Reserved ${money(u.reserved_cost_micros)} / cap ${money(b.cost_micros)}${known?'':` · reported ${money(u.cost_micros)}`}`);
  [['token-meter','tokens'],['cost-meter','cost_micros']].forEach(([id,key])=>{const n=el(id);n.hidden=!(known&&typeof u[key]==='number'&&b[key]>0);n.value=Math.min(1,u[key]/b[key]);});
  const summary=r.task_summary;
  put('verified',`${summary.verified} / ${summary.completion_tasks}`);
  put('attention',number(summary.attention));put('attention-copy',`${summary.blocked} blocked · ${summary.unknown} unknown · ${summary.human_handoffs} human handoffs`);
  const tbody=el('tasks');tbody.replaceChildren();el('empty').hidden=r.tasks.length>0;
  r.tasks.forEach(t=>{const row=document.createElement('tr');const task=node('td',value(t.task_id));task.append(node('small',`Repository ${value(t.repository_id)} · queue ${value(t.task_queue)} · phase ${value(t.budget_phase)}`));task.append(node('small',`Depends on: ${(t.depends_on||[]).join(', ')||'none'}`));row.append(task);
    const owner=node('td',value(t.owner));owner.append(node('small',`${value(t.machine)} · session ${value(t.session_id)}`));row.append(owner);
    const state=node('td','');const tag=node('span',t.unused_reserve?'Unused reserve':value(t.state));tag.className='tag '+(['verified','blocked','unknown','failed','handoff_pending','cancel_requested'].includes(t.state)&&!(t.state==='verified'&&!t.verified_subject)?t.state:'');state.append(tag);state.append(node('small',`Attempt ${value(t.attempt_id)} · heartbeat ${typeof t.heartbeat_at==='number'?new Date(t.heartbeat_at*1000).toLocaleTimeString():t.unused_reserve?'not started':'unknown'}`));row.append(state);
    row.append(node('td',t.unused_reserve?'External capacity · not required unless attempted':t.reason||(['blocked','unknown','handoff_pending'].includes(t.state)?'Action unspecified — review authority':'—')));
    const subject=typeof t.verified_subject==='object'&&t.verified_subject?JSON.stringify(t.verified_subject):value(t.verified_subject);
    row.append(node('td',t.unused_reserve?'—':t.state==='verified'?subject:'Unverified'));row.append(node('td',`${t.usage_known===true?number(t.tokens):'Unknown total'} / ${number(t.reserved_tokens)}`));tbody.append(row);});
  const identity=el('identity');identity.replaceChildren();[['Base commit',r.base_commit],['Plan SHA-256',r.plan_sha256],['Unused external reserves',summary.unused_reserves],['Observation freshness','Current means authority reachable; individual task heartbeats may be old.']].forEach(([k,v])=>{identity.append(node('dt',k),node('dd',value(v)));});
  const i=s.integration;put('integration-state',i?value(i.status):'Not connected');put('integration-copy',i?`PR readiness: ${i.pr_ready===true&&s.freshness==='current'?'reported ready':'not established'} · head ${value(i.head)} · remaining ${value(i.remaining)}`:'No integration report is connected. Publication readiness is unknown.');
  const items=el('integration-items');items.replaceChildren();if(i)(i.items||[]).forEach(item=>{const n=node('div',`${value(item.item_id)} · ${value(item.owner)} · ${value(item.status)} · integrated commit ${value(item.integrated_commit)}`);n.className='integration-item';items.append(n);(item.gates||[]).forEach(g=>items.append(node('p',`${value(g.gate_id)}: ${value(g.status)} · subject ${value(g.subject)}`)));});
  const f=s.feature;el('feature').hidden=!f;
  if(f){
    put('feature-state',value(f.status));
    put('feature-identity',`${value(f.feature_id)} · spec ${value(f.spec_revision)} · plan ${value(f.plan_revision)} · composition ${value(f.composition_id)}`);
    put('feature-ready',`Release readiness: ${f.release_ready===true&&s.freshness==='current'?'established for this composition':'not established'}. Delivery requires separate authorization.`);
    const blockers=el('feature-blockers');blockers.replaceChildren();(f.blockers||[]).forEach(b=>blockers.append(node('p',value(b))));
    const services=el('feature-services');services.replaceChildren();Object.entries((f.composition||{}).components||{}).forEach(([name,c])=>services.append(node('p',`${name} · commit ${value(c.commit)} · image ${value(c.image_digest)}`)));
    renderGraph(r.tasks);
    const prs=el('feature-prs');prs.replaceChildren();(f.pull_requests||[]).forEach(p=>prs.append(node('p',`${value(p.repository_id)} · ${value(p.platform)} #${value(p.number)} · ${value(p.state)} · ${p.current?'current composition':'historical'} · ${value(p.commit)}`)));
    const contracts=el('feature-contracts');contracts.replaceChildren();(f.contracts||[]).forEach(c=>contracts.append(node('p',`${value(c.contract_id)} · revision ${value(c.revision)} · producer ${value(c.producer)} · semantics ${value(c.semantics_sha256)}`)));
    const checks=el('feature-checks');checks.replaceChildren();(f.checks||[]).forEach(c=>checks.append(node('p',`${value(c.check_id)} · ${value(c.kind)} · ${value(c.verdict)} · subject ${value(c.subject)}`)));
    const release=el('feature-release');release.replaceChildren();(f.steps||[]).forEach(c=>release.append(node('p',`${value(c.step_id)} · ${value(c.owner)} · ${value(c.kind)} · ${value(c.state||c.status)}${c.irreversible?' · irreversible action':''}`)));
  }

}
function renderGraph(tasks){
  const target=el('feature-graph');target.replaceChildren();
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
  const columns=new Map(),memo=new Map(),byId=new Map(tasks.map(t=>[t.task_id,t]));
  function depth(t,seen=new Set()){
    if(memo.has(t.task_id))return memo.get(t.task_id);
    if(seen.has(t.task_id))return 0;
    const next=new Set(seen);next.add(t.task_id);
    const d=Math.min(8,Math.max(0,...(t.depends_on||[]).filter(id=>byId.has(id)).map(id=>1+depth(byId.get(id),next))));memo.set(t.task_id,d);return d;
  }
  const positions=new Map();
  tasks.forEach(t=>{const d=depth(t),row=columns.get(d)||0;columns.set(d,row+1);positions.set(t.task_id,[d*240+16,row*76+16]);});
  const width=(Math.max(0,...columns.keys())+1)*240,height=Math.max(1,...columns.values())*76+16;
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('width',width);svg.setAttribute('height',height);svg.setAttribute('role','img');svg.setAttribute('aria-label','Task dependency graph by repository');
  function element(tag,attributes){const n=document.createElementNS(ns,tag);Object.entries(attributes).forEach(([k,v])=>n.setAttribute(k,v));return n;}
  tasks.forEach(t=>{const [x,y]=positions.get(t.task_id);(t.depends_on||[]).forEach(id=>{if(!positions.has(id))return;const [a,b]=positions.get(id);svg.append(element('path',{d:`M${a+210} ${b+28} L${x} ${y+28}`,stroke:'#666',fill:'none'}));});});
  tasks.forEach(t=>{const [x,y]=positions.get(t.task_id);svg.append(element('rect',{x,y,width:210,height:56,rx:8,fill:'#161616',stroke:t.state==='verified'?'#78a48b':'#555'}));const title=element('text',{x:x+10,y:y+22,fill:'#eee','font-size':12});title.textContent=t.task_id.length>26?t.task_id.slice(0,23)+'…':t.task_id;svg.append(title);const line=element('text',{x:x+10,y:y+42,fill:'#aaa','font-size':10});line.textContent=`${value(t.repository_id)} · ${value(t.state)}`;svg.append(line);});
  target.append(svg);
}

async function poll(){if(paused)return;try{const response=await fetch('/api/snapshot',{cache:'no-store',credentials:'same-origin'});if(!response.ok)throw new Error('Unavailable');render(await response.json());}catch(_){put('freshness','DISCONNECTED');warning('Connection lost. Last displayed values are stale; current state is unknown.');put('integration-state','Unknown — disconnected');put('feature-state','Unknown — disconnected');put('feature-ready','Readiness unknown: authority disconnected.');}}
el('pause').addEventListener('click',()=>{paused=!paused;put('pause',paused?'Resume updates':'Pause updates');if(paused){put('freshness','PAUSED');warning('Updates paused. Displayed values are a historical snapshot.');put('feature-state','Historical — paused');put('feature-ready','Readiness unknown: updates paused.');put('integration-state','Historical — paused');}else poll();});
poll();setInterval(poll,3000);
