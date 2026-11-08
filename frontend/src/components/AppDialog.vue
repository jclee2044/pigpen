<script setup lang="ts">
import { ref,onMounted,useId } from 'vue'
import AppIcon from './AppIcon.vue'
defineProps<{ title:string; centered?:boolean; small?:boolean }>()
const emit=defineEmits<{close:[]}>()
const titleId=useId()
const dialog=ref<HTMLDialogElement>()
onMounted(()=>dialog.value?.showModal())
</script>
<template><Teleport to="body"><dialog ref="dialog" :class="{'dialog-centered':centered,'dialog-small':small}" :aria-labelledby="titleId" @cancel.prevent="emit('close')" @click="e=>{if(e.target===dialog)emit('close')}"><div class="dialog-head"><h2 :id="titleId">{{title}}</h2><button type="button" class="icon-button" aria-label="Close dialog" @click="emit('close')"><AppIcon name="close" /></button></div><slot /></dialog></Teleport></template>

<style scoped>
.dialog-small{width:min(320px,calc(100% - 32px))}
.dialog-centered{position:fixed;inset:0;margin:auto}
</style>
