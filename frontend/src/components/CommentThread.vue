<script setup lang="ts">
import AppLoading from './AppLoading.vue'
import PurchaseEmptyState from './PurchaseEmptyState.vue'
import { computed,ref } from 'vue'
import { rows,state,mutate } from '../state/household'
import { useSubmission } from '../lib/submission'
const props=defineProps<{resource:'wishlist-items'|'approval-requests';id:string}>()
const text=ref(''),{saving,error,retryId,run}=useSubmission()
const comments=computed(()=>rows('comments').filter(x=>x.target_resource===props.resource&&x.target_id===props.id).sort((a,b)=>a.created_at.localeCompare(b.created_at)))
async function send(){await run(()=>mutate('comment.create',{target_resource:props.resource,target_id:props.id,text:text.value}),()=>{text.value=''})}
</script>
<template><section class="section-space"><h3>Comments</h3><div v-for="comment in comments" :key="comment.id" class="comment"><strong>{{rows('users').find(x=>x.id===comment.actor_id)?.name}}</strong><p>{{comment.text}}</p><small>{{new Date(comment.created_at).toLocaleString()}}</small></div><PurchaseEmptyState v-if="!comments.length" /><form @submit.prevent="send"><AppLoading v-if="saving" compact label="Sending comment…" /><div v-if="error" role="alert" class="notice error">{{error}}</div><label>Comment<textarea v-model="text" :disabled="!state.online||saving||!!retryId" required maxlength="4000" /></label><button class="button" :disabled="!state.online||saving">{{retryId?'Retry saved submission':'Add comment'}}</button><small v-if="!state.online">Reconnect to add a comment.</small></form></section></template>
