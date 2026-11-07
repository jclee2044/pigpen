/** One IndexedDB ledger. Writes resolve only after their transaction commits. */
import type { Operation } from '../api/generated'
export interface Pending { operation:Operation; state:'queued'|'uncertain'|'blocked'; error?:string; details?:unknown; sequence?:number }
const DB_NAME='pigpen-v1'
export function openDb(): Promise<IDBDatabase> { return new Promise((resolve,reject)=>{
 const req=indexedDB.open(DB_NAME,1)
 req.onupgradeneeded=()=>{req.result.createObjectStore('meta');req.result.createObjectStore('pending',{keyPath:'operation.operation_id'})}
 req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);req.onblocked=()=>reject(new Error('Close other PigPen tabs to update local storage.'))
}) }
const clone=<T>(value:T):T=>JSON.parse(JSON.stringify(value))
export async function readMeta<T>(key:string):Promise<T|undefined>{const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction('meta');const req=tx.objectStore('meta').get(key);req.onsuccess=()=>resolve(req.result as T|undefined);req.onerror=()=>reject(req.error);tx.oncomplete=()=>db.close();tx.onabort=()=>{db.close();reject(tx.error)}})}
export async function writeMeta<T>(key:string,value:T){const db=await openDb();return new Promise<void>((resolve,reject)=>{const tx=db.transaction('meta','readwrite');tx.objectStore('meta').put(clone(value),key);tx.oncomplete=()=>{db.close();resolve()};tx.onabort=tx.onerror=()=>{db.close();reject(tx.error??new Error('Local storage unavailable'))}})}
export async function pending():Promise<Pending[]>{const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction('pending');const req=tx.objectStore('pending').getAll();req.onsuccess=()=>resolve((req.result as Pending[]).sort((a,b)=>(a.sequence??0)-(b.sequence??0)||a.operation.client_time.localeCompare(b.operation.client_time)));req.onerror=()=>reject(req.error);tx.oncomplete=()=>db.close()})}
export async function savePending(value:Pending){
 const db=await openDb()
 return new Promise<void>((resolve,reject)=>{
  const tx=db.transaction(['meta','pending'],'readwrite'),store=tx.objectStore('pending'),meta=tx.objectStore('meta'),existing=store.get(value.operation.operation_id)
  existing.onsuccess=()=>{
   const previous=existing.result as Pending|undefined
   if(previous?.sequence!==undefined)store.put(clone({...value,sequence:previous.sequence}))
   else{const counter=meta.get('queue-sequence');counter.onsuccess=()=>{const sequence=Number(counter.result??0)+1;meta.put(sequence,'queue-sequence');store.put(clone({...value,sequence}))}}
  }
  tx.oncomplete=()=>{db.close();resolve()};tx.onabort=tx.onerror=()=>{db.close();reject(tx.error??new Error('Could not save this action on this device.'))}
 })
}
export async function removePending(id:string){const db=await openDb();return new Promise<void>((resolve,reject)=>{const tx=db.transaction('pending','readwrite');tx.objectStore('pending').delete(id);tx.oncomplete=()=>{db.close();resolve()};tx.onabort=tx.onerror=()=>{db.close();reject(tx.error)}})}

import type { Snapshot } from '../api/models'
export interface CachedSnapshot extends Snapshot { lastSync:string }
export async function commitCache(value:CachedSnapshot,replace=false):Promise<CachedSnapshot>{
 const db=await openDb()
 return new Promise((resolve,reject)=>{
  const tx=db.transaction('meta','readwrite'),store=tx.objectStore('meta'),get=store.get('cache');let chosen=value
  get.onsuccess=()=>{const previous=get.result as CachedSnapshot|undefined;if(!replace&&previous&&previous.cursor>value.cursor)chosen=previous;else store.put(clone(value),'cache')}
  tx.oncomplete=()=>{db.close();resolve(chosen)};tx.onabort=tx.onerror=()=>{db.close();reject(tx.error??new Error('Could not save the latest household records.'))}
 })
}
