<script setup lang="ts">
import { computed,nextTick,onMounted,onUnmounted,ref,watch } from 'vue'
import { RouterLink,useRoute } from 'vue-router'
import type { User } from '../api/models'
import { state,activeUser } from '../state/household'
import AppIcon from './AppIcon.vue'
import PigAvatar from './PigAvatar.vue'

defineProps<{profile?:User;householdName?:string}>()
const unread=computed(()=>state.records.notifications.filter(n=>!n.deleted&&!n.read_at&&n.recipient_id===activeUser.value?.id).length)
const route=useRoute()
const open=ref(false)
const container=ref<HTMLElement>()
const trigger=ref<HTMLButtonElement>()
const panel=ref<HTMLElement>()

function close(restoreFocus=false){
 open.value=false
 if(restoreFocus)trigger.value?.focus()
}
async function focusLink(){
 open.value=true
 await nextTick()
 panel.value?.querySelector<HTMLAnchorElement>('a')?.focus()
}
function outside(event:PointerEvent){
 if(event.target instanceof Node&&!container.value?.contains(event.target))close()
}
function leave(event:FocusEvent){
 if(!(event.relatedTarget instanceof Node)||!container.value?.contains(event.relatedTarget))close()
}
watch(()=>route.fullPath,()=>close())
onMounted(()=>document.addEventListener('pointerdown',outside))
onUnmounted(()=>document.removeEventListener('pointerdown',outside))
</script>

<template>
 <div ref="container" class="household-menu" @keydown.esc.stop.prevent="close(true)" @focusout="leave">
  <button ref="trigger" type="button" class="profile-link household-trigger" aria-label="Our household" :aria-expanded="open" aria-controls="household-navigation" @click="open=!open" @keydown.down.prevent="focusLink">
   <PigAvatar :avatar="profile?.avatar" />
   <span class="household-label"><strong>Our household</strong><small data-testid="selected-profile">{{profile?.name||householdName||'Choose a profile'}}</small><AppIcon name="arrow" class="household-chevron" /></span>
  </button>
  <Transition name="household-dropdown">
  <nav v-if="open" :inert="!open" :aria-hidden="!open||undefined" id="household-navigation" ref="panel" class="household-dropdown" aria-label="Household settings">
   <RouterLink to="/profiles" @click="close()"><AppIcon name="profiles" /><span>Profiles</span></RouterLink>
   <RouterLink to="/notifications" @click="close()"><AppIcon name="bell" /><span>Notifications</span><span v-if="unread" class="notification-count" :aria-label="unread+' unread notifications'">{{unread>99?'99+':unread}}</span></RouterLink>
   <RouterLink to="/settings" @click="close()"><AppIcon name="settings" /><span>Settings</span></RouterLink>
  </nav>
  </Transition>
 </div>
</template>
