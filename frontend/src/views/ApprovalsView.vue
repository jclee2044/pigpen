<script setup lang="ts">
import { computed,ref,watch } from 'vue'
import { useRoute } from 'vue-router'
import SwipeWish from '../components/SwipeWish.vue'
import AppIcon from '../components/AppIcon.vue'
import AppLoading from '../components/AppLoading.vue'
import PurchaseEmptyState from '../components/PurchaseEmptyState.vue'
import PlanForm from '../components/PlanForm.vue'
import PurchaseForm from '../components/PurchaseForm.vue'
import AppDialog from '../components/AppDialog.vue'
import CommentThread from '../components/CommentThread.vue'
import PigAvatar from '../components/PigAvatar.vue'
import { rows,state,activeUser,mutate } from '../state/household'
import type { Request } from '../api/models'
import { approved,newest } from '../lib/selectors'
import { money } from '../lib/money'
import { readMeta,writeMeta } from '../lib/storage'
import { useSubmission } from '../lib/submission'
const route=useRoute()
const revealed=ref(''),confirming=ref<{request:Request;action:'delete'|'deny'}>(),reason=ref('')
const selected=ref(String(route.query.detail??''))
const detail=computed(()=>rows('approval-requests').find(r=>r.id===selected.value))
const commentCount=(id:string)=>rows('comments').filter(c=>c.target_resource==='approval-requests'&&c.target_id===id).length
function openRequest(request:Request){if(!saving.value&&!retryId.value){revealed.value='';selected.value=request.id}}
function openCard(event:MouseEvent,request:Request){if(!(event.target as HTMLElement).closest('button,a,input,textarea,select'))openRequest(request)}
function editRequest(request:Request){selected.value='';editing.value=request}
const filter=ref('open'),adding=ref(false),editing=ref<Request>(),purchasing=ref<Request>()
const requests=computed(()=>newest(rows('approval-requests').filter(x=>filter.value==='all'||(filter.value==='mine'?x.requester_id===activeUser.value?.id:filter.value==='approved'?x.status==='open'&&approved(x,state.records):filter.value==='denied'?x.status==='denied':x.status==='open'))))
const user=(id:string)=>rows('users').find(x=>x.id===id)
const voteFor=(request:Request,id=activeUser.value?.id)=>rows('approval-votes').find(v=>v.request_id===request.id&&v.reviewer_id===id)
const hasApproved=(request:Request,id=activeUser.value?.id)=>{const v=voteFor(request,id);return !!v?.approved&&v.request_revision===request.revision}
const {saving,error,retryId,run}=useSubmission()
async function accept(request:Request){
 const existing=voteFor(request)
 await run(()=>mutate('vote.set',{request_id:request.id,request_revision:request.revision,expected_revision:existing?.revision??0,approved:true},existing?.id),()=>{})
}
function confirmAction(request:Request,action:'delete'|'deny'){
 if(saving.value||retryId.value)return
 selected.value='';revealed.value='';reason.value='';error.value='';confirming.value={request,action}
}
async function retryAction(){await run(()=>Promise.resolve(),()=>{})}
async function submitAction(){
 const pending=confirming.value
 if(!pending)return
 const {request,action}=pending
 await run(()=>action==='delete'?mutate('request.delete',{expected_revision:request.revision},request.id):mutate('request.deny',{expected_revision:request.revision,reason:reason.value.trim()},request.id),()=>{confirming.value=undefined})
}
const denialNotices=ref<Request[]>([])
const deniedForMe=computed(()=>rows('approval-requests').filter(r=>r.requester_id===activeUser.value?.id&&r.status==='denied'))
let noticeScope=''
watch(()=>JSON.stringify([activeUser.value?.household_id,activeUser.value?.id,deniedForMe.value.map(r=>r.id)]),async(_value,_old,onCleanup)=>{
 let canceled=false
 onCleanup(()=>{canceled=true})
 const profile=activeUser.value
 const scope=profile?`seen-request-denials:${profile.household_id}:${profile.id}`:''
 if(noticeScope!==scope){denialNotices.value=[];noticeScope=scope}
 if(!scope)return
 const seen=await readMeta<string[]>(scope).catch(()=>undefined)??[]
 if(canceled)return
 const denied=deniedForMe.value
 denialNotices.value=denialNotices.value.filter(r=>denied.some(current=>current.id===r.id))
 for(const request of denied){
  if(!seen.includes(request.id)&&!denialNotices.value.some(r=>r.id===request.id))denialNotices.value.push(request)
 }
 // First-view acknowledgments are local to this household/profile/device.
 // Keep the visible frames until dismissed or the page is left.
 await writeMeta(scope,[...new Set([...seen,...denied.map(r=>r.id)])]).catch(()=>{})
},{immediate:true})
watch(()=>activeUser.value?.id,()=>{revealed.value='';if(!saving.value&&!retryId.value){selected.value='';confirming.value=undefined;editing.value=undefined}})
watch(()=>route.query.detail,id=>{selected.value=String(id??'');if(id)filter.value='all'},{immediate:true})
</script>
<template>
 <div class="page-heading"><div><h1>Approvals</h1></div><button class="button primary icon-only" aria-label="Request approval" title="Request approval" :disabled="saving||!!retryId" @click="adding=true"><AppIcon name="plus" /></button></div>
 <div class="toolbar"><label>Show requests<select v-model="filter"><option value="open">Open requests</option><option value="all">All requests</option><option value="mine">My requests</option><option value="approved">Approved requests</option><option value="denied">Denied requests</option></select></label></div>
 <section v-for="notice in denialNotices" :key="notice.id" class="card denial-notice" role="status">
  <div><h2>Your request for “{{notice.item}}” was denied.</h2><button class="button" @click="openRequest(notice)">View request</button></div>
  <button class="icon-button" :aria-label="'Dismiss denial notice for '+notice.item" @click="denialNotices=denialNotices.filter(r=>r.id!==notice.id)"><AppIcon name="close" /></button>
 </section>
 <p class="text-small">All other active profiles must approve. Approval does not record a purchase.</p>
 <section v-if="!requests.length" class="card empty"><PurchaseEmptyState /></section>
 <div v-if="error&&!confirming&&!detail" role="alert" class="notice error">{{error}}<button v-if="retryId" class="button" :disabled="saving" @click="retryAction">Retry saved action</button></div>
 <div class="cards-grid">
  <SwipeWish v-for="r in requests" :key="r.id" :id="r.id" :name="r.item" :enabled="r.requester_id===activeUser?.id&&r.status!=='purchased'&&!saving&&!retryId" :open="revealed===r.id" @reveal="id=>revealed=id" @delete="confirmAction(r,'delete')">
   <article :id="'request-'+r.id" class="card plan-card request-card" tabindex="-1" :aria-label="r.item" @click="openCard($event,r)">
    <div class="plan-card-top"><PigAvatar :avatar="user(r.requester_id)?.avatar" :size="38" /><small>{{user(r.requester_id)?.name}} asked</small><button v-if="r.requester_id===activeUser?.id&&r.status==='open'" class="request-comments request-edit-icon" aria-label="Edit request" title="Edit request" :disabled="!state.online||saving||!!retryId" @click.stop="editRequest(r)"><AppIcon name="edit" /></button><button class="request-comments" :aria-label="`${commentCount(r.id)} ${commentCount(r.id)===1?'comment':'comments'} on ${r.item}`" aria-haspopup="dialog" @click.stop="openRequest(r)"><AppIcon name="comments" /><span>{{commentCount(r.id)}}</span></button></div>
    <p class="request-status"><span class="pill" :class="{pending:r.status==='open'&&!approved(r,state.records)}">{{r.status==='open'?(approved(r,state.records)?'Approved':'Awaiting approval'):r.status}}</span></p>
    <div class="wish-card-summary"><h2><button class="title-button" aria-haspopup="dialog" @click="openRequest(r)">{{r.item}}</button></h2><strong class="plan-price">{{money(r.amount_minor)}}</strong></div>
    <p v-if="r.description" class="plan-description">{{r.description}}</p>
    <p v-if="r.url" class="request-link"><a :href="r.url" target="_blank" rel="noopener noreferrer">{{r.url}} ↗</a></p>
    <p v-if="r.category_id" class="text-small">Category: {{rows('categories').find(c=>c.id===r.category_id)?.name}}</p>
    <p v-if="r.status!=='open'" class="text-small">{{r.status==='purchased'?'Purchased — final approval history is preserved.':r.status==='denied'?'This request was denied. Open the request to see the reason.':'This request was canceled.'}}</p>
    <div v-if="r.status==='open'&&activeUser&&r.requester_id!==activeUser.id" class="request-actions">
     <button class="button danger" :disabled="!state.online||saving||!!retryId" @click="confirmAction(r,'deny')">Deny</button><button class="button primary" :disabled="saving||!!retryId||hasApproved(r)" @click="accept(r)">{{hasApproved(r)?'Approved':'Approve'}}</button>
    </div>
    <button v-if="r.status==='open'&&approved(r,state.records)" class="button primary section-space" :disabled="saving||!!retryId" @click="purchasing=r">Record approved purchase</button>
   </article>
  </SwipeWish>
 </div>
 <AppDialog v-if="detail" centered :title="detail.item" @close="selected=''">
  <strong class="plan-price">{{money(detail.amount_minor)}}</strong>
  <p class="request-summary">{{user(detail.requester_id)?.name}}’s request {{detail.status==='open'?(approved(detail,state.records)?'approved':'awaiting approval'):detail.status}}</p>
  <p class="request-description">{{detail.description}}</p>
  <p v-if="detail.url" class="request-link"><a :href="detail.url" target="_blank" rel="noopener noreferrer">{{detail.url}} ↗</a></p>
  <p v-if="detail.category_id" class="text-small">Category: {{rows('categories').find(c=>c.id===detail?.category_id)?.name}}</p>
  <div v-if="error" role="alert" class="notice error">{{error}}<button v-if="retryId" class="button" :disabled="saving" @click="retryAction">Retry saved action</button></div>
  <div class="actions section-space">
   <template v-if="detail.requester_id===activeUser?.id"><button v-if="detail.status==='open'" class="button" :disabled="!state.online||saving||!!retryId" @click="editRequest(detail)">Edit request</button><button v-if="detail.status!=='purchased'" class="button danger" :disabled="!state.online||saving||!!retryId" @click="confirmAction(detail,'delete')">Delete request</button></template>
   <template v-else-if="activeUser&&detail.status==='open'"><button class="button danger" :disabled="!state.online||saving||!!retryId" @click="confirmAction(detail,'deny')">Deny</button><button class="button primary" :disabled="saving||!!retryId||hasApproved(detail)" @click="accept(detail)">{{hasApproved(detail)?'Approved':'Approve'}}</button></template>
   <button v-if="detail.status==='open'&&approved(detail,state.records)" class="button primary" :disabled="saving||!!retryId" @click="purchasing=detail;selected=''">Record approved purchase</button>
  </div>
  <CommentThread resource="approval-requests" :id="detail.id" compact />
 </AppDialog>
 <AppDialog v-if="confirming" centered :title="confirming.action==='delete'?'Delete request?':'Deny request?'" @close="!saving&&!retryId&&(confirming=undefined)">
  <form @submit.prevent="submitAction"><AppLoading v-if="saving" compact /><p v-if="confirming.action==='delete'">Delete “{{confirming.request.item}}”?</p><p v-if="confirming.action==='delete'" class="text-small">This removes the request from the approvals list.</p><label v-else>Reason for denial<textarea v-model="reason" required maxlength="4000" :disabled="saving||!!retryId" /></label><div v-if="error" role="alert" class="notice error">{{error}}</div><p v-if="!state.online" class="notice">Reconnect to {{confirming.action}} this request.</p><div class="actions section-space"><button type="button" class="button" :disabled="saving||!!retryId" @click="confirming=undefined">Cancel</button><button class="button danger" :disabled="!state.online||saving||(confirming.action==='deny'&&!reason.trim())">{{retryId?'Retry saved action':confirming.action==='delete'?'Delete request':'Deny request'}}</button></div></form>
 </AppDialog>
 <PlanForm v-if="adding||editing" kind="request" :request="editing" @close="adding=false;editing=undefined" />
 <PurchaseForm v-if="purchasing" :request="purchasing" @close="purchasing=undefined" />
</template>
<style scoped>
.denial-notice{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:20px;border-color:var(--rose)}
.denial-notice h2{font-size:17px;overflow-wrap:anywhere}
.denial-notice .icon-button{flex-shrink:0}
.request-card{cursor:pointer}
.request-card .plan-card-top{margin-bottom:8px}
.request-card .plan-card-top small{flex:1;min-width:0;overflow-wrap:anywhere}
.request-comments{display:flex;align-items:center;justify-content:center;gap:5px;flex-shrink:0;min-width:44px;min-height:44px;padding:4px;border:0;background:transparent;color:var(--muted);font:inherit;cursor:pointer}
.request-comments svg{width:20px;height:20px}
.request-comments:hover{color:var(--rose)}
.request-status{margin:0 0 16px}
.request-description{white-space:pre-wrap;overflow-wrap:anywhere}
.request-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:16px}
.request-link{overflow-wrap:anywhere;font-size:13px}
.request-card .plan-description{flex:0}
</style>
