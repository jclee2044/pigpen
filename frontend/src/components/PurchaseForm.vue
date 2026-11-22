<script setup lang="ts">
import ReceiptPhotoPreview from './ReceiptPhotoPreview.vue'
import AppLoading from './AppLoading.vue'
import { computed,ref,watch } from 'vue'
import { monthCategories,monthRevision,OTHER_CATEGORY_ID } from '../lib/categoryMonths'
import { ApiError } from '../api/client'
import type { ReceiptScan } from '../api/receipts'
import { rows,mutate,state } from '../state/household'
import type { Purchase,Request,Wish } from '../api/models'
import { parseMoney,inputMoney,today } from '../lib/money'
import { useSubmission } from '../lib/submission'
import AppDialog from './AppDialog.vue'
const props=defineProps<{purchase?:Purchase; request?:Request; wish?:Wish; receipt?:ReceiptScan}>()
const emit=defineEmits<{close:[];saved:[];retake:[]}>()
const item=ref(props.purchase?.item??props.request?.item??props.wish?.name??props.receipt?.suggestions?.item??'')
const amount=ref(props.purchase?inputMoney(props.purchase.amount_minor):props.request?inputMoney(props.request.amount_minor):props.wish?inputMoney(props.wish.price_minor):props.receipt?.suggestions?.amount_minor?inputMoney(props.receipt.suggestions.amount_minor):'')
const initialCategory=props.purchase?.category_id??props.request?.category_id??''
const initialCategoryRow=rows('categories').find(c=>c.id===initialCategory)
const category=ref(props.purchase?initialCategory:(initialCategoryRow?.parent_id??initialCategory))
const explanation=ref(props.purchase?.category_explanation??'')
const date=ref(props.purchase?.transaction_date??props.receipt?.suggestions?.transaction_date??today()),merchant=ref(props.purchase?.merchant??props.receipt?.suggestions?.merchant??''),description=ref(props.purchase?.description??props.request?.description??props.wish?.description??props.receipt?.suggestions?.description??'')
const categories=computed(()=>{
 const available=monthCategories(state.records,date.value.slice(0,7)).filter(x=>x.kind!=='savings'&&!x.parent_id&&x.id!==OTHER_CATEGORY_ID)
 if(props.purchase&&date.value.slice(0,7)===props.purchase.transaction_date.slice(0,7)&&initialCategoryRow&&initialCategoryRow.id!==OTHER_CATEGORY_ID&&!available.some(c=>c.id===initialCategoryRow.id))available.push(initialCategoryRow)
 return available
})
const unavailable=computed(()=>!!category.value&&category.value!==OTHER_CATEGORY_ID&&!categories.value.some(c=>c.id===category.value))
const addingCategory=ref(false),categoryError=ref('')
async function addSelectedCategory(){
 addingCategory.value=true;categoryError.value=''
 try{await mutate('category.include',{month:date.value.slice(0,7),included:true,expected_revision:monthRevision(state.records,date.value.slice(0,7))},category.value)}
 catch(e){categoryError.value=e instanceof Error?e.message:'Could not add category'}
 finally{addingCategory.value=false}
}
const receiptWarnings=computed(()=>props.receipt?.suggestions?.warnings.filter(w=>!w.startsWith('Review the receipt,')&&!w.startsWith('Line items may be incomplete or misread.'))??[])
const duplicates=ref<string[]>([])
const receiptReviewed=ref(false)
const confirmClose=ref(false)
function requestClose(){
 if(props.receipt){if(!saving.value&&!retryId.value)confirmClose.value=true}
 else emit('close')
}
const keep=ref(props.receipt?.keep_indefinitely??false),allowDuplicate=ref(false)
watch(()=>state.selectedId,()=>{if(props.receipt)emit('close')})
const {saving,error,retryId,run}=useSubmission()
function categoryLabel(id:string){const c=rows('categories').find(x=>x.id===id);return c?.kind==='personal'?`${c.name} · ${rows('users').find(u=>u.id===c.owner_id)?.name}`:c?.parent_id?`${rows('categories').find(p=>p.id===c.parent_id)?.name} / ${c.name}`:c?.name}
async function save(){await run(async()=>{if(props.receipt&&!receiptReviewed.value&&!retryId.value)throw new Error('Check the receipt details before saving.');if(unavailable.value)throw new Error('Choose an available category or add this category.');if(category.value===OTHER_CATEGORY_ID&&!explanation.value.trim())throw new Error('Please explain is required for Other.');const data={category_explanation:category.value===OTHER_CATEGORY_ID?explanation.value.trim():'',item:item.value,amount_minor:parseMoney(amount.value,false),category_id:category.value,transaction_date:date.value,merchant:merchant.value||null,description:description.value,request_id:props.purchase?.request_id??props.request?.id??null,request_revision:props.request?.revision??null};if(props.receipt){if(state.selectedId!==props.receipt.actor_id)throw new Error('Switch to the profile that scanned this receipt.');try{return await mutate('receipt.confirm',{scan_id:props.receipt.id,expected_revision:props.receipt.revision,keep_indefinitely:keep.value,allow_duplicate:allowDuplicate.value,purchase:data})}catch(e){if(e instanceof ApiError&&e.code==='receipt_duplicate')duplicates.value=(e.details as {purchase_ids:string[]}).purchase_ids;throw e}}return props.purchase?mutate('purchase.update',{...data,expected_revision:props.purchase.revision},props.purchase.id):mutate('purchase.create',data)},()=>{emit('saved');emit('close')})}
</script>
<template><AppDialog :title="purchase?'Edit purchase':'Add purchase'" @close="requestClose"><AppLoading v-if="saving" compact /><form @submit.prevent="save"><template v-if="receipt"><ReceiptPhotoPreview :src="'/api/v1/receipt-scans/'+receipt.id+'/content'" /><button type="button" class="button" :disabled="saving||!!retryId||!state.online" @click="run(()=>mutate('receipt.cancel',{expected_revision:receipt!.revision},receipt!.id),()=>emit('retake'))">Retake photo</button><p v-for="warning in receiptWarnings" :key="warning" class="notice">{{warning}}</p></template><div v-if="error" class="notice error" role="alert">{{error}}</div><div v-if="request" class="notice">Recording this purchase will link it to the approved request.</div><fieldset :disabled="saving||!!retryId"><label><span>Item or service <span class="required-marker" aria-hidden="true">*</span></span><input aria-label="Item or service" v-model="item" required maxlength="200" /></label><label><span>Amount ($) <span class="required-marker" aria-hidden="true">*</span></span><input aria-label="Amount ($)" v-model="amount" inputmode="decimal" placeholder="0.00" required /></label><label class="transaction-date"><span>Transaction date <span class="required-marker" aria-hidden="true">*</span></span><input aria-label="Transaction date" v-model="date" type="date" required /></label><label><span>Category <span class="required-marker" aria-hidden="true">*</span></span><select aria-label="Category" v-model="category" required><option disabled value="">Choose a category</option><option v-for="c in categories" :key="c.id" :value="c.id">{{categoryLabel(c.id)}}</option><option v-if="unavailable" :value="category" disabled>{{categoryLabel(category)}} · Unavailable</option><option :value="OTHER_CATEGORY_ID">Other</option></select></label><div v-if="unavailable" class="notice"><p>This category is not available for {{date.slice(0,7)}}. Choose another category or add it.</p><button type="button" class="button small" :disabled="!state.online||addingCategory" @click="addSelectedCategory">Add {{categoryLabel(category)}}</button><p v-if="categoryError" role="alert">{{categoryError}}</p></div><label v-if="category===OTHER_CATEGORY_ID"><span>Please explain <span class="required-marker" aria-hidden="true">*</span></span><textarea aria-label="Please explain" v-model="explanation" required maxlength="4000" /></label><label>Merchant<input v-model="merchant" maxlength="200" /></label><label>Description<textarea v-model="description" maxlength="4000" /></label></fieldset><template v-if="receipt"><div class="receipt-retention"><label class="check-label"><input v-model="keep" type="checkbox" :disabled="saving||!!retryId" /> Keep photo indefinitely</label><p v-if="!keep">Photo expires {{new Date(receipt.expires_at).toLocaleDateString()}}. Purchase details will remain.</p></div><p v-for="id in duplicates" :key="id"><a :href="'/purchases?detail='+id" target="_blank" rel="noopener">Review matching purchase</a></p><label v-if="duplicates.length" class="check-label"><input v-model="allowDuplicate" type="checkbox" /> I reviewed the matching purchase and want to save another</label><label class="check-label"><input v-model="receiptReviewed" type="checkbox" :disabled="saving||!!retryId" /> I verified everything above is accurate</label><p v-if="!state.online" class="notice">Reconnect to save this scanned purchase.</p></template><div class="purchase-actions"><button type="button" class="button" :disabled="saving||!!retryId||(!!receipt&&!state.online)" @click="receipt?run(()=>mutate('receipt.cancel',{expected_revision:receipt!.revision},receipt!.id),()=>emit('close')):requestClose()">Cancel</button><button class="button primary" :disabled="saving||(!!receipt&&(!state.online||(!receiptReviewed&&!retryId)))">{{saving?'Saving…':retryId?'Retry saved submission':purchase?'Save changes':'Save'}}</button></div></form></AppDialog><AppDialog v-if="confirmClose" title="Continue without saving?" centered small @close="confirmClose=false"><div class="purchase-actions"><button type="button" class="button" @click="confirmClose=false">Keep editing</button><button type="button" class="button primary" @click="emit('close')">Leave</button></div></AppDialog></template>

<style scoped>
.purchase-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:16px}
.purchase-actions .button{width:100%;min-width:0;margin:0;padding:10px 8px;font-size:13px}
.transaction-date{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;gap:10px}
.transaction-date>span{white-space:nowrap;font-size:12px}
.transaction-date input{min-width:0;width:100%;font-size:14px;padding:8px}

.receipt-retention p{font-size:12px;font-weight:400;line-height:1.4;margin:4px 0 0 30px}
.check-label input { flex:0 0 20px; }
.receipt-preview { display:block; max-width:100%; max-height:220px; margin:0 auto 16px; object-fit:contain; }
.required-marker { color: var(--rose-dark); font-weight: 700; }
</style>
