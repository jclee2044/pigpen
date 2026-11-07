<script setup lang="ts">
import { RouterLink,RouterView } from 'vue-router'
import { onMounted,onUnmounted,computed } from 'vue'
import { state,boot,activeUser,household,refresh,setError,synchronize,startSynchronization } from './state/household'
import ProfilesView from './views/ProfilesView.vue'
import PendingPanel from './components/PendingPanel.vue'
import { registerPwa,pwa,applyUpdate } from './lib/pwa'
let stopSync:(()=>void)|undefined
onMounted(async()=>{void registerPwa();await boot();stopSync=startSynchronization();if(state.hasCache)void synchronize()})
onUnmounted(()=>stopSync?.())
const unread=computed(()=>state.records.notifications.filter(n=>!n.deleted&&!n.read_at&&n.recipient_id===activeUser.value?.id).length)
const dataSource=computed(()=>!state.online?'Saved data':state.environment==='production'?'Live data':state.environment==='development'?'Development data':'Test data')
import AppIcon from './components/AppIcon.vue'
import HouseholdMenu from './components/HouseholdMenu.vue'
import horizontalLogo from './assets/pigpen-horizontal.png'
const nav=[['/','Dashboard','home'],['/purchases','Purchases','receipt'],['/budget','Budget','budget'],['/wish-lists','Wish lists','heart'],['/approvals','Approvals','shield']]
</script>
<template>
 <a href="#main" class="skip-link">Skip to content</a>
 <header class="app-header"><RouterLink to="/" class="wordmark" aria-label="PigPen home"><img :src="horizontalLogo" alt="" width="2172" height="724" /></RouterLink><div class="header-actions"><RouterLink to="/notifications" class="icon-button" aria-label="Notifications"><AppIcon name="bell" /><span v-if="unread" class="notification-dot" :aria-label="unread+' unread notifications'">{{unread>9?'9+':unread}}</span></RouterLink><HouseholdMenu :profile="activeUser" :household-name="household?.name" /></div></header>
 <aside class="sidebar"><p class="eyebrow">OUR HOUSEHOLD</p><nav aria-label="Main navigation"><RouterLink v-for="[path,label,icon] in nav" :key="path" :to="path!" :exact-active-class="'active'"><AppIcon :name="icon!" /><span>{{label}}</span></RouterLink></nav></aside>
 <main id="main" tabindex="-1"><div v-if="pwa.updateAvailable" class="notice" role="status">Update available. Saved changes will be preserved. <button class="button small" @click="applyUpdate">Update app</button></div><div v-if="state.error" role="alert" class="notice error">{{state.error}} <button class="button small" @click="refresh().then(()=>state.error='').catch(setError)">Retry connection</button> <button class="icon-button" aria-label="Dismiss error" @click="state.error=''">×</button></div><div v-if="state.notice" class="notice success" role="status">{{state.notice}} <button class="icon-button" aria-label="Dismiss message" @click="state.notice=''">×</button></div><div v-if="!state.booted" class="card empty" role="status">Loading…</div><template v-else-if="state.hasCache"><div class="status-strip"><span v-if="state.environment" class="data-source">{{dataSource}}</span><span class="status-dot" :class="{offline:!state.online}" /><span>{{state.syncing?'Syncing…':state.online?'Connected':'Offline · saved on this device'}}</span><span v-if="state.lastSync">Last synced {{new Date(state.lastSync).toLocaleString()}}</span><button class="inline-link" :disabled="state.syncing" @click="synchronize">Sync now</button></div><PendingPanel /><ProfilesView v-if="!household||!activeUser" /><RouterView v-else /></template><section v-else class="card empty"><h1>Unable to connect</h1><p>Connect to your household server to open PigPen for the first time.</p></section></main>
 <nav class="mobile-nav" aria-label="Mobile navigation"><RouterLink v-for="[path,label,icon] in nav" :key="path" :to="path!" exact-active-class="active"><AppIcon :name="icon!" /><span>{{label}}</span></RouterLink></nav>
</template>
<style src="./style.css"></style>
