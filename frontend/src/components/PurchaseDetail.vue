<script setup lang="ts">
import AppLoading from './AppLoading.vue'
import PurchaseEmptyState from './PurchaseEmptyState.vue'
import { computed,ref } from 'vue'
import type { Purchase } from '../api/models'
import { rows,state,activeUser,mutate,refresh } from '../state/household'
import { request } from '../api/client'
import { money } from '../lib/money'
import AppDialog from './AppDialog.vue'
import { useSubmission } from '../lib/submission'
const props=defineProps<{purchase:Purchase}>();const emit=defineEmits<{close:[];edit:[]}>()
const attachments=computed(()=>rows('attachments').filter(x=>x.purchase_id===props.purchase.id)),file=ref<File>(),uploading=ref(false),uploadError=ref('');let uploadForm:FormData|undefined
const {saving,error,retryId,run}=useSubmission()
async function remove(){if(!confirm('Delete this purchase? It will be removed from spending totals.'))return;await run(()=>mutate('purchase.delete',{expected_revision:props.purchase.revision},props.purchase.id),()=>emit('close'))}
function choose(event:Event){file.value=(event.target as HTMLInputElement).files?.[0];uploadForm=undefined;uploadError.value=''}
async function upload(){if(!file.value||!activeUser.value)return;uploadError.value='';if(file.value.size>10*1024*1024){uploadError.value='Choose an image up to 10 MiB.';return}uploading.value=true;try{if(!uploadForm){uploadForm=new FormData();uploadForm.append('file',file.value);uploadForm.append('operation_id',crypto.randomUUID());uploadForm.append('actor_id',activeUser.value.id);uploadForm.append('client_time',new Date().toISOString())}await request('/purchases/'+props.purchase.id+'/attachments',{method:'POST',body:uploadForm});await refresh();file.value=undefined;uploadForm=undefined}catch(e){uploadError.value=e instanceof Error?e.message:'Could not upload image'}finally{uploading.value=false}}
async function deleteImage(id:string,revision:number){if(!confirm('Remove this attachment?'))return;try{const query=new URLSearchParams({operation_id:crypto.randomUUID(),actor_id:activeUser.value!.id,expected_revision:String(revision),client_time:new Date().toISOString()});await request('/attachments/'+id+'?'+query,{method:'DELETE'});await refresh()}catch(e){uploadError.value=e instanceof Error?e.message:'Could not remove attachment'}}
</script>
<template><AppDialog :title="purchase.item" @close="emit('close')"><AppLoading v-if="saving" compact label="Saving…" /><strong class="metric-value">{{money(purchase.amount_minor)}}</strong><p>{{rows('users').find(x=>x.id===purchase.purchaser_id)?.name}} · {{purchase.transaction_date}}<br />{{rows('categories').find(x=>x.id===purchase.category_id)?.name}}</p><p v-if="purchase.merchant">{{purchase.merchant}}</p><p v-if="purchase.description" style="white-space:pre-wrap">{{purchase.description}}</p><p v-if="purchase.request_id" class="notice">Linked to an approved household request. Approval history is preserved.</p><p v-if="purchase.bill_id" class="notice">Recorded payment for a monthly bill.</p><div v-if="error" class="notice error" role="alert">{{error}}</div><div class="actions"><button class="button" :disabled="!state.online||saving||!!retryId" @click="emit('edit')">Edit purchase</button><button class="button danger" :disabled="!state.online||saving" @click="remove">{{retryId?'Retry saved submission':'Delete purchase'}}</button></div><hr /><h3>Receipt & images</h3><div v-if="uploadError" class="notice error" role="alert">{{uploadError}}</div><PurchaseEmptyState v-if="!attachments.length" /><div v-for="image in attachments" :key="image.id" class="purchase-image"><a :href="'/api/v1/attachments/'+image.id+'/content'" target="_blank" rel="noopener" :aria-label="'Open image: '+image.filename"><img :src="'/api/v1/attachments/'+image.id+'/content'" :alt="image.filename" loading="lazy" /></a><div class="row"><div class="row-main"><a :href="'/api/v1/attachments/'+image.id+'/content'" target="_blank" rel="noopener">{{image.filename}}</a><p>{{Math.ceil(image.byte_size/1024)}} KB</p></div><button class="button small" :disabled="!state.online" @click="deleteImage(image.id,image.revision)">Remove image</button></div></div><form class="section-space" @submit.prevent="upload"><AppLoading v-if="uploading" compact label="Uploading image…" /><label>Attach receipt or bank screenshot<input type="file" accept="image/png,image/jpeg,image/webp" :disabled="!state.online||uploading" @change="choose" /></label><button class="button" :disabled="!file||!state.online||uploading">{{uploading?'Uploading…':'Upload image'}}</button></form></AppDialog></template>

<style scoped>
.purchase-image{margin:18px 0}
.purchase-image img{display:block;width:100%;max-height:420px;object-fit:contain;background:var(--paper);border:1px solid var(--line);border-radius:12px}
</style>
