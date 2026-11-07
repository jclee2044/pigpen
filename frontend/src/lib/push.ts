import { request } from '../api/client'
import { state,mutate,synchronize } from '../state/household'
export interface PushConfig {enabled:boolean;public_key:string|null}
interface Binding {installation:{user_id:string};subscription:{id:string;revision:number;active:boolean}|null}
export function applicationKey(value:string):Uint8Array<ArrayBuffer>{
 const raw=atob(value.replace(/-/g,'+').replace(/_/g,'/'))
 return Uint8Array.from(raw,x=>x.charCodeAt(0))
}
export const getPushConfig=()=>request<PushConfig>('/push-config')
export const getPushBinding=()=>request<Binding>('/installations/'+state.deviceId)
export async function enablePush(publicKey:string){
 // Keep the permission prompt directly within the user's click gesture.
 const permission=await Notification.requestPermission()
 if(permission!=='granted')throw new Error('Notifications were not allowed. You can change permission in your device settings.')
 const registration=await navigator.serviceWorker.ready
 const subscription=await registration.pushManager.getSubscription()??await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:applicationKey(publicKey)})
 await synchronize()
 const binding=await getPushBinding()
 if(binding.installation.user_id!==state.selectedId)throw new Error('Sync your selected profile before enabling notifications.')
 const value=subscription.toJSON()
 if(!value.endpoint||!value.keys?.p256dh||!value.keys?.auth)throw new Error('This browser did not provide a complete push subscription.')
 await mutate('subscription.set',{installation_id:state.deviceId,expected_revision:binding.subscription?.revision??0,endpoint:value.endpoint,p256dh:value.keys.p256dh,auth:value.keys.auth},binding.subscription?.id)
}
export async function disablePush(){
 const binding=await getPushBinding()
 if(binding.subscription?.active)await mutate('subscription.disable',{expected_revision:binding.subscription.revision},binding.subscription.id)
 const registration=await navigator.serviceWorker.getRegistration()
 await (await registration?.pushManager.getSubscription())?.unsubscribe()
}
