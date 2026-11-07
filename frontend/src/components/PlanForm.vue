<script setup lang="ts">
import { ref } from 'vue'
import type { Wish,Request } from '../api/models'
import { rows,mutate } from '../state/household'
import { inputMoney,parseMoney } from '../lib/money'
import { useSubmission } from '../lib/submission'
import AppDialog from './AppDialog.vue'
const props=defineProps<{kind:'wish'|'request';wish?:Wish;request?:Request;prefill?:Wish}>(),emit=defineEmits<{close:[]}>()
const name=ref(props.wish?.name??props.request?.item??props.prefill?.name??''),amount=ref(inputMoney(props.wish?.price_minor??props.request?.amount_minor??props.prefill?.price_minor??0)),description=ref(props.wish?.description??props.request?.description??props.prefill?.description??''),url=ref(props.wish?.url??props.request?.url??props.prefill?.url??''),category=ref(props.request?.category_id??''),status=ref(props.wish?.status??'active')
const {saving,error,retryId,run}=useSubmission()
async function save(){await run(()=>{
 if(props.kind==='wish'){const data={name:name.value,price_minor:parseMoney(amount.value),description:description.value,url:url.value||null};return props.wish?mutate('wishlist.update',{...data,status:status.value,expected_revision:props.wish.revision},props.wish.id):mutate('wishlist.create',data)}
 const data={item:name.value,amount_minor:parseMoney(amount.value,false),description:description.value,url:url.value||null,category_id:category.value||null}
 return props.request?mutate('request.update',{...data,expected_revision:props.request.revision},props.request.id):mutate('request.create',data)
},()=>emit('close'))}
</script>
<template><AppDialog :title="kind==='wish'?(wish?'Edit wish':'A little something to wish for'):(request?'Revise your request':'Ask the household')" @close="emit('close')"><form @submit.prevent="save"><div v-if="error" class="notice error" role="alert">{{error}}</div><fieldset :disabled="saving||!!retryId"><label>{{kind==='wish'?'Wish name':'Proposed purchase'}}<input v-model="name" required maxlength="200" /></label><label>{{kind==='wish'?'Price ($)':'Estimated amount ($)'}}<input v-model="amount" inputmode="decimal" required /></label><label>Description<textarea v-model="description" maxlength="4000" /></label><label>Link <span class="form-help">Optional</span><input v-model="url" type="url" placeholder="https://" /></label><label v-if="kind==='request'">Proposed category<select v-model="category"><option value="">Decide when purchased</option><option v-for="c in rows('categories').filter(x=>x.active&&x.kind!=='savings')" :key="c.id" :value="c.id">{{c.name}}</option></select></label><label v-if="wish&&kind==='wish'">Wish status<select v-model="status"><option value="active">Active</option><option value="purchased">Purchased</option><option value="archived">Archived</option></select></label></fieldset><p class="text-small">{{kind==='wish'?'Saving a wish does not record spending.':'Every other active profile must approve. Approval does not reserve or spend money.'}}</p><button class="button primary" :disabled="saving">{{saving?'Saving…':retryId?'Retry saved submission':kind==='wish'?'Save wish':request?'Save revised request':'Submit request'}}</button></form></AppDialog></template>
