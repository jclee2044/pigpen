<script setup lang="ts">
import { nextTick,onMounted,onUnmounted,ref } from 'vue'
import AppIcon from './AppIcon.vue'

const emit=defineEmits<{scan:[];manual:[]}>()
const mobileQuery=window.matchMedia('(pointer: coarse)')
const mobile=ref(mobileQuery.matches)
function updateMobile(){mobile.value=mobileQuery.matches}
const open=ref(false)
const container=ref<HTMLElement>()
const trigger=ref<HTMLButtonElement>()
const panel=ref<HTMLElement>()
function close(restoreFocus=false){
 open.value=false
 if(restoreFocus)trigger.value?.focus()
}
async function focusFirst(){
 open.value=true
 await nextTick()
 panel.value?.querySelector<HTMLButtonElement>('button')?.focus()
}
function outside(event:PointerEvent){
 if(event.target instanceof Node&&!container.value?.contains(event.target))close()
}
function leave(event:FocusEvent){
 if(!(event.relatedTarget instanceof Node)||!container.value?.contains(event.relatedTarget))close()
}
function choose(action:'scan'|'manual'){
 close(true)
 if(action==='scan')emit('scan')
 else emit('manual')
}
onMounted(()=>{document.addEventListener('pointerdown',outside);mobileQuery.addEventListener('change',updateMobile)})
onUnmounted(()=>{document.removeEventListener('pointerdown',outside);mobileQuery.removeEventListener('change',updateMobile)})
</script>

<template>
 <div ref="container" class="purchase-add" @keydown.esc.stop.prevent="close(true)" @focusout="leave">
  <button ref="trigger" type="button" class="button primary icon-only" aria-label="New purchase" title="New purchase" :aria-expanded="open" aria-controls="purchase-add-options" @click="open=!open" @keydown.down.prevent="focusFirst"><AppIcon name="plus" /></button>
  <Transition name="household-dropdown">
  <div v-if="open" :inert="!open" :aria-hidden="!open||undefined" id="purchase-add-options" ref="panel" class="purchase-add-options" role="group" aria-label="New purchase options">
   <button v-if="mobile" type="button" @click="choose('scan')">Scan receipt</button>
   <button type="button" @click="choose('manual')">Enter manually</button>
  </div>
  </Transition>
 </div>
</template>

<style scoped>
.purchase-add{position:relative;display:flex}
.purchase-add-options{position:absolute;right:0;top:100%;z-index:20;width:190px;max-width:calc(100vw - 32px);padding:6px;background:var(--paper);border:1px solid var(--line);border-radius:14px;box-shadow:0 8px 28px #3d333118;transform-origin:top right}
.purchase-add-options button{display:block;width:100%;min-height:44px;padding:10px 12px;border:0;border-radius:8px;background:transparent;color:var(--ink);font:inherit;font-size:14px;text-align:left;cursor:pointer}
.purchase-add-options button:hover,.purchase-add-options button:focus-visible{background:var(--blush);color:var(--rose-dark)}
</style>
