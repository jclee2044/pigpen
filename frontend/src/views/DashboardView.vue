<script setup lang="ts">
import { computed,ref } from 'vue'
import { RouterLink } from 'vue-router'
import { activeUser,state,rows } from '../state/household'
import { shell } from '../state/shell'
import { summary,recent } from '../lib/selectors'
import { money } from '../lib/money'
import PurchaseForm from '../components/PurchaseForm.vue'
import PurchaseRows from '../components/PurchaseRows.vue'
import AppIcon from '../components/AppIcon.vue'
const totals=computed(()=>summary(state.records,shell.month)),add=ref(false)
const purchases=computed(()=>recent(rows('purchases').filter(x=>x.transaction_date.slice(0,7)===shell.month)).slice(0,5))
const attention=computed(()=>rows('approval-requests').filter(r=>r.status==='open'&&r.requester_id!==activeUser.value?.id&&!rows('approval-votes').some(v=>v.request_id===r.id&&v.reviewer_id===activeUser.value?.id&&v.approved&&v.request_revision===r.revision)))
const approvalStatus=computed(()=>attention.value.length?`${attention.value.length} ${attention.value.length===1?'request needs':'requests need'} review`:'No requests to review')
const pendingPurchases=computed(()=>state.pending.filter(x=>x.operation.kind==='purchase.create'&&x.state!=='blocked'))
</script>
<template>
 <div class="page-heading"><h1>Dashboard</h1><button class="button primary" @click="add=true">+ Add purchase</button></div>
 <div class="toolbar dashboard-toolbar">
  <label><span class="sr-only">Selected month</span><input v-model="shell.month" type="month" /></label>
  <RouterLink to="/approvals" class="approval-status" :aria-label="'Approvals: '+approvalStatus">
   <span class="approval-status-icon" :class="{pending:attention.length}"><AppIcon :name="attention.length?'shield':'check'" /></span>
   <span class="approval-status-copy"><strong>Approvals</strong><span role="status">{{approvalStatus}}</span></span>
   <AppIcon name="arrow" class="approval-status-arrow" />
  </RouterLink>
 </div>
 <div class="metrics">
  <section class="card"><span class="metric-label">Budgeted</span><strong class="metric-value" data-testid="allocated">{{money(totals.allocated)}}</strong></section>
  <section class="card"><span class="metric-label">Spent</span><strong class="metric-value" data-testid="spent">{{money(totals.spent)}}</strong><small>Confirmed purchases</small></section>
  <section class="card blush"><span class="metric-label">Budget remaining</span><strong class="metric-value" data-testid="remaining">{{money(totals.remaining)}}</strong><small>Includes savings activity</small></section>
 </div>
 <div v-if="pendingPurchases.length" class="notice"><strong>{{pendingPurchases.length}} {{pendingPurchases.length===1?'purchase':'purchases'}} waiting to sync.</strong> Not included in confirmed spending.</div>
 <section class="card">
  <div class="section-heading" style="margin-top:0"><h2>Budget by category</h2><RouterLink to="/budget">View budget →</RouterLink></div>
  <div class="progress" role="img" :aria-label="`${money(totals.spent)} spent of ${money(totals.allocated)} budgeted`"><span :style="{width:Math.min(100,totals.allocated?totals.spent/totals.allocated*100:0)+'%'}" /></div>
  <div class="summary-split"><div v-for="c in totals.rows.filter(x=>x.active&&x.kind!=='savings').slice(0,3)" :key="c.id"><small>{{c.name}}</small><strong :class="{negative:c.remaining<0}">{{money(c.remaining)}} left</strong></div></div>
 </section>
 <div class="section-heading"><h2>Recent purchases</h2><RouterLink to="/purchases">View all →</RouterLink></div>
 <section class="card"><PurchaseRows :purchases="purchases" @select="p=>$router.push('/purchases?detail='+p.id)" /></section>
 <PurchaseForm v-if="add" @close="add=false" />
</template>
