<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { Finding } from '../api/reviews'
import { money, monthLabel } from '../lib/money'
import AppIcon from './AppIcon.vue'
const props=defineProps<{finding:Finding;compact?:boolean}>()
defineEmits<{ask:[finding:Finding]}>()
const maximum=computed(()=>Math.max(1,...props.finding.chart.map(p=>p.amount_minor)))
const label=(value:string)=>/^\d{4}-\d{2}$/.test(value)?monthLabel(value):value
</script>
<template><section class="card review-finding" :class="{blush:compact}"><h3>{{finding.title}}</h3><p>{{finding.explanation}}</p><template v-if="!compact"><div v-if="finding.chart.length" class="review-chart" role="img" :aria-label="finding.chart.map(p=>label(p.label)+': '+money(p.amount_minor)).join('; ')"><div v-for="(point,index) in finding.chart" :key="index" class="chart-row"><span>{{label(point.label)}}</span><span class="chart-track"><i :style="{width:(Math.max(0,point.amount_minor)/maximum*100)+'%'}" :class="{current:index===finding.chart.length-1}" /></span><strong>{{money(point.amount_minor)}}</strong></div></div><details v-if="finding.purchases.length"><summary>View purchases ({{finding.purchases.length}})</summary><RouterLink v-for="purchase in finding.purchases" :key="purchase.id" class="review-purchase" :to="'/purchases?detail='+purchase.id"><span>{{purchase.item}}<small>{{purchase.transaction_date}}</small></span><strong>{{money(purchase.amount_minor)}}</strong></RouterLink></details><button type="button" class="button small ask-finding" @click="$emit('ask',finding)">Ask about this <AppIcon name="comments" /></button></template></section></template>
<style scoped>
.review-finding{margin-bottom:16px}.review-finding p{font-size:14px;margin:0 0 12px}.review-finding.blush p{margin:0}.review-chart{display:grid;gap:10px;margin:18px 0}.chart-row{display:grid;grid-template-columns:minmax(60px,1fr) minmax(45px,1.5fr) auto;align-items:center;gap:12px;font-size:12px}.chart-row>span:first-child{overflow-wrap:anywhere}.chart-row strong{font-weight:400;font-variant-numeric:tabular-nums}.chart-track{height:10px}.chart-track i{display:block;height:100%;border-radius:4px;background:var(--blush)}.chart-track .current{background:var(--rose)}.ask-finding{background:var(--blush);border-color:transparent;border-radius:20px;margin-top:12px}.review-purchase{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 0;border-top:1px solid var(--line);font-size:14px}.review-purchase span{min-width:0;overflow-wrap:anywhere}.review-purchase small{display:block}.review-purchase strong{white-space:nowrap}.review-finding summary{min-height:44px}
</style>
