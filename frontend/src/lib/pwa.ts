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

/** Check on app opening, foregrounding or pull-to-refresh; activation remains the caller's decision. */
export async function checkForAppUpdate():Promise<boolean>{
 if(!import.meta.env.PROD||!registration||!navigator.onLine)return false
 if(registration.waiting){pwa.updateAvailable=true;return true}
 let timer:ReturnType<typeof setTimeout>|undefined
 try{
  // A stalled update request must not leave the refresh wheel spinning forever.
  const checked=await Promise.race([
   registration.update().then(()=>true),
   new Promise<false>(resolve=>{timer=setTimeout(()=>resolve(false),10000)}),
  ])
  clearTimeout(timer)
  if(!checked)return false
  const worker=registration.installing
  if(worker&&worker.state!=='installed'&&worker.state!=='redundant'){
   await new Promise<void>(resolve=>{
    const finish=()=>{clearTimeout(timer);worker.removeEventListener('statechange',change);resolve()}
    const change=()=>{if(worker.state==='installed'||worker.state==='redundant')finish()}
    worker.addEventListener('statechange',change)
    timer=setTimeout(finish,10000)
    change()
   })
  }
  pwa.updateAvailable=!!registration.waiting
  return pwa.updateAvailable
 }catch{
  // Data has already synced; an unavailable app download can be retried later.
  return false
 }finally{clearTimeout(timer)}
}

export function applyUpdate(){if(registration?.waiting){updating=true;registration.waiting.postMessage({type:'ACTIVATE'})}}
export function standalone(){return matchMedia('(display-mode: standalone)').matches||Boolean((navigator as Navigator&{standalone?:boolean}).standalone)}
export function isIos(){return /iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1)}
