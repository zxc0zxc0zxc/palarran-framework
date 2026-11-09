/** Native UI/client registration; contains no scheduler or provider execution. */
import fs from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createRpcClient } from './rpc.mjs';
const executeFile=promisify(execFile);
const COMMANDS=['spawn','status','wait','result','send','follow_up','cancel'];
const RECORD='palarran-swarm-view';
const SAFE_ID=/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/u;
const KEYS={spawn:['run_id','idempotency_key','tasks','limits','budget'],status:['run_id'],
 wait:['run_id','after','limit','seconds'],result:['run_id','task_id'],send:['run_id','task_id','message','idempotency_key'],
 follow_up:['run_id','task_id','idempotency_key','task'],cancel:['run_id','task_id','idempotency_key']};
const scrub=(value,limit=120)=>String(value??'').replace(/[\x00-\x1f\x7f-\x9f]/gu,' ').slice(0,limit);
const count=value=>Number.isSafeInteger(value)&&value>=0?String(value):'?';
const money=value=>Number.isSafeInteger(value)&&value>=0?'$'+(value/1e6).toFixed(4):'unknown';
function error(code){return {status:'REJECTED',code,hint:'Use the current pi session and a scoped run; no automatic retry.'};}
export async function resolveRepository(cwd){
  const physical=await fs.realpath(cwd);
  try {
    const {stdout}=await executeFile('/usr/bin/git',['--no-replace-objects','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-C',physical,'rev-parse','--show-toplevel'],{
      env:{PATH:'/usr/bin:/bin',GIT_CONFIG_NOSYSTEM:'1',GIT_CONFIG_GLOBAL:'/dev/null',GIT_OPTIONAL_LOCKS:'0'},timeout:2000,maxBuffer:4096,
    });
    return await fs.realpath(stdout.trim());
  }catch{return physical;}
}
export function compactResult(value){
  let encoded;
  try {encoded=JSON.stringify(value);}catch{return error('invalid_supervisor_response');}
  if(Buffer.byteLength(encoded)<=16384)return value;
  const result={status:scrub(value.status,64),truncated:true,code:'response_truncated',
    hint:'Read selected result artifacts or narrower task status; full transcripts are not inserted.',
    run_id:scrub(value.run_id,128),task_id:scrub(value.task_id,128)};
  if(typeof value.summary==='string')result.summary=scrub(value.summary,4096);
  if(value.counts&&typeof value.counts==='object')result.counts=value.counts;
  if(value.budget&&typeof value.budget==='object')result.budget=value.budget;
  if(Array.isArray(value.artifacts))result.artifacts=value.artifacts.slice(0,8).map(x=>typeof x==='string'?scrub(x,256):{reference:scrub(x?.reference??x?.path,256)});
  if(Array.isArray(value.tasks))result.tasks=value.tasks.slice(0,8).map(t=>({task_id:scrub(t.task_id,128),state:scrub(t.state??t.status,40)}));
  if(Buffer.byteLength(JSON.stringify(result))>12000)delete result.budget;
  if(Buffer.byteLength(JSON.stringify(result))>12000)delete result.counts;
  return result;
}
export function widgetLines(value){
  const c=value.counts??{},b=value.budget??{};
  const lines=[`Palarran · ${scrub(value.run_id,48)} · ${scrub(value.status,32)}`,
    `Tasks ${count(c.total)} · running ${count(c.running)} · queued ${count(c.queued)} · unknown ${count(c.unknown)}`,
    `Tokens ${count(b.tokens_used)} used / ${count(b.tokens_reserved)} reserved · spend ${money(b.cost_micros_used)} / ${money(b.cost_micros_reserved)} reserved`];
  for(const task of (Array.isArray(value.tasks)?value.tasks:[]).slice(0,5))lines.push(`${scrub(task.task_id,28)} · ${scrub(task.state??task.status,20)} · ${scrub(task.goal,66)}`);
  if(Array.isArray(value.attention)&&value.attention.length)lines.push(`Attention: ${value.attention.slice(0,2).map(x=>scrub(typeof x==='string'?x:x?.code,70)).join('; ')}`);
  return lines;
}
export function registerPalarran(pi,options={}){
  const rpc=options.rpc??createRpcClient(options);
  const repository=options.resolveRepository??resolveRepository;
  const schedule=options.setInterval??setInterval,unschedule=options.clearInterval??clearInterval;
  let current,interval,generation=0;
  const known=new Map();
  const key=p=>JSON.stringify([p.session_id,p.repository]);
  async function parentFor(ctx){
    const id=ctx.sessionManager.getSessionId();
    if(typeof id!=='string'||!SAFE_ID.test(id))throw new Error('invalid_parent');
    const project=await repository(ctx.cwd);
    if(id!==ctx.sessionManager.getSessionId())throw new Error('parent_changed');
    return {session_id:id,repository:project};
  }
  function clear(){
    generation++;
    if(interval!==undefined){unschedule(interval);interval=undefined;}
    if(current){current.abort.abort();if(current.ctx.hasUI)current.ctx.ui.setWidget('palarran-swarm',undefined);}
    current=undefined;
  }
  function show(state,value){
    if(current!==state||state.generation!==generation||!state.ctx.hasUI)return;
    state.ctx.ui.setWidget('palarran-swarm',widgetLines(value));
  }
  async function poll(){
    const state=current;
    if(!state?.run_id||state.polling)return;
    state.polling=true;
    try{
      const value=await rpc('status',{run_id:state.run_id,parent:state.parent},{signal:state.abort.signal});
      if(current!==state||state.abort.signal.aborted)return;
      show(state,value);
      if(!['REJECTED','UNKNOWN','CONFLICT'].includes(value.status)){
        const events=await rpc('events',{run_id:state.run_id,parent:state.parent,after:state.cursor,limit:10},{signal:state.abort.signal});
        if(current===state&&Number.isSafeInteger(events.cursor)&&events.cursor>=state.cursor)state.cursor=events.cursor;
      }
      if(current===state&&['COMPLETED','CANCELLED'].includes(value.status)&&interval!==undefined){unschedule(interval);interval=undefined;}
    }catch{if(current===state)show(state,error('supervisor_unavailable'));}
    finally{state.polling=false;}
  }
  function watch(state){
    if(!state.ctx.hasUI||state.ctx.mode!=='tui'||!state.run_id||interval!==undefined)return;
    interval=schedule(poll,options.intervalMs??5000);interval?.unref?.();
  }
  function select(state,run_id,persist=true){
    if(typeof run_id!=='string'||!SAFE_ID.test(run_id))return;
    const changed=state.run_id!==run_id;
    state.run_id=run_id;known.set(key(state.parent),run_id);
    if(persist&&changed&&typeof pi.appendEntry==='function')pi.appendEntry(RECORD,{version:1,run_id,...state.parent});
    watch(state);
  }
  async function session(ctx){
    clear();const token=generation;
    const parent=await parentFor(ctx);
    if(token!==generation)return;
    const state={ctx,parent,run_id:known.get(key(parent)),cursor:0,abort:new AbortController(),polling:false,generation};
    current=state;
    if(!state.run_id){
      const entries=ctx.sessionManager.getEntries?.()??[];
      for(const record of [...entries].reverse()){
        const data=record?.data;
        if(record?.type==='custom'&&record.customType===RECORD&&data?.version===1&&data.session_id===parent.session_id&&data.repository===parent.repository&&typeof data.run_id==='string'&&SAFE_ID.test(data.run_id)){select(state,data.run_id,false);break;}
      }
    }
    watch(state);
  }
  async function scoped(command,params,ctx,signal){
    const parent=await parentFor(ctx);
    const payload={};
    for(const name of KEYS[command]??[])if(Object.hasOwn(params??{},name))payload[name]=params[name];
    payload.parent=parent;
    if(!payload.run_id&&command!=='spawn')payload.run_id=known.get(key(parent));
    const value=await rpc(command,payload,{signal});
    if(value.run_id&&current&&key(current.parent)===key(parent)&&!signal?.aborted&&command==='spawn')select(current,value.run_id);
    return compactResult(value);
  }
  for(const command of COMMANDS){
    pi.registerTool({name:'swarm_'+command,label:'Swarm '+command.replace('_',' '),
      description:command==='spawn'?'Queue bounded tasks in the durable Palarran supervisor. Queued is not running; model tools cannot approve paid work.':`Read or manage this pi parent's Palarran ${command.replace('_',' ')} state. Unknown outcomes require inspection.`,
      parameters:options.schemas?.[command]??{type:'object',additionalProperties:false},
      execute:async(_id,params,signal,_update,ctx)=>{
        let value;try{value=await scoped(command,params,ctx,signal);}catch{value=error('invalid_or_unavailable_parent');}
        return {content:[{type:'text',text:JSON.stringify(value)}],details:value,isError:['REJECTED','UNKNOWN','CONFLICT'].includes(value.status)};
      }});
  }
  pi.registerCommand('swarm',{description:'Inspect Palarran tasks or explicitly approve/start a reviewed bounded run.',handler:async(args,ctx)=>{
    try{
      const words=String(args??'').trim().split(/\s+/u).filter(Boolean);
      const action=words[0]??(current?.run_id?'status':'help');
      const allowed=new Set(['status','use','doctor','result','cancel','approve','start','recover','integrate','help']);
      if(!allowed.has(action)||words.length>3)throw new Error('invalid_command');
      if(action==='help'){
        ctx.ui.notify('Palarran: /swarm doctor | status RUN | use RUN | result RUN TASK | cancel RUN [TASK] | approve RUN | start RUN | recover RUN | integrate RUN TASK. Start executes only an operator-reviewed bounded run.','info');return;
      }
      const parent=await parentFor(ctx),run_id=words[1]??known.get(key(parent));
      if(action!=='doctor'&&(!run_id||!SAFE_ID.test(run_id)))throw new Error('missing_run');
      if(words[2]&&!SAFE_ID.test(words[2]))throw new Error('invalid_task');
      const payload={parent};if(run_id)payload.run_id=run_id;if(words[2])payload.task_id=words[2];
      const value=compactResult(await rpc(action==='use'?'status':action,payload,{}));
      if(value.run_id&&current&&key(current.parent)===key(parent)&&!['REJECTED','CONFLICT','UNKNOWN'].includes(value.status))select(current,value.run_id);
      if(current&&key(current.parent)===key(parent))show(current,value);
      ctx.ui.notify(JSON.stringify(value),['REJECTED','UNKNOWN','CONFLICT'].includes(value.status)?'warning':'info');
    }catch{ctx.ui.notify('Palarran command unavailable. Use /swarm help with a scoped run and task ID.','warning');}
  }});
  pi.on('session_start',async(_event,ctx)=>{try{await session(ctx);}catch{clear();}});
  pi.on('session_shutdown',()=>{clear();});
  return {poll,dispose:clear};
}
