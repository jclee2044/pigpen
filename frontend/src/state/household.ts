import { computed,reactive } from 'vue'
import type { Kind,Payloads } from '../api/generated'
import { ApiError,request,execute,operation } from '../api/client'
import { emptyRecords,type Snapshot,type Resources,type ChangePage,type RuntimeInfo } from '../api/models'
import { readMeta,writeMeta,pending as readPending,savePending,removePending,commitCache,type CachedSnapshot,type Pending } from '../lib/storage'
import { applyPage } from '../lib/sync'
import { orderCategories } from '../lib/categoryOrder'
import type { Category } from '../api/models'

export class PendingSubmissionError extends Error { constructor(public submissionId:string,text:string){super(text);this.name='PendingSubmissionError'} }
export const state=reactive({records:emptyRecords(),selectedId:'',deviceId:'',booted:false,hasCache:false,online:navigator.onLine,busy:false,syncing:false,pending:[] as Pending[],lastSync:'',error:'',notice:'',environment:null as RuntimeInfo['environment']|null})
// Online reorder writes are durable, but need no waiting-to-sync notice while running.
export const submittingOperations=reactive(new Set<string>())
export const activeUser=computed(()=>state.records.users.find(x=>x.id===state.selectedId&&x.active&&!x.deleted))
export const household=computed(()=>state.records.household[0])
export const offlineKinds=new Set<Kind>(['purchase.create','request.create','vote.set'])
export const rows=<K extends keyof Resources>(key:K):Resources[K][]=>{
 const result=state.records[key].filter(x=>!x.deleted) as Resources[K][]
 return key==='categories'?orderCategories(result as Category[],household.value?.category_order) as Resources[K][]:result
}
let runtimeLoading=false
function identifyServer(){
 if(state.environment||runtimeLoading)return
 runtimeLoading=true
 // Optional metadata must never block financial reads or queued writes.
 void request<RuntimeInfo>('/runtime',{},3000).then(info=>{
  if(['production','development','test'].includes(info.environment))state.environment=info.environment
 }).catch(()=>{}).finally(()=>{runtimeLoading=false})
}
export async function refresh(replace=false){
 const snapshot=await request<Snapshot>('/sync/snapshot')
 const stamp=new Date().toISOString()
 const committed=await commitCache({...snapshot,lastSync:stamp},replace)
 state.records=committed.records;state.lastSync=committed.lastSync;state.hasCache=true;state.online=true
 identifyServer()
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
let selectionEpoch=0
export async function selectProfile(id:string){
 if(!state.records.users.some(x=>x.id===id&&x.active))throw new Error('Choose an active profile.')
 const epoch=++selectionEpoch
 await writeMeta('selected-profile',id)
 if(epoch!==selectionEpoch)return
 state.selectedId=id
 if(state.online)await bindCurrentProfile()
}
export async function clearProfile(){
 ++selectionEpoch
 await writeMeta('selected-profile','')
 state.selectedId=''
}
async function bindCurrentProfile(){
 const bind=async()=>{
  const id=await readMeta<string>('selected-profile')
  if(!id||!state.records.users.some(x=>x.id===id&&x.active))return
  let revision=0
  try{
   try{const result=await request<{installation:{revision:number;user_id:string}}>('/installations/'+state.deviceId);if(result.installation.user_id===id)return;revision=result.installation.revision}catch(error){if(!(error instanceof ApiError)||error.status!==404)throw error}
   if(await readMeta<string>('selected-profile')!==id)return
   const op=operation('installation.select',{expected_revision:revision},id,state.deviceId)
   await savePending({operation:op,state:'queued'})
   try{await execute(op);await removePending(op.operation_id)}catch(error){await savePending({operation:op,state:error instanceof ApiError&&error.status>=400&&error.status<500?'blocked':'uncertain',error:message(error)});throw error}
  }catch(error){state.error='Profile selected locally. Device notification binding needs a retry. '+message(error)}
  finally{state.pending=await readPending()}
 }
 if(navigator.locks)await navigator.locks.request('pigpen-profile-binding',bind);else await bind()
}
export async function mutate<K extends Kind>(kind:K,data:Payloads[K],entity?:string):Promise<unknown>{
 if(!state.online&&!offlineKinds.has(kind))throw new Error('Reconnect to make this change.')
 const actor=activeUser.value?.id??null
 if(!actor&&!['household.initialize','user.create'].includes(kind))throw new Error('Select your profile first.')
 const op=operation(kind,data,actor,entity)
 const item:Pending={operation:op,state:'queued'}
 await savePending(item)
 submittingOperations.add(op.operation_id)
 try{
  state.pending=await readPending()
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
   if(kind==='receipt.confirm'&&error instanceof ApiError&&error.code==='receipt_duplicate')await removePending(op.operation_id)
   else await savePending(item)
   state.pending=await readPending()
   if(error instanceof ApiError&&error.status===0)state.online=false
   if(!blocked)throw new PendingSubmissionError(op.operation_id,'Your submission is saved on this device. Retry it to check the server outcome safely.')
   throw error
  }finally{state.busy=false}
 }finally{submittingOperations.delete(op.operation_id)}
}
export async function retryPending(id:string){
 const item=(await readPending()).find(x=>x.operation.operation_id===id);if(!item)return
 try{const outcome=await execute(item.operation);await removePending(id);state.pending=await readPending();await refresh();return outcome.result}
 catch(error){if(error instanceof ApiError&&error.status>=400&&error.status<500)await savePending({...item,state:'blocked',error:message(error),details:error.details});state.pending=await readPending();throw error}
}
export async function discardBlocked(id:string){const item=(await readPending()).find(x=>x.operation.operation_id===id);if(item?.state!=='blocked')throw new Error('Resolve whether this action reached the server before discarding it.');await removePending(id);state.pending=await readPending()}
export function setError(error:unknown){state.error=message(error)}


