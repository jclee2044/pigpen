<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { askAdvisor, type Answer, type Turn } from '../api/advisor'
import type { Finding, Review } from '../api/reviews'
import { state } from '../state/household'
import { monthLabel } from '../lib/money'
import AppIcon from './AppIcon.vue'
import pig from '../../../assets/advisor/pig-greeting.webp'
const props=defineProps<{review:Review;finding?:Finding;expanded:boolean}>()
const emit=defineEmits<{expand:[];close:[]}>()
const messages=ref<{question:string;context:string;answer:Answer}[]>([])
const draft=ref(''),pending=ref(''),error=ref(''),thinking=ref(false)
const input=ref<HTMLInputElement>(),log=ref<HTMLElement>()
let generation=0
const available=computed(()=>props.review.chat_enabled&&state.online&&!!state.selectedId)
const prompts=computed(()=>props.finding?['What drove this?','What would you suggest?']:['What should we focus on?','Where could we reallocate money?'])
watch(()=>[state.selectedId,props.review.id],()=>{generation++;messages.value=[];draft.value='';pending.value='';error.value='';thinking.value=false;emit('close')})
onUnmounted(()=>generation++)
async function focus(){await nextTick();input.value?.focus()}
defineExpose({focus})
async function send(question:string){
 if(!available.value||thinking.value||!question.trim())return
 emit('expand')
 const current=generation,context=props.finding?.title||monthLabel(props.review.month)+' analysis'
 const history:Turn[]=messages.value.slice(-3).flatMap(m=>[{role:'user',content:m.context+': '+m.question},{role:'assistant',content:m.answer.answer.slice(0,6000)}])
 pending.value=question.trim();draft.value='';error.value='';thinking.value=true
 try{
  const answer=await askAdvisor(state.selectedId,props.review.month,question.trim(),history,{review_month:props.review.month,finding_id:props.finding?.id??null})
  if(current!==generation)return
  messages.value.push({question:question.trim(),context,answer})
 }catch(e){if(current===generation){error.value=e instanceof Error?e.message:'Could not get an answer.';draft.value=question}}
 finally{if(current===generation){thinking.value=false;pending.value='';await nextTick();log.value?.lastElementChild?.scrollIntoView({block:'nearest',behavior:'instant'})}}
}
</script>
<template><section class="card review-chat" :aria-label="expanded?'Chat about monthly analysis':'Ask Sir Pennysworth about this analysis'"><header><img :src="pig" alt=""><div><h2>{{expanded?'Sir Pennysworth':'Ask Sir Pennysworth'}}</h2><small>{{monthLabel(review.month)}}<template v-if="finding"> · {{finding.title}}</template></small></div><button v-if="expanded" class="icon-button" aria-label="Close analysis chat" @click="emit('close')"><AppIcon name="close" /></button></header><div v-if="expanded" ref="log" class="review-transcript" role="log" aria-label="Analysis conversation" aria-live="polite"><template v-for="(message,index) in messages" :key="index"><div class="sent message">{{message.question}}</div><div class="pig-reply"><img :src="pig" alt=""><div class="received message">{{message.answer.answer}}<nav><RouterLink v-for="source in message.answer.sources" :key="source.path" :to="source.path">{{source.label}}</RouterLink></nav></div></div></template><div v-if="pending" class="sent message">{{pending}}</div><div v-if="thinking" class="received message" role="status">Sir Pennysworth is thinking…</div></div><p v-if="error" class="notice error" role="alert">{{error}}</p><p v-if="!state.online" role="status">Reconnect to ask Sir Pennysworth.</p><p v-else-if="!review.chat_enabled" role="status">Chat is currently unavailable.</p><template v-if="available"><div class="prompts"><button v-for="prompt in prompts" :key="prompt" class="button small" :disabled="thinking" @click="send(prompt)">{{prompt}}</button></div><form class="composer" @submit.prevent="send(draft)"><input ref="input" v-model="draft" maxlength="1000" required autocomplete="off" aria-label="Message Sir Pennysworth about this analysis" placeholder="Message Sir Pennysworth…"><button class="button primary" :disabled="thinking||!draft.trim()" aria-label="Send analysis question">↑</button></form></template></section></template>
<style scoped>
.review-chat{border:2px solid var(--brand-rose);overflow-wrap:anywhere}.review-chat header{display:flex;align-items:center;gap:12px}.review-chat header>img{width:64px;height:54px;object-fit:contain;flex:none}.review-chat h2{margin:0}.review-chat header>div{min-width:0}.review-chat header .icon-button{margin-left:auto;flex:none}.prompts{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0}.prompts .button{border-radius:20px;white-space:normal;text-align:left}.composer{display:flex;gap:8px;align-items:center;margin:0}.composer input{flex:1;min-width:0;border-radius:24px}.composer button{border-radius:24px}.review-transcript{display:flex;flex-direction:column;gap:14px;margin:20px -12px;padding:14px 12px;max-height:52svh;overflow:auto;background:var(--page);overscroll-behavior:contain}.message{max-width:90%;padding:12px 16px;border-radius:22px;font-size:15px;line-height:1.5;white-space:pre-wrap}.sent{align-self:flex-end;background:#a94665;color:#fff;border-bottom-right-radius:5px}.received{align-self:flex-start;background:var(--track);color:var(--ink);border-bottom-left-radius:5px}.pig-reply{display:flex;align-items:flex-end;gap:6px}.pig-reply img{width:34px;height:34px;object-fit:contain;flex:none}.message nav{display:flex;flex-wrap:wrap;gap:10px;font-size:12px;margin-top:10px}@media(max-width:380px){.review-chat header>img{width:46px}.review-chat h2{font-size:22px}}
</style>
