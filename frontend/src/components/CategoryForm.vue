<script setup lang="ts">
import AppLoading from './AppLoading.vue'
import { computed,ref } from 'vue'
import type { Category } from '../api/models'
import { mutate,rows,activeUser,state } from '../state/household'
import { useSubmission } from '../lib/submission'
import AppDialog from './AppDialog.vue'
import CategoryDeleteDialog from './CategoryDeleteDialog.vue'
const props=defineProps<{category?:Category;sharedOnly?:boolean;parentCategory?:Category}>(),emit=defineEmits<{close:[]}>()
const name=ref(props.category?.name??''),kind=ref<'expense'|'personal'|'subcategory'>(props.parentCategory?'subcategory':'expense'),parent=ref(props.parentCategory?.id??''),active=ref(props.category?.active??true)
const deleting=ref(false)
const canDelete=computed(()=>props.category?.active&&(!props.category.owner_id||props.category.owner_id===activeUser.value?.id)&&!(props.category.kind==='personal'&&!props.category.parent_id))
const allows=ref(props.category?.allows_subcategories??false)
const parents=computed(()=>rows('categories').filter(c=>c.active&&!c.parent_id&&(
 c.kind==='expense'&&c.allows_subcategories||!props.sharedOnly&&c.kind==='personal'&&c.owner_id===activeUser.value?.id)))
const hasChildren=computed(()=>!!props.category&&rows('categories').some(c=>c.parent_id===props.category?.id))
const {saving,error,retryId,run}=useSubmission()
async function save(){await run(()=>{
 if(props.category)return mutate('category.update',{name:name.value,active:active.value,expected_revision:props.category.revision,...(props.category.kind==='expense'&&!props.category.parent_id?{allows_subcategories:allows.value}:{})},props.category.id)
 const selected=kind.value==='personal'?parents.value.find(c=>c.kind==='personal'):parents.value.find(c=>c.id===parent.value)
 const child=kind.value!=='expense'
 if(child&&!selected)throw new Error('Choose a parent category.')
 return mutate('category.create',{name:name.value,kind:child?selected!.kind as 'expense'|'personal':'expense',owner_id:child?selected!.owner_id:null,parent_id:child?selected!.id:null,allows_subcategories:!child&&allows.value})
},()=>emit('close'))}
</script>
<template><CategoryDeleteDialog v-if="deleting&&category" :category="category" @close="deleting=false" @deleted="emit('close')" /><AppDialog v-else :title="category?'Edit category':parentCategory?'Add subcategory':'Make room for something new'" @close="emit('close')"><AppLoading v-if="saving" compact /><form @submit.prevent="save"><div v-if="error" class="notice error" role="alert">{{error}}</div><fieldset :disabled="saving||!!retryId"><label>Category name<input v-model="name" required maxlength="200" /></label><label v-if="!category&&!parentCategory">Category type<select v-model="kind"><option value="expense">Shared expense</option><option v-if="!sharedOnly" value="personal">My Personal subcategory</option><option v-if="!sharedOnly&&parents.length" value="subcategory">Subcategory</option></select></label><label v-if="!category&&kind==='subcategory'">Parent category<select aria-label="Parent category" v-model="parent" required :disabled="!!parentCategory"><option value="" disabled>Choose a category</option><option v-for="c in parents" :key="c.id" :value="c.id">{{c.name}}</option></select></label><template v-if="(!category&&kind==='expense')||(category?.kind==='expense'&&!category.parent_id)"><label class="check-label"><input v-model="allows" type="checkbox" :disabled="hasChildren" />Allow subcategories</label><p v-if="hasChildren" class="text-small">Subcategories are enabled while this category has children.</p></template><p v-if="!category&&kind!=='expense'||allows" class="text-small">Subcategories share their parent budget.</p><label v-if="category&&!(category.kind==='personal'&&!category.parent_id)" class="check-label"><input v-model="active" type="checkbox" />Available for new entries</label></fieldset><button class="button primary" :disabled="saving">{{saving?'Saving…':retryId?'Retry saved submission':'Save category'}}</button><button v-if="canDelete" type="button" class="button danger delete-action" :disabled="saving||!!retryId||!state.online" @click="deleting=true">Delete category</button></form></AppDialog></template>
<style scoped>
.delete-action{margin-left:8px;margin-top:12px}
</style>
