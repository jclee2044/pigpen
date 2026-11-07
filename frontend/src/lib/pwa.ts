import { reactive } from 'vue'
export const pwa=reactive({ready:false,updateAvailable:false,error:''})
let registration:ServiceWorkerRegistration|undefined
let updating=false
export async function registerPwa(){
 if(!import.meta.env.PROD||!('serviceWorker' in navigator))return
 try{
  registration=await navigator.serviceWorker.register('/sw.js',{scope:'/',updateViaCache:'none'})
  pwa.updateAvailable=!!registration.waiting
  registration.addEventListener('updatefound',()=>{const worker=registration?.installing;worker?.addEventListener('statechange',()=>{if(worker.state==='installed'&&navigator.serviceWorker.controller)pwa.updateAvailable=true})})
  navigator.serviceWorker.addEventListener('controllerchange',()=>{pwa.ready=true;if(updating)location.reload()})
  await navigator.serviceWorker.ready;pwa.ready=true
 }catch{pwa.error='Offline installation could not finish. Reconnect and reload to try again.'}
}
export function applyUpdate(){if(registration?.waiting){updating=true;registration.waiting.postMessage({type:'ACTIVATE'})}}
export function standalone(){return matchMedia('(display-mode: standalone)').matches||Boolean((navigator as Navigator&{standalone?:boolean}).standalone)}
export function isIos(){return /iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1)}
