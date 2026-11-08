<script setup lang="ts">
import type { Category } from '../api/models'
import { mutate,state } from '../state/household'
import { useSubmission } from '../lib/submission'
import AppDialog from './AppDialog.vue'
import AppLoading from './AppLoading.vue'
const props=defineProps<{category:Category}>()
const emit=defineEmits<{close:[];deleted:[]}>()
const {saving,error,retryId,run}=useSubmission()
function close(){if(!saving.value&&!retryId.value)emit('close')}
async function remove(){
 if(!state.online)return
 await run(()=>mutate('category.update',{name:props.category.name,active:false,expected_revision:props.category.revision},props.category.id),()=>emit('deleted'))
}
</script>
<template>
 <AppDialog title="Delete category?" @close="close">
  <AppLoading v-if="saving" compact />
  <p>Delete “{{category.name}}” from available categories? Past purchases and saved budgets keep their history. Future months will skip this category. You can restore it in Manage categories.</p>
  <p v-if="category.allows_subcategories" class="text-small">Its subcategories cannot be used for new entries while this category is archived.</p>
  <div v-if="error" role="alert" class="notice error">{{error}}</div>
  <p v-if="!state.online" class="notice">Reconnect to delete this category.</p>
  <div class="actions">
   <button class="button" :disabled="saving||!!retryId" @click="close">Cancel</button>
   <button class="button danger" :disabled="saving||!state.online" @click="remove">{{saving?'Deleting…':retryId?'Retry deletion':'Delete category'}}</button>
  </div>
 </AppDialog>
</template>