let inFlight:Promise<void>|undefined
async function pullChanges(){
 let cache=await readMeta<CachedSnapshot>('cache')
 if(!cache){await refresh();return}
 for(let pages=0;pages<10000;pages++){
  let page:ChangePage
  try{page=await request<ChangePage>('/sync/pull?cursor='+cache.cursor+'&limit=100')}catch(error){if(error instanceof ApiError&&error.status===409&&error.code==='cursor'){await refresh(true);return}throw error}
  const next=applyPage(cache,page)
  cache=await commitCache({...next,lastSync:new Date().toISOString()})
  state.records=cache.records;state.lastSync=cache.lastSync;state.online=true;state.hasCache=true
  identifyServer()
  if(!page.has_more)return
 }
 throw new Error('There are more changes to load. Sync again to continue.')
}
async function synchronizeInside(){
 state.syncing=true
 try{
  const epoch=selectionEpoch;const selected=await readMeta<string>('selected-profile');if(selected&&epoch===selectionEpoch)state.selectedId=selected
  // Replay persisted envelopes verbatim. This also resolves uncertain online-only submissions.
  for(const item of await readPending()){
   if(item.state==='blocked')continue
   try{await execute(item.operation);await removePending(item.operation.operation_id)}
   catch(error){
    const blocked=error instanceof ApiError&&error.status>=400&&error.status<500
    await savePending({...item,state:blocked?'blocked':'uncertain',error:message(error),details:error instanceof ApiError?error.details:null})
    if(!blocked)throw error
   }
  }
  state.pending=await readPending()
  await pullChanges()
  state.error=''
  if(activeUser.value)await bindCurrentProfile()
 }catch(error){
  state.pending=await readPending()
  if(error instanceof ApiError&&error.status===0)state.online=false
  else state.error=message(error)
 }finally{state.syncing=false}
}
export function synchronize():Promise<void>{
 if(inFlight)return inFlight
 const run=()=>synchronizeInside()
 inFlight=(navigator.locks?navigator.locks.request('pigpen-sync',run):run()).finally(()=>{inFlight=undefined})
 return inFlight
}
export function startSynchronization(onForeground:()=>Promise<void>=synchronize){
 const online=()=>{state.online=true;void synchronize()}
 const offline=()=>{state.online=false}
 const foreground=()=>{if(document.visibilityState==='visible')void onForeground()}
 window.addEventListener('online',online);window.addEventListener('offline',offline);window.addEventListener('focus',foreground);document.addEventListener('visibilitychange',foreground)
 const push=(event:MessageEvent)=>{if(event.data?.type==='PIGPEN_NOTIFICATION'&&document.visibilityState==='visible')void synchronize()}
 navigator.serviceWorker?.addEventListener('message',push)
 const timer=setInterval(()=>{if(document.visibilityState==='visible'&&navigator.onLine)void synchronize()},60000)
 return ()=>{navigator.serviceWorker?.removeEventListener('message',push);clearInterval(timer);window.removeEventListener('online',online);window.removeEventListener('offline',offline);window.removeEventListener('focus',foreground);document.removeEventListener('visibilitychange',foreground)}
}
