<script setup lang="ts">
import { nextTick,onMounted,onUnmounted,ref,watch } from 'vue'
import { RouterLink,useRoute } from 'vue-router'
import type { User } from '../api/models'
import AppIcon from './AppIcon.vue'
import PigAvatar from './PigAvatar.vue'

defineProps<{profile?:User;householdName?:string}>()
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
   <span class="household-label"><strong>Our household</strong><small data-testid="selected-profile">{{profile?.name||householdName||'Choose a profile'}}</small></span>
   <AppIcon name="arrow" class="household-chevron" />
  </button>
  <nav v-if="open" id="household-navigation" ref="panel" class="household-dropdown" aria-label="Household settings">
   <RouterLink to="/profiles" @click="close()"><AppIcon name="settings" /><span>Profiles &amp; settings</span></RouterLink>
  </nav>
 </div>
</template>
