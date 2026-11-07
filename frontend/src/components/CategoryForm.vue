<script setup lang="ts">
import { ref } from 'vue'
import type { Category } from '../api/models'
import { mutate,rows,activeUser } from '../state/household'
import { useSubmission } from '../lib/submission'
import AppDialog from './AppDialog.vue'
const props=defineProps<{category?:Category}>(),emit=defineEmits<{close:[]}>()
const name=ref(props.category?.name??''),kind=ref<'expense'|'personal'>('expense'),parent=ref(rows('categories').find(x=>x.kind==='personal'&&!x.parent_id&&x.owner_id===activeUser.value?.id)?.id??''),active=ref(props.category?.active??true)
const {saving,error,retryId,run}=useSubmission()
async function save(){await run(()=>props.category?mutate('category.update',{name:name.value,active:active.value,expected_revision:props.category.revision},props.category.id):mutate('category.create',{name:name.value,kind:kind.value,owner_id:kind.value==='personal'?activeUser.value!.id:null,parent_id:kind.value==='personal'?parent.value:null}),()=>emit('close'))}
</script>
<template><AppDialog :title="category?'Edit category':'Make room for something new'" @close="emit('close')"><form @submit.prevent="save"><div v-if="error" class="notice error" role="alert">{{error}}</div><fieldset :disabled="saving||!!retryId"><label>Category name<input v-model="name" required maxlength="200" /></label><label v-if="!category">Category type<select v-model="kind"><option value="expense">Shared expense</option><option value="personal">My Personal subcategory</option></select></label><p v-if="!category&&kind==='personal'" class="text-small">Spending counts toward your Personal allowance. Subcategories have no separate allocation.</p><label v-if="category&&!(category.kind==='personal'&&!category.parent_id)" class="check-label"><input v-model="active" type="checkbox" />Available for new entries</label></fieldset><button class="button primary" :disabled="saving">{{saving?'Saving…':retryId?'Retry saved submission':'Save category'}}</button></form></AppDialog></template>
