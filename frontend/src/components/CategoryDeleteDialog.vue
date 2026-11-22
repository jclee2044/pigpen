<script setup lang="ts">
import type { Category } from '../api/models'
import { monthRevision } from '../lib/categoryMonths'
import { ref } from 'vue'
import { mutate,state } from '../state/household'
import { useSubmission } from '../lib/submission'
import AppDialog from './AppDialog.vue'
import AppLoading from './AppLoading.vue'
const props=defineProps<{category:Category;month:string}>()
const revision=ref(monthRevision(state.records,props.month))
const emit=defineEmits<{close:[];deleted:[]}>()
const {saving,error,retryId,run}=useSubmission()
function close(){if(!saving.value&&!retryId.value)emit('close')}
async function remove(){
 if(!state.online)return
 await run(()=>mutate('category.include',{month:props.month,included:false,expected_revision:revision.value},props.category.id),()=>emit('deleted'))
}
</script>
<template>
 <AppDialog title="Remove category?" @close="close">
  <AppLoading v-if="saving" compact />
  <p>Remove “{{category.name}}”? Existing allocations and spending stay in the budget history.</p>
  <p v-if="category.allows_subcategories" class="text-small">Its subcategories will also be removed from purchase choices.</p>
  <div v-if="error" role="alert" class="notice error">{{error}}</div>
  <p v-if="!state.online" class="notice">Reconnect to remove this category.</p>
  <div class="actions">
   <button class="button" :disabled="saving||!!retryId" @click="close">Cancel</button>
   <button class="button danger" :disabled="saving||!state.online" @click="remove">{{saving?'Removing…':retryId?'Retry removal':'Remove'}}</button>
  </div>
 </AppDialog>
</template>
