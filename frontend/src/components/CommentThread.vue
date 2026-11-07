<script setup lang="ts">
import { computed,ref } from 'vue'
import { rows,state,mutate } from '../state/household'
import { useSubmission } from '../lib/submission'
const props=defineProps<{resource:'wishlist-items'|'approval-requests';id:string}>()
const text=ref(''),{saving,error,retryId,run}=useSubmission()
const comments=computed(()=>rows('comments').filter(x=>x.target_resource===props.resource&&x.target_id===props.id).sort((a,b)=>a.created_at.localeCompare(b.created_at)))
async function send(){await run(()=>mutate('comment.create',{target_resource:props.resource,target_id:props.id,text:text.value}),()=>{text.value=''})}
</script>
<template><section class="section-space"><h3>Comments</h3><div v-for="comment in comments" :key="comment.id" class="comment"><strong>{{rows('users').find(x=>x.id===comment.actor_id)?.name}}</strong><p>{{comment.text}}</p><small>{{new Date(comment.created_at).toLocaleString()}}</small></div><p v-if="!comments.length" class="text-small">No comments yet.</p><form @submit.prevent="send"><div v-if="error" role="alert" class="notice error">{{error}}</div><label>Comment<textarea v-model="text" :disabled="!state.online||saving||!!retryId" required maxlength="4000" /></label><button class="button" :disabled="!state.online||saving">{{retryId?'Retry saved submission':'Add comment'}}</button><small v-if="!state.online">Reconnect to add a comment.</small></form></section></template>
