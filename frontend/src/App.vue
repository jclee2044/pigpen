<script setup lang="ts">
import { RouterLink,RouterView } from 'vue-router'
import { onMounted,onUnmounted,computed } from 'vue'
import { state,boot,activeUser,household,refresh,setError,synchronize,startSynchronization } from './state/household'
import AppLoading from './components/AppLoading.vue'
import ProfilesView from './views/ProfilesView.vue'
import PendingPanel from './components/PendingPanel.vue'
import { registerPwa,applyUpdate,checkForAppUpdate } from './lib/pwa'
let stopSync:(()=>void)|undefined
let pwaRegistration:Promise<void>
let refreshInFlight:Promise<void>|undefined
onMounted(async()=>{pwaRegistration=registerPwa();await boot();stopSync=startSynchronization(()=>refreshApp(false));if(state.hasCache)void refreshApp(false)})
onUnmounted(()=>stopSync?.())
import AppIcon from './components/AppIcon.vue'
import HouseholdMenu from './components/HouseholdMenu.vue'
import BrandLogo from './components/BrandLogo.vue'
import PullToRefresh from './components/PullToRefresh.vue'
import NotificationBanner from './components/NotificationBanner.vue'
import NotificationPrompt from './components/NotificationPrompt.vue'
import MobileNavigation from './components/MobileNavigation.vue'
const entered=computed(()=>state.booted&&state.hasCache&&!!household.value&&!!activeUser.value)
function refreshApp(pulled=true):Promise<void>{
 if(refreshInFlight)return pulled?refreshInFlight.then(()=>refreshApp()):refreshInFlight
 refreshInFlight=syncAndUpdate(pulled).finally(()=>{refreshInFlight=undefined})
 return refreshInFlight
}
async function syncAndUpdate(pulled:boolean){
 const started=performance.now()
 await synchronize()
 if(!state.online||state.error||state.pending.length)return
 await pwaRegistration
 const available=await checkForAppUpdate()
 if(available){
  if(pulled)await new Promise(resolve=>setTimeout(resolve,Math.max(0,650-(performance.now()-started))))
  if(state.booted&&!state.busy&&!state.syncing&&!state.pending.length&&!state.error&&document.visibilityState==='visible'&&!document.querySelector('dialog[open],[data-defer-app-update]')&&!document.activeElement?.matches('input,textarea,select,[contenteditable]'))applyUpdate()
 }
}
const nav=[['/','Dashboard','home'],['/purchases','Purchases','receipt'],['/budget','Budget','budget'],['/wish-lists','Wish lists','heart'],['/approvals','Approvals','shield']]
</script>
<template>
 <a href="#main" class="skip-link">Skip to content</a>
 <PullToRefresh :class="{'app-entered':entered}" @error="setError" :refresh="refreshApp" :disabled="!entered||state.busy">
 <template #header><header v-if="entered" class="app-header"><RouterLink to="/" class="wordmark" aria-label="PigPen home"><BrandLogo /></RouterLink><div class="header-actions"><HouseholdMenu :profile="activeUser" :household-name="household?.name" /></div></header></template>
 <main id="main" tabindex="-1" :class="{'entry-screen':!entered,'loading-screen':!state.booted}"><div v-if="state.error" role="alert" class="notice error">{{state.error}} <button class="button small" @click="refresh().then(()=>state.error='').catch(setError)">Retry connection</button> <button class="icon-button" aria-label="Dismiss error" @click="state.error=''">×</button></div><div v-if="state.notice" class="notice success" role="status">{{state.notice}} <button class="icon-button" aria-label="Dismiss message" @click="state.notice=''">×</button></div><AppLoading v-if="!state.booted" class="card startup-loading" /><template v-else-if="state.hasCache"><p v-if="!state.online" class="notice" role="status">Offline · saved on this device</p><PendingPanel /><ProfilesView v-if="!household||!activeUser" entry /><RouterView v-else /></template><section v-else class="card empty"><h1>Unable to connect</h1><p>Connect to your household server to open PigPen for the first time.</p></section></main>
 </PullToRefresh>
 <AppLoading v-if="state.booted&&state.hasCache&&state.syncing" compact class="sync-loading" />
 <aside v-if="entered" class="sidebar"><p class="eyebrow">OUR HOUSEHOLD</p><nav aria-label="Main navigation"><RouterLink v-for="[path,label,icon] in nav" :key="path" :to="path!" :exact-active-class="'active'"><AppIcon :name="icon!" /><span>{{label}}</span></RouterLink></nav></aside>
 <MobileNavigation v-if="entered" />
 <NotificationBanner v-if="entered" />
 <NotificationPrompt v-if="entered" />
</template>
<style src="./style.css"></style>
