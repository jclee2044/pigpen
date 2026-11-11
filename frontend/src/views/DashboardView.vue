<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { state,rows } from '../state/household'
import { shell } from '../state/shell'
import { summary,recent } from '../lib/selectors'
import { money } from '../lib/money'
import BudgetInsights from '../components/BudgetInsights.vue'
import PurchaseRows from '../components/PurchaseRows.vue'
import FitMoney from '../components/FitMoney.vue'
const chatting = ref(false)
// Home is already the active route while its chat panel is expanded.
const stopHomeListener = useRouter().afterEach((to, from) => {
  if (to.name === 'dashboard' && from.name === 'dashboard') chatting.value = false
})
onBeforeUnmount(stopHomeListener)
const totals=computed(()=>summary(state.records,shell.month))
const purchases=computed(()=>recent(rows('purchases').filter(x=>x.transaction_date.slice(0,7)===shell.month)).slice(0,5))
const pendingPurchases=computed(()=>state.pending.filter(x=>x.operation.kind==='purchase.create'&&x.state!=='blocked'))
</script>
<template>
 <div class="dashboard-intro" :class="{ drafting: !chatting }">
 <div v-show="!chatting" class="page-heading"><h1>Dashboard</h1></div>
 <BudgetInsights v-model:expanded="chatting" />
 </div>
 <template v-if="!chatting">
 <div class="metrics">
  <section class="card"><span class="metric-label">Budgeted</span><FitMoney class="metric-value" data-testid="allocated" :amount="totals.allocated" /></section>
  <section class="card"><span class="metric-label">Spent</span><FitMoney class="metric-value" data-testid="spent" :amount="totals.spent" /><small>Confirmed purchases</small></section>
  <section class="card blush"><span class="metric-label">Budget remaining</span><FitMoney class="metric-value" data-testid="remaining" :amount="totals.remaining" /><small>Includes savings activity</small></section>
 </div>
 <div v-if="pendingPurchases.length" class="notice"><strong>{{pendingPurchases.length}} {{pendingPurchases.length===1?'purchase':'purchases'}} waiting to sync.</strong> Not included in confirmed spending.</div>
 <section class="card">
  <div class="section-heading" style="margin-top:0"><h2>Budget by category</h2><RouterLink to="/budget">View budget →</RouterLink></div>
  <div class="progress" role="img" :aria-label="`${money(totals.spent)} spent of ${money(totals.allocated)} budgeted`"><span :style="{width:Math.min(100,totals.allocated?totals.spent/totals.allocated*100:0)+'%'}" /></div>
  <div class="summary-split"><div v-for="c in totals.rows.filter(x=>x.active&&x.kind!=='savings').slice(0,3)" :key="c.id"><small>{{c.name}}</small><strong :class="{negative:c.remaining<0}">{{money(c.remaining)}} left</strong></div></div>
 </section>
 <div class="section-heading"><h2>Recent purchases</h2><RouterLink to="/purchases">View all →</RouterLink></div>
 <section class="card"><PurchaseRows :purchases="purchases" @select="p=>$router.push('/purchases?detail='+p.id)" /></section>
 </template>
</template>
