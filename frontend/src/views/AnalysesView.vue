<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { getReview, getReviews, type Review, type ReviewSummary, type Finding } from '../api/reviews'
import { state } from '../state/household'
import { money, monthLabel } from '../lib/money'
import AppLoading from '../components/AppLoading.vue'
import FitMoney from '../components/FitMoney.vue'
import ReviewFinding from '../components/ReviewFinding.vue'
import ReviewChat from '../components/ReviewChat.vue'
const route=useRoute(),router=useRouter()
const report=ref<Review>(),items=ref<ReviewSummary[]>([]),next=ref<string|null>(null)
const loading=ref(false),error=ref(''),chatting=ref(false),finding=ref<Finding>()
const chat=ref<InstanceType<typeof ReviewChat>>()
const month=computed(()=>typeof route.params.month==='string'?route.params.month:'')
let generation=0
async function load(more=false){
 const current=++generation;loading.value=true;error.value=''
 if(!more){report.value=undefined;items.value=[];next.value=null;chatting.value=false;finding.value=undefined}
 try{
  if(month.value){const result=await getReview(month.value);if(current===generation)report.value=result}
  else{
   const result=await getReviews(more?next.value??undefined:undefined)
   if(current!==generation)return
   items.value=more?[...items.value,...result.items]:result.items;next.value=result.next_before
   if(typeof route.query.report==='string'){
    const match=items.value.find(r=>r.id===route.query.report)
    if(match){void router.replace('/analyses/'+match.month);return}
    if(next.value){void load(true);return}
   }
  }
 }catch(e){if(current===generation)error.value=e instanceof Error?e.message:'Could not load analyses.'}
 finally{if(current===generation)loading.value=false}
}
watch(()=>[month.value,route.query.report,state.selectedId,state.online],()=>void load(),{immediate:true})
onUnmounted(()=>generation++)
function ask(selected:Finding){finding.value=selected;chatting.value=true;void chat.value?.focus()}
function close(){chatting.value=false;finding.value=undefined}
</script>
<template><div class="analyses-page"><nav class="analysis-nav"><button v-if="chatting" class="inline-link" @click="close">‹ {{monthLabel(month)}} analysis</button><RouterLink v-else to="/">‹ Home</RouterLink><RouterLink v-if="month" to="/analyses">Past analyses</RouterLink></nav><div class="page-heading"><h1>{{month?monthLabel(month)+' analysis':'Past analyses'}}</h1></div><AppLoading v-if="loading" compact /><div v-if="error" class="notice error" role="alert">{{error}} <button class="button small" @click="load()">Retry</button></div><template v-if="report"><template v-if="!chatting"><section class="card blush review-totals"><div><small>Budgeted</small><FitMoney :amount="report.totals.budgeted_minor" /></div><div><small>Spent</small><FitMoney :amount="report.totals.spent_minor" /></div><div><small>{{report.totals.remaining_minor<0?'Over':'Under'}} budget</small><FitMoney :amount="Math.abs(report.totals.remaining_minor)" /></div></section><p class="analysis-summary">{{report.summary}}</p><p v-if="report.data_changed" class="notice">Records have changed since this analysis was prepared. The figures below are the saved review.</p><ReviewFinding v-for="item in report.findings" :key="item.id" :finding="item" @ask="ask" /><details class="review-basis"><summary>Review details</summary><p>Prepared {{new Date(report.created_at).toLocaleString()}}. Confirmed purchases only.</p><p v-if="report.coverage.comparison_months.length">Comparison months: {{report.coverage.comparison_months.map(monthLabel).join(', ')}}.</p><p v-else>No earlier recorded months to compare.</p><p v-if="report.coverage.included_purchase_count<report.coverage.purchase_count">Findings use {{report.coverage.included_purchase_count}} of {{report.coverage.purchase_count}} purchases. Totals include all purchases.</p><p v-if="report.totals.savings_allocated_minor||report.totals.savings_actual_minor">Savings: {{money(report.totals.savings_allocated_minor)}} allocated; {{money(report.totals.savings_actual_minor)}} net contributions. Separate from expenses above.</p></details></template><ReviewFinding v-else-if="finding" :finding="finding" compact /><ReviewChat ref="chat" :review="report" :finding="finding" :expanded="chatting" @expand="chatting=true" @close="close" /></template><template v-else-if="!month"><section v-if="items.length" class="card"><RouterLink v-for="item in items" :key="item.id" class="analysis-history-row" :to="'/analyses/'+item.month"><strong>{{monthLabel(item.month)}}</strong><span>{{item.finding_count}} {{item.finding_count===1?'finding':'findings'}} →</span></RouterLink></section><p v-else-if="!loading&&!error">No analyses yet. Reviews appear after a month has ended.</p><button v-if="next" class="button more-reviews" :disabled="loading" @click="load(true)">Load earlier analyses</button></template></div></template>
<style scoped>
.analyses-page{max-width:760px;margin:0 auto}.analysis-nav{display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:13px;font-weight:700;margin:0 0 18px;min-height:32px}.review-totals{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:16px}.review-totals strong{display:block;font:30px Georgia;margin-top:8px;overflow-wrap:anywhere}.review-totals small{font-size:12px}.analysis-summary{font-size:14px;margin:16px 0}.review-basis{margin:18px 0}.review-basis p{font-size:12px}.analysis-history-row{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:20px 0;border-bottom:1px solid var(--line);font-size:14px}.analysis-history-row:first-child{padding-top:0}.analysis-history-row:last-child{border:0;padding-bottom:0}.analysis-history-row span{font-size:12px;white-space:nowrap}.more-reviews{margin-top:18px}@media(max-width:400px){.review-totals{gap:8px;padding:16px}.review-totals strong{font-size:25px}}
</style>
