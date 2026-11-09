import type { ExtensionAPI } from '@earendil-works/pi-coding-agent';
import { Type } from 'typebox';
import { registerPalarran } from './core.mjs';

const id=Type.String({minLength:1,maxLength:128,pattern:'^[A-Za-z0-9][A-Za-z0-9_.:-]*$'});
const optionalRun={run_id:Type.Optional(id)};
const task=Type.Object({
  task_id:id,goal:Type.String({minLength:1,maxLength:8192}),
  acceptance:Type.Union([Type.String({minLength:1,maxLength:8192}),Type.Array(Type.String({minLength:1,maxLength:2048}),{minItems:1,maxItems:32})]),
  depends_on:Type.Optional(Type.Array(Type.Union([id,Type.Object({task_id:id,condition:Type.Union([Type.Literal('artifact'),Type.Literal('verified'),Type.Literal('integrated')])},{additionalProperties:false})]),{maxItems:500})),
  mode:Type.Optional(Type.Union([Type.Literal('read'),Type.Literal('write')])),
  repository:Type.String({minLength:1,maxLength:4096}),
  base_commit:Type.Optional(Type.String({pattern:'^[a-f0-9]{40,64}$'})),
  files:Type.Optional(Type.Array(Type.String({maxLength:4096}),{maxItems:256})),
  profile:Type.Optional(Type.Union([Type.String({maxLength:128}),Type.Record(Type.String(),Type.Unknown())])),
},{additionalProperties:false});
const limits=Type.Object(Object.fromEntries(['workers','model_requests','writers','heavy','integration','queue'].map(k=>[k,Type.Optional(Type.Integer({minimum:1,maximum:k==='queue'?10000:100}))])),{additionalProperties:false});
const schemas={
  spawn:Type.Object({...optionalRun,idempotency_key:id,tasks:Type.Array(task,{minItems:1,maxItems:500}),limits:Type.Optional(limits),budget:Type.Optional(Type.Object({tokens:Type.Integer({minimum:0}),cost_micros:Type.Integer({minimum:0})},{additionalProperties:false}))},{additionalProperties:false}),
  status:Type.Object(optionalRun,{additionalProperties:false}),
  wait:Type.Object({...optionalRun,after:Type.Optional(Type.Integer({minimum:0})),limit:Type.Optional(Type.Integer({minimum:1,maximum:100})),seconds:Type.Optional(Type.Integer({minimum:0,maximum:30}))},{additionalProperties:false}),
  result:Type.Object({...optionalRun,task_id:id},{additionalProperties:false}),
  send:Type.Object({...optionalRun,task_id:id,message:Type.String({minLength:1,maxLength:8192}),idempotency_key:id},{additionalProperties:false}),
  follow_up:Type.Object({...optionalRun,task_id:id,idempotency_key:id,task},{additionalProperties:false}),
  cancel:Type.Object({...optionalRun,task_id:Type.Optional(id),idempotency_key:Type.Optional(id)},{additionalProperties:false}),
};
export default function(pi:ExtensionAPI){registerPalarran(pi,{schemas});}
