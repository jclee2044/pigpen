<script setup lang="ts">
import AppLoading from './AppLoading.vue'
import { computed,ref,onMounted,watch } from 'vue'
import { ApiError } from '../api/client'
import { state,activeUser } from '../state/household'
import { getPushConfig,getPushBinding,enablePush,disablePush,type PushConfig } from '../lib/push'
import { pwa,isIos,standalone } from '../lib/pwa'
const config=ref<PushConfig>(),enabled=ref(false),working=ref(false),error=ref(''),loaded=ref(false)
const supported=window.isSecureContext&&'Notification' in window&&'PushManager' in window&&'serviceWorker' in navigator
const needsInstall=isIos()&&!standalone()
const pending=computed(()=>state.pending.some(x=>x.operation.kind.startsWith('subscription.')))
async function load(){if(!supported)return;try{config.value=await getPushConfig();const registration=await navigator.serviceWorker.getRegistration();const browser=await registration?.pushManager.getSubscription();const binding=await getPushBinding().catch(e=>{if(e instanceof ApiError&&e.status===404)return null;throw e});enabled.value=Notification.permission==='granted'&&!!browser&&!!binding?.subscription?.active&&binding.installation.user_id===state.selectedId;loaded.value=true;error.value=''}catch{error.value='Reconnect and sync your profile to check notification settings.'}}
onMounted(load)
watch([()=>state.pending.length,()=>state.syncing,()=>state.selectedId,()=>pwa.ready],()=>{if(!pending.value&&!state.syncing&&state.online)void load()})
async function change(enable:boolean){working.value=true;error.value='';try{if(enable&&config.value?.public_key)await enablePush(config.value.public_key);else await disablePush();await load()}catch(e){error.value=e instanceof Error?e.message:'Notification settings could not be saved.'}finally{working.value=false}}
</script>
<template>
 <section v-if="activeUser" class="card section-space push-settings">
  <div class="push-settings-row">
   <h2>Push notifications</h2>
   <button class="push-switch" type="button" role="switch" aria-label="Push notifications" aria-describedby="push-privacy" :aria-checked="enabled" :aria-busy="working" :disabled="needsInstall||!supported||!loaded||!state.online||!pwa.ready||working||pending||!config?.enabled" @click="change(!enabled)">
    <span class="push-switch-track" aria-hidden="true"><span class="push-switch-thumb" /></span>
   </button>
  </div>
  <AppLoading v-if="working||(supported&&!needsInstall&&!loaded&&!error)" compact />
  <p id="push-privacy" class="push-help">Get alerts for approval requests, comments, and household updates. Notifications show who did what and relevant item names. Amounts, prices, balances, and other financial numbers are not included.</p>
  <p v-if="needsInstall" class="push-help">In Safari, tap Share → Add to Home Screen. Open PigPen from that icon to enable notifications.</p>
  <p v-else-if="!supported" class="push-help">This browser does not support push notifications. Your notification inbox is always available.</p>
  <p v-else-if="config&&!config.enabled" class="push-help">Push delivery is not configured on your household server yet. Your notification inbox still works.</p>
  <p v-if="pending" class="push-help" role="status">Your saved notification change is waiting to be confirmed. It will retry automatically while PigPen is open.</p>
  <p v-if="error" role="alert" class="notice error push-help">{{error}}</p>
 </section>
</template>

<style scoped>
.push-settings-row{display:flex;align-items:center;justify-content:space-between;gap:16px}
.push-settings-row h2{margin:0;font:500 16px/1.4 Arial,Helvetica,sans-serif;letter-spacing:0;color:var(--ink)}
.push-switch{display:flex;align-items:center;flex-shrink:0;width:56px;height:44px;padding:0;border:0;border-radius:22px;background:transparent}
.push-switch-track{display:block;position:relative;width:56px;height:34px;border-radius:20px;background:var(--track);box-shadow:inset 0 0 0 1px var(--field-line);transition:background .18s}
.push-switch-thumb{position:absolute;top:3px;left:3px;width:28px;height:28px;border-radius:50%;background:#fff;box-shadow:0 1px 4px #0003;transition:transform .18s}
.push-switch[aria-checked="true"] .push-switch-track{background:var(--rose);box-shadow:none}
.push-switch[aria-checked="true"] .push-switch-thumb{transform:translateX(22px)}
.push-help{font-size:13px;line-height:1.5;margin:12px 0 0}
@media(prefers-reduced-motion:reduce){.push-switch-track,.push-switch-thumb{transition:none}}
</style>
