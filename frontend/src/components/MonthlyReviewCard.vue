<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { getReviews, type ReviewList } from '../api/reviews'
import { state, household } from '../state/household'
import { money, monthLabel } from '../lib/money'
import AppIcon from './AppIcon.vue'

const result=ref<ReviewList>()
const now=ref(Date.now())
let generation=0
let timer:ReturnType<typeof setInterval>|undefined
async function load(){
 const current=++generation
 now.value=Date.now()
 if(!state.online||!state.selectedId){result.value=undefined;return}
 try{const response=await getReviews();if(current===generation)result.value=response}catch{if(current===generation)result.value=undefined}
}
const visible=computed(()=>{
 if(!result.value?.show_home||!result.value.latest)return false
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:household.value?.timezone||'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now.value)
 const part=(type:string)=>parts.find(p=>p.type===type)?.value
 const currentMonth=`${part('year')}-${part('month')}`
 if(currentMonth!==result.value.current_month)return false
 return result.value.latest.is_preview?result.value.latest.month===currentMonth:Number(part('day'))<=5
})
const latest=computed(()=>result.value?.latest)
watch(()=>[state.online,state.selectedId,state.lastSync],load,{immediate:true})
function wake(){if(document.visibilityState==='visible')void load()}
onMounted(()=>{timer=setInterval(()=>void load(),60000);document.addEventListener('visibilitychange',wake)})
onUnmounted(()=>{generation++;clearInterval(timer);document.removeEventListener('visibilitychange',wake)})
</script>
<template><section v-if="visible&&latest" class="card monthly-review-card"><h2>{{monthLabel(latest.month)}} {{latest.is_preview?'preview':'analysis'}}</h2><p v-if="latest.is_preview">Month-to-date analysis</p><p v-else>{{money(Math.abs(latest.remaining_minor))}} {{latest.remaining_minor<0?'over':'under'}} budget · {{latest.finding_count}} {{latest.finding_count===1?'finding':'findings'}}</p><RouterLink class="button review-action" :to="'/analyses/'+latest.month">Review analysis <AppIcon name="arrow" /></RouterLink></section></template>
<style scoped>.monthly-review-card{background:var(--brand-rose);margin:0 0 24px auto;width:min(100%,560px);color:#fff}.monthly-review-card p{color:inherit;margin:12px 0 18px}.review-action{background:#edbdce;border-color:#edbdce;color:#3d3331}.review-action:hover{filter:brightness(.96)}.review-action:focus-visible{outline-color:#fff}:global([data-theme=dark] .monthly-review-card .review-action){background:#603746;border-color:#603746;color:var(--ink)}</style>
