<script setup lang="ts">
import { computed,ref,onMounted,watch } from 'vue'
import { ApiError } from '../api/client'
import { state,activeUser } from '../state/household'
import { getPushConfig,getPushBinding,enablePush,disablePush,type PushConfig } from '../lib/push'
import { pwa,isIos,standalone } from '../lib/pwa'
const config=ref<PushConfig>(),enabled=ref(false),working=ref(false),error=ref(''),loaded=ref(false)
const supported=window.isSecureContext&&'Notification' in window&&'PushManager' in window&&'serviceWorker' in navigator
const needsInstall=isIos()&&!standalone()
const pending=computed(()=>state.pending.some(x=>x.operation.kind.startsWith('subscription.')))
async function load(){if(!supported)return;try{config.value=await getPushConfig();const registration=await navigator.serviceWorker.getRegistration();const browser=await registration?.pushManager.getSubscription();const binding=await getPushBinding().catch(e=>{if(e instanceof ApiError&&e.status===404)return null;throw e});enabled.value=!!browser&&!!binding?.subscription?.active;loaded.value=true;error.value=''}catch{error.value='Reconnect and sync your profile to check notification settings.'}}
onMounted(load)
watch([()=>state.pending.length,()=>state.syncing,()=>state.selectedId,()=>pwa.ready],()=>{if(!pending.value&&!state.syncing&&state.online)void load()})
async function change(enable:boolean){working.value=true;error.value='';try{if(enable&&config.value?.public_key)await enablePush(config.value.public_key);else await disablePush();await load()}catch(e){error.value=e instanceof Error?e.message:'Notification settings could not be saved.'}finally{working.value=false}}
</script>
<template><section v-if="activeUser" class="card section-space"><h2>Push notifications</h2><p>Receive household updates for {{activeUser.name}} on this device. Notifications contain no purchase or budget details.</p><p v-if="!supported">This browser does not support push notifications. Your notification inbox is always available.</p><p v-else-if="needsInstall">Add PigPen to your iPhone home screen, open the installed app, then enable notifications here.</p><p v-else-if="config&&!config.enabled">Push delivery is not configured on your household server yet. Your notification inbox still works.</p><template v-else><p>{{enabled?'Notifications are enabled for the selected profile.':'Notifications are off on this device.'}}</p><button class="button" :disabled="!loaded||!state.online||!pwa.ready||working||pending||!config?.enabled" @click="change(!enabled)">{{working?'Saving…':enabled?'Turn off notifications':'Enable notifications'}}</button></template><p v-if="pending" class="text-small">Your saved notification change is waiting to be confirmed. Use Sync now to retry it.</p><p v-if="error" role="alert" class="notice error">{{error}}</p></section></template>
