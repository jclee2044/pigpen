<script setup lang="ts">
import { computed,ref } from 'vue'
import { state,rows,activeUser,mutate } from '../state/household'
import type { Purchase,Request,Wish } from '../api/models'
import { parseMoney,inputMoney,today } from '../lib/money'
import { useSubmission } from '../lib/submission'
import AppDialog from './AppDialog.vue'
const props=defineProps<{purchase?:Purchase; request?:Request; wish?:Wish}>()
const emit=defineEmits<{close:[];saved:[]}>()
const item=ref(props.purchase?.item??props.request?.item??props.wish?.name??'')
const amount=ref(props.purchase?inputMoney(props.purchase.amount_minor):props.request?inputMoney(props.request.amount_minor):props.wish?inputMoney(props.wish.price_minor):'')
const category=ref(props.purchase?.category_id??props.request?.category_id??'')
const date=ref(props.purchase?.transaction_date??today()),merchant=ref(props.purchase?.merchant??''),description=ref(props.purchase?.description??props.request?.description??props.wish?.description??'')
const categories=computed(()=>rows('categories').filter(x=>x.active&&x.kind!=='savings'&&(!x.parent_id||rows('categories').some(p=>p.id===x.parent_id&&p.active))))
const {saving,error,retryId,run}=useSubmission()
function categoryLabel(id:string){const c=rows('categories').find(x=>x.id===id);return c?.kind==='personal'?`${c.name} · ${rows('users').find(u=>u.id===c.owner_id)?.name}`:c?.name}
async function save(){await run(()=>{const data={item:item.value,amount_minor:parseMoney(amount.value,false),category_id:category.value,transaction_date:date.value,merchant:merchant.value||null,description:description.value,request_id:props.purchase?.request_id??props.request?.id??null,request_revision:props.request?.revision??null};return props.purchase?mutate('purchase.update',{...data,expected_revision:props.purchase.revision},props.purchase.id):mutate('purchase.create',data)},()=>{emit('saved');emit('close')})}
</script>
<template><AppDialog :title="purchase?'Edit purchase':'Add purchase'" @close="emit('close')"><form @submit.prevent="save"><div v-if="error" class="notice error" role="alert">{{error}}</div><div v-if="request" class="notice">Recording this purchase will link it to the approved request.</div><fieldset :disabled="saving||!!retryId"><label>Item or service<input v-model="item" required maxlength="200" /></label><div class="form-grid"><label>Amount ($)<input v-model="amount" inputmode="decimal" placeholder="0.00" required /></label><label>Transaction date<input v-model="date" type="date" required /></label></div><label>Category<select v-model="category" required><option disabled value="">Choose a category</option><option v-for="c in categories" :key="c.id" :value="c.id">{{categoryLabel(c.id)}}</option></select></label><label>Merchant <span class="form-help">Optional</span><input v-model="merchant" maxlength="200" /></label><label>Description <span class="form-help">Optional receipt details</span><textarea v-model="description" maxlength="4000" /></label></fieldset><p class="text-small muted">Recorded by {{activeUser?.name}}. {{state.online?'Your household will see this after it is saved.':'This purchase will wait on your device until you reconnect.'}}</p><button class="button primary" :disabled="saving">{{saving?'Saving…':retryId?'Retry saved submission':purchase?'Save changes':'Save purchase'}}</button></form></AppDialog></template>
