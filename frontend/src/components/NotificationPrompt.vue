<script setup lang="ts">
import AppLoading from './AppLoading.vue'
import { computed,onMounted,onUnmounted,ref,watch } from 'vue'
import { state } from '../state/household'
import { getPushConfig,enablePush,type PushConfig } from '../lib/push'
import { isIos,standalone,pwa } from '../lib/pwa'
import AppIcon from './AppIcon.vue'
const dialog=ref<HTMLDialogElement>(),config=ref<PushConfig>(),working=ref(false),error=ref('')
const needsInstall=isIos()&&!standalone()
const supported=window.isSecureContext&&'Notification' in window&&'PushManager' in window&&'serviceWorker' in navigator
// Safari installation guidance must not suppress the later installed-app permission prompt.
const storageKey='pigpen.notification-prompt.'+(needsInstall?'install':'permission')
const dismissed=ref(false)
try{dismissed.value=localStorage.getItem(storageKey)==='seen'}catch{/* Keep this visit usable when storage is unavailable. */}
const pending=computed(()=>state.pending.some(x=>x.operation.kind.startsWith('subscription.')))
const eligible=computed(()=>!dismissed.value&&state.online&&config.value?.enabled&&(needsInstall||(supported&&pwa.ready&&Notification.permission==='default')))
function dismiss(){
 dismissed.value=true
 try{localStorage.setItem(storageKey,'seen')}catch{/* Dismiss for this visit even if storage is unavailable. */}
 dialog.value?.close()
}
async function load(){
 if(dismissed.value||!state.online||(!needsInstall&&!supported))return
 try{config.value=await getPushConfig()}catch{/* Retry when connectivity returns. */}
}
onMounted(load)
watch(()=>state.online,online=>{if(online)void load()})
watch([eligible,dialog],()=>{if(eligible.value&&!dialog.value?.open)dialog.value?.showModal()})
onUnmounted(()=>dialog.value?.close())
async function enable(){
 if(!config.value?.public_key)return
 working.value=true;error.value=''
 try{await enablePush(config.value.public_key);dismiss()}catch(e){error.value=e instanceof Error?e.message:'Could not enable notifications. Try again in Settings.'}finally{working.value=false}
}
</script>
<template>
 <dialog ref="dialog" class="notification-prompt" aria-labelledby="notification-prompt-title" aria-describedby="notification-prompt-description" @cancel.prevent="!working&&dismiss()">
  <div class="prompt-icon"><AppIcon name="bell" /></div>
  <h2 id="notification-prompt-title">Enable notifications?</h2>
  <p id="notification-prompt-description">Get notified about approval requests, comments, and household updates. Notifications show who did what and relevant item names, without amounts, prices, balances, or other financial numbers.</p>
  <p v-if="needsInstall">In Safari, tap Share → Add to Home Screen. Then open PigPen from that icon to enable notifications.</p>
  <p v-else class="text-small">You can change this later in Settings.</p>
  <p v-if="error" class="notice error" role="alert">{{error}}</p>
  <div class="actions">
   <AppLoading v-if="working" compact />
   <button v-if="!needsInstall" class="button primary" :disabled="working||pending||!state.online||!config?.public_key" @click="enable">{{working?'Enabling…':'Enable notifications'}}</button>
   <button class="button" :disabled="working" @click="dismiss">{{needsInstall?'Got it':'Not now'}}</button>
  </div>
 </dialog>
</template>
<style scoped>
.notification-prompt{position:fixed;inset:0;margin:auto;overflow:auto;width:min(420px,calc(100% - 32px));padding:28px;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);box-shadow:0 16px 60px #0003}
.notification-prompt::backdrop{background:#0006}
.prompt-icon{display:grid;place-items:center;width:48px;height:48px;margin-bottom:20px;border-radius:14px;background:var(--blush);color:var(--rose)}
.notification-prompt h2{margin-bottom:12px}
.notification-prompt .actions{margin-top:24px}
</style>
