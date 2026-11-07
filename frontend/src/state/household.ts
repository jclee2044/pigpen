import { computed,reactive } from 'vue'
import type { Kind,Payloads } from '../api/generated'
import { ApiError,request,execute,operation } from '../api/client'
import { emptyRecords,type Snapshot,type Resources } from '../api/models'
import { readMeta,writeMeta,pending as readPending,savePending,removePending,type Pending } from '../lib/storage'

export class PendingSubmissionError extends Error { constructor(public submissionId:string,text:string){super(text);this.name='PendingSubmissionError'} }
export const state=reactive({records:emptyRecords(),selectedId:'',deviceId:'',booted:false,hasCache:false,online:navigator.onLine,busy:false,pending:[] as Pending[],lastSync:'',error:'',notice:''})
export const activeUser=computed(()=>state.records.users.find(x=>x.id===state.selectedId&&x.active&&!x.deleted))
export const household=computed(()=>state.records.household[0])
export const offlineKinds=new Set<Kind>(['purchase.create','request.create','vote.set'])
export const rows=<K extends keyof Resources>(key:K):Resources[K][]=>state.records[key].filter(x=>!x.deleted) as Resources[K][]
export async function refresh(){
 const snapshot=await request<Snapshot>('/sync/snapshot')
 const stamp=new Date().toISOString()
 await writeMeta('cache',{...snapshot,lastSync:stamp})
 state.records=snapshot.records;state.lastSync=stamp;state.hasCache=true;state.online=true
}
export async function boot(){
 try{
  const cache=await readMeta<Snapshot&{lastSync:string}>('cache')
  if(cache){state.records=cache.records;state.lastSync=cache.lastSync;state.hasCache=true}
  state.selectedId=await readMeta<string>('selected-profile')??''
  state.deviceId=await readMeta<string>('device')??crypto.randomUUID();await writeMeta('device',state.deviceId)
  state.pending=await readPending()
  try{await refresh()}catch(error){if(error instanceof ApiError&&error.status===0)state.online=false;else state.error=message(error);if(!state.hasCache)state.error=message(error)}
 }catch(error){state.error='Local storage is unavailable. PigPen cannot safely save actions on this device. '+message(error)}
 finally{state.booted=true}
}
export const message=(error:unknown)=>error instanceof Error?error.message:'Something went wrong. Please retry.'
export async function selectProfile(id:string){
 if(!state.records.users.some(x=>x.id===id&&x.active))throw new Error('Choose an active profile.')
 await writeMeta('selected-profile',id);state.selectedId=id
 if(state.online){
  try{
   let revision=0
   try{const result=await request<{installation:{revision:number}}>('/installations/'+state.deviceId);revision=result.installation.revision}catch(error){if(!(error instanceof ApiError)||error.status!==404)throw error}
   await mutate('installation.select',{expected_revision:revision},state.deviceId)
  }catch(error){state.error='Profile selected locally. Device notification binding needs a retry. '+message(error)}
 }
}
export async function mutate<K extends Kind>(kind:K,data:Payloads[K],entity?:string):Promise<unknown>{
 if(!state.online&&!offlineKinds.has(kind))throw new Error('Reconnect to make this change.')
 const actor=activeUser.value?.id??null
 if(!actor&&!['household.initialize','user.create'].includes(kind))throw new Error('Select your profile first.')
 const op=operation(kind,data,actor,entity)
 const item:Pending={operation:op,state:'queued'}
 await savePending(item);state.pending=await readPending()
 if(!state.online){state.notice='Saved on this device. Waiting to sync.';return undefined}
 state.busy=true
 try{
  const outcome=await execute(op)
  await removePending(op.operation_id);state.pending=await readPending()
  try{await refresh()}catch{state.notice='Saved on the server. Refresh to load the latest records.'}
  return outcome.result
 }catch(error){
  const blocked=error instanceof ApiError&&error.status>=400&&error.status<500
  item.state=blocked?'blocked':'uncertain';item.error=message(error);item.details=error instanceof ApiError?error.details:null
  await savePending(item);state.pending=await readPending()
  if(error instanceof ApiError&&error.status===0)state.online=false
  if(!blocked)throw new PendingSubmissionError(op.operation_id,'Your submission is saved on this device. Retry it to check the server outcome safely.')
  throw error
 }finally{state.busy=false}
}
export async function retryPending(id:string){const item=(await readPending()).find(x=>x.operation.operation_id===id);if(!item)return;const outcome=await execute(item.operation);await removePending(id);state.pending=await readPending();await refresh();return outcome.result}
export async function discardBlocked(id:string){const item=(await readPending()).find(x=>x.operation.operation_id===id);if(item?.state!=='blocked')throw new Error('Resolve whether this action reached the server before discarding it.');await removePending(id);state.pending=await readPending()}
export function setError(error:unknown){state.error=message(error)}
