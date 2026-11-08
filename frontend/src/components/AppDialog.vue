<script setup lang="ts">
import { ref,onMounted } from 'vue'
import AppIcon from './AppIcon.vue'
defineProps<{ title:string; centered?:boolean }>()
const emit=defineEmits<{close:[]}>()
const dialog=ref<HTMLDialogElement>()
onMounted(()=>dialog.value?.showModal())
</script>
<template><Teleport to="body"><dialog ref="dialog" :class="{'dialog-centered':centered}" aria-labelledby="dialog-title" @cancel.prevent="emit('close')" @click="e=>{if(e.target===dialog)emit('close')}"><div class="dialog-head"><h2 id="dialog-title">{{title}}</h2><button type="button" class="icon-button" aria-label="Close dialog" @click="emit('close')"><AppIcon name="close" /></button></div><slot /></dialog></Teleport></template>

<style scoped>
.dialog-centered{position:fixed;inset:0;margin:auto}
</style>
