<script setup lang="ts">
import AppIcon from '../components/AppIcon.vue'
import AppLoading from '../components/AppLoading.vue'
import PurchaseEmptyState from '../components/PurchaseEmptyState.vue'
import { computed,ref,watch } from 'vue'
import { useRoute } from 'vue-router'
import { rows,state,activeUser,mutate } from '../state/household'
import type { Request } from '../api/models'
import { approved } from '../lib/selectors'
import { money } from '../lib/money'
import { useSubmission } from '../lib/submission'
import PlanForm from '../components/PlanForm.vue'
import PurchaseForm from '../components/PurchaseForm.vue'
import AppDialog from '../components/AppDialog.vue'
import CommentThread from '../components/CommentThread.vue'
import PigAvatar from '../components/PigAvatar.vue'
const filter=ref('open'),adding=ref(false),editing=ref<Request>(),purchasing=ref<Request>(),selected=ref(String(useRoute().query.detail??''))
const route=useRoute()
watch(()=>route.query.detail,id=>selected.value=String(id??''))
const requests=computed(()=>rows('approval-requests').filter(x=>filter.value==='all'||(filter.value==='mine'?x.requester_id===activeUser.value?.id:filter.value==='approved'?x.status==='open'&&approved(x,state.records):x.status==='open')))
const detail=computed(()=>rows('approval-requests').find(x=>x.id===selected.value))
const user=(id:string)=>rows('users').find(x=>x.id===id),reviewers=(r:Request)=>rows('users').filter(x=>x.active&&x.id!==r.requester_id)
const votes=(r:Request)=>rows('approval-votes').filter(v=>v.request_id===r.id&&v.request_revision===r.revision&&v.approved)
const myVote=computed(()=>rows('approval-votes').find(v=>v.request_id===detail.value?.id&&v.reviewer_id===activeUser.value?.id))
const {saving,error,retryId,run}=useSubmission()
function open(id:string){selected.value=id;error.value='';retryId.value=''}
async function vote(){if(!detail.value)return;await run(()=>mutate('vote.set',{request_id:detail.value!.id,request_revision:detail.value!.revision,expected_revision:myVote.value?.revision??0,approved:!(myVote.value?.approved&&myVote.value.request_revision===detail.value!.revision)},myVote.value?.id),()=>{})}
async function cancel(){if(!detail.value||!confirm('Cancel this request? Its history will remain.'))return;await run(()=>mutate('request.cancel',{expected_revision:detail.value!.revision},detail.value!.id),()=>{})}
</script>
<template><div class="page-heading"><div><h1>Approvals</h1></div><button class="button primary icon-only" aria-label="Request approval" title="Request approval" @click="adding=true"><AppIcon name="plus" /></button></div><div class="toolbar"><label>Show requests<select v-model="filter"><option value="open">Open requests</option><option value="mine">My requests</option><option value="approved">Approved to purchase</option><option value="all">All requests</option></select></label></div><p class="text-small">All other active profiles must approve. Approval does not record a purchase.</p><section v-if="!requests.length" class="card empty"><PurchaseEmptyState /></section><div class="cards-grid"><article v-for="r in requests" :key="r.id" class="card plan-card"><div class="plan-card-top"><PigAvatar :avatar="user(r.requester_id)?.avatar" :size="38" /><small>{{user(r.requester_id)?.name}} asked</small><span class="pill" :class="{pending:r.status==='open'&&!approved(r,state.records)}">{{r.status==='open'?(approved(r,state.records)?'Approved':'Awaiting approval'):r.status}}</span></div><h2><button class="title-button" @click="open(r.id)">{{r.item}}</button></h2><strong class="plan-price">{{money(r.amount_minor)}}</strong><p class="plan-description">{{r.description}}</p><p v-if="r.status==='open'" class="text-small">{{votes(r).filter(v=>reviewers(r).some(u=>u.id===v.reviewer_id)).length}} of {{reviewers(r).length}} reviewers approve</p><button class="button" @click="open(r.id)">Review request</button></article></div><PlanForm v-if="adding||editing" kind="request" :request="editing" @close="adding=false;editing=undefined" /><PurchaseForm v-if="purchasing" :request="purchasing" @close="purchasing=undefined" /><AppDialog v-if="detail" :title="detail.item" @close="selected='' "><AppLoading v-if="saving" compact label="Saving…" /><strong class="plan-price">{{money(detail.amount_minor)}}</strong><p>{{user(detail.requester_id)?.name}}’s request</p><p style="white-space:pre-wrap">{{detail.description}}</p><a v-if="detail.url" :href="detail.url" target="_blank" rel="noopener noreferrer">Visit item link ↗</a><div v-if="error" role="alert" class="notice error">{{error}}</div><div v-if="detail.status==='open'"><div class="reviewers section-space"><div v-for="u in reviewers(detail)" :key="u.id" class="row"><PigAvatar :avatar="u.avatar" :size="34" /><strong class="row-main">{{u.name}}</strong><span class="pill" :class="{pending:!votes(detail).some(v=>v.reviewer_id===u.id)}">{{votes(detail).some(v=>v.reviewer_id===u.id)?'Approved':'Awaiting review'}}</span></div></div><div class="actions section-space"><button v-if="detail.requester_id!==activeUser?.id" class="button primary" :disabled="saving" @click="vote">{{retryId?'Retry saved action':myVote?.approved&&myVote.request_revision===detail.revision?'Remove my approval':'Approve request'}}</button><template v-else><button class="button" :disabled="!state.online||saving||!!retryId" @click="editing=detail;selected=''">Edit request</button><button class="button danger" :disabled="!state.online||saving" @click="cancel">{{retryId?'Retry saved action':'Cancel request'}}</button></template><button v-if="approved(detail,state.records)" class="button primary" @click="purchasing=detail;selected=''">Record approved purchase</button></div></div><p v-else class="notice section-space">{{detail.status==='purchased'?'Purchased — final approval history is preserved.':'This request was canceled.'}}</p><CommentThread resource="approval-requests" :id="detail.id" /></AppDialog></template>
