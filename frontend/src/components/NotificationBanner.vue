<script setup lang="ts">
import { onUnmounted,ref,watch } from 'vue'
import { RouterLink } from 'vue-router'
import { activeUser,state } from '../state/household'
import type { Note } from '../api/models'
import { noteLabel } from '../lib/notifications'
import AppIcon from './AppIcon.vue'

const current=ref<Note>()
let seen=new Set<string>()
let recipient=''
let queue:Note[]=[]
let timer:ReturnType<typeof setTimeout>|undefined
function advance(){
 clearTimeout(timer)
 current.value=queue.shift()
 if(current.value)timer=setTimeout(advance,6000)
}
watch(()=>[activeUser.value?.id,state.records.notifications] as const,([id,notes])=>{
 const relevant=notes.filter(n=>!n.deleted&&n.recipient_id===id)
 if(recipient!==id){
  recipient=id??'';seen=new Set(relevant.map(n=>n.id));queue=[];current.value=undefined;clearTimeout(timer);return
 }
 const fresh=relevant.filter(n=>!seen.has(n.id)&&!n.read_at)
 relevant.forEach(n=>seen.add(n.id))
 if(document.visibilityState!=='visible')return
 queue.push(...fresh.sort((a,b)=>a.created_at.localeCompare(b.created_at)))
 if(!current.value)advance()
},{immediate:true})
onUnmounted(()=>clearTimeout(timer))
</script>

<template>
 <Transition name="notification-banner">
  <aside v-if="current" :key="current.id" class="notification-banner" aria-label="New notification">
   <RouterLink :to="'/notifications?notification='+current.id" class="notification-banner-link" @click="advance">
    <span class="notification-banner-icon"><AppIcon name="bell" /></span>
    <span role="status"><strong>PigPen <small>now</small></strong><span>{{noteLabel(current)}}</span></span>
   </RouterLink>
   <button class="icon-button" aria-label="Dismiss notification" @click="advance">×</button>
  </aside>
 </Transition>
</template>

<style scoped>
.notification-banner{position:fixed;z-index:80;top:calc(var(--safe-area-top) + 8px);left:50%;transform:translateX(-50%);width:min(440px,calc(100% - 24px));display:flex;align-items:center;padding:8px;border:1px solid var(--line);border-radius:22px;background:var(--paper);color:var(--ink);box-shadow:0 8px 32px #0003}
.notification-banner-link{display:flex;align-items:center;gap:12px;flex:1;min-width:0;padding:8px;color:inherit}
.notification-banner-link>span:last-child{flex:1;min-width:0}
.notification-banner-icon{display:grid;place-items:center;width:40px;height:40px;flex:none;border-radius:12px;background:var(--blush);color:var(--rose)}
.notification-banner strong{display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:13px;margin-bottom:5px}
.notification-banner small{font-weight:400;font-size:12px}
.notification-banner-link span>span{font-size:14px;display:block}
.notification-banner .icon-button{flex:none}
.notification-banner-enter-active,.notification-banner-leave-active{transition:transform .22s,opacity .22s}
.notification-banner-enter-from,.notification-banner-leave-to{transform:translate(-50%,-120%);opacity:0}
@media(prefers-reduced-motion:reduce){.notification-banner-enter-active,.notification-banner-leave-active{transition:none}}
</style>
