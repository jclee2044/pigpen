<script setup lang="ts">
import AppDialog from './AppDialog.vue'
import type { Comment } from '../api/models'
import AppLoading from './AppLoading.vue'
import PurchaseEmptyState from './PurchaseEmptyState.vue'
import { computed,ref } from 'vue'
import { rows,state,mutate,activeUser } from '../state/household'
import { useSubmission } from '../lib/submission'
const props=defineProps<{resource:'wishlist-items'|'approval-requests';id:string;compact?:boolean}>()
const text=ref(''),{saving,error,retryId,run}=useSubmission()
const comments=computed(()=>rows('comments').filter(x=>x.target_resource===props.resource&&x.target_id===props.id).sort((a,b)=>a.created_at.localeCompare(b.created_at)))
const resend=useSubmission(),selected=ref<Comment>()
let doubleTapped=''
let touchStart:{x:number;y:number;time:number}|undefined
let lastTap:{id:string;x:number;y:number;time:number}|undefined
function confirmResend(comment:Comment){
 if(comment.actor_id===activeUser.value?.id&&!saving.value&&!retryId.value&&!resend.saving.value&&!selected.value)selected.value=comment
}
function touchDown(event:PointerEvent){
 doubleTapped=''
 if(event.pointerType==='touch')touchStart={x:event.clientX,y:event.clientY,time:Date.now()}
}
function touchUp(event:PointerEvent,comment:Comment){
 if(event.pointerType!=='touch')return
 const start=touchStart;touchStart=undefined
 const time=Date.now()
 if(!start||time-start.time>500||Math.hypot(event.clientX-start.x,event.clientY-start.y)>12){lastTap=undefined;return}
 if(lastTap&&lastTap.id===comment.id&&time-lastTap.time<350&&Math.hypot(event.clientX-lastTap.x,event.clientY-lastTap.y)<24){lastTap=undefined;doubleTapped=comment.id}
 else lastTap={id:comment.id,x:event.clientX,y:event.clientY,time}
}
function touchClick(comment:Comment){
 if(doubleTapped===comment.id){doubleTapped='';confirmResend(comment)}
}
function closeResend(){if(!resend.saving.value&&!resend.retryId.value)selected.value=undefined}
async function resendNotification(){
 if(!selected.value)return
 await resend.run(()=>mutate('comment.resend',{},selected.value!.id),()=>{selected.value=undefined})
}
async function send(){await run(()=>mutate('comment.create',{target_resource:props.resource,target_id:props.id,text:text.value}),()=>{text.value=''})}
</script>
<template><section class="section-space"><h3>Comments</h3><div v-for="comment in comments" :key="comment.id" class="comment" :tabindex="comment.actor_id===activeUser?.id?0:undefined" @dblclick="confirmResend(comment)" @click="touchClick(comment)" @pointerdown="touchDown" @pointerup="touchUp($event,comment)" @pointercancel="touchStart=undefined;lastTap=undefined" @keydown.enter.prevent="confirmResend(comment)" @keydown.space.prevent="confirmResend(comment)"><div class="comment-heading"><strong>{{rows('users').find(x=>x.id===comment.actor_id)?.name}}</strong><time :datetime="comment.created_at"><span>{{new Date(comment.created_at).toLocaleDateString(undefined,{year:'numeric',month:'numeric',day:'numeric'})}},</span> <span>{{new Date(comment.created_at).toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'})}}</span></time></div><p>{{comment.text}}</p></div><p v-if="!comments.length&&compact" class="text-small">No comments yet.</p><PurchaseEmptyState v-else-if="!comments.length" /><form @submit.prevent="send"><AppLoading v-if="saving" compact /><div v-if="error" role="alert" class="notice error">{{error}}</div><label>Say something...<textarea v-model="text" :disabled="!state.online||saving||!!retryId" required maxlength="4000" /></label><button class="button" :disabled="!state.online||saving">{{retryId?'Retry saved submission':'Add comment'}}</button><small v-if="!state.online">Reconnect to add a comment.</small></form><AppDialog v-if="selected" title="Resend notification?" centered small @close="closeResend"><div v-if="resend.error.value" role="alert" class="notice error">{{resend.error.value}}</div><div class="actions"><button class="button" :disabled="resend.saving.value||!!resend.retryId.value" @click="closeResend">No</button><button class="button primary" :disabled="!state.online||resend.saving.value" @click="resendNotification">{{resend.saving.value?'Sending…':resend.retryId.value?'Retry saved submission':'Yes'}}</button></div></AppDialog></section></template>

<style scoped>
.comment[tabindex]{touch-action:manipulation}
.comment-heading{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 8px;-webkit-text-size-adjust:100%;text-size-adjust:100%}
.comment-heading strong{font-size:14px}
.comment-heading time{display:inline-flex;gap:3px;color:var(--muted);font-size:12px;font-weight:400;line-height:1.5;white-space:nowrap}
.comment-heading time span{font:inherit}
.comment-heading time :deep(a){font:inherit;color:inherit;text-decoration:none}
</style>
