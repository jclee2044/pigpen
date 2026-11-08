<script setup lang="ts">
import AppIcon from '../components/AppIcon.vue'
import AppLoading from '../components/AppLoading.vue'
import { computed,ref,watch } from 'vue'
import { useRoute,useRouter } from 'vue-router'
import PurchaseSpending from '../components/PurchaseSpending.vue'
import PurchaseDetail from '../components/PurchaseDetail.vue'
import { rows,state,mutate } from '../state/household'
import { shell } from '../state/shell'
import { spendingWeeks } from '../lib/purchaseSpending'
import { recent } from '../lib/selectors'
import type { Purchase } from '../api/models'
import PurchaseForm from '../components/PurchaseForm.vue'
import PurchaseRows from '../components/PurchaseRows.vue'
import AppDialog from '../components/AppDialog.vue'
import { useSubmission } from '../lib/submission'
const deleting=ref<Purchase>()
const {saving,error,retryId,run}=useSubmission()
async function deletePurchase(){
 const purchase=deleting.value
 if(!purchase)return
 await run(()=>mutate('purchase.delete',{expected_revision:purchase.revision},purchase.id),()=>{deleting.value=undefined})
}
function requestDelete(purchase:Purchase){if(saving.value||retryId.value)return;error.value='';deleting.value=purchase}
const route=useRoute(),router=useRouter()
const detailId=ref(String(route.query.detail??''))
const detail=computed(()=>rows('purchases').find(x=>x.id===detailId.value))
watch(()=>route.query.detail,id=>detailId.value=String(id??''))
function closeDetail(){detailId.value='';void router.replace('/purchases')}
const add=ref(false),edit=ref<Purchase>(),category=ref('')
const selectedWeek=ref('')
const monthPurchases=computed(()=>recent(rows('purchases').filter(x=>x.transaction_date.slice(0,7)===shell.month&&(!category.value||x.category_id===category.value||rows('categories').some(c=>c.id===x.category_id&&c.parent_id===category.value)))))
const purchases=computed(()=>selectedWeek.value ? spendingWeeks(shell.month,monthPurchases.value).find(w=>w.start===selectedWeek.value)?.items??[] : monthPurchases.value)
</script>
<template><div class="page-heading"><div><h1>Purchases</h1></div><button class="button primary icon-only" aria-label="New purchase" title="New purchase" @click="add=true"><AppIcon name="plus" /></button></div><div class="toolbar purchases-toolbar"><label>Category<select aria-label="Category" v-model="category"><option value="">All categories</option><option v-for="c in rows('categories').filter(x=>x.kind!=='savings')" :key="c.id" :value="c.id">{{c.name}}</option></select></label></div><PurchaseSpending v-model:month="shell.month" v-model:selected-week="selectedWeek" :purchases="monthPurchases" :categories="rows('categories')" /><section class="card"><PurchaseRows :purchases="purchases" swipe-to-delete @select="p=>detailId=p.id" @delete="requestDelete" /></section><AppDialog v-if="deleting" title="Delete purchase?" @close="!saving&&!retryId&&(deleting=undefined)"><AppLoading v-if="saving" compact /><p>Delete “{{deleting.item}}”? It will be removed from spending totals.</p><div v-if="error" class="notice error" role="alert">{{error}}</div><p v-if="!state.online" class="notice">Reconnect to delete this purchase.</p><div class="actions"><button class="button" :disabled="saving||!!retryId" @click="deleting=undefined">Cancel</button><button class="button danger" :disabled="!state.online||saving" @click="deletePurchase">{{saving?'Deleting…':retryId?'Retry saved submission':'Delete purchase'}}</button></div></AppDialog><PurchaseDetail v-if="detail" :purchase="detail" @close="closeDetail" @edit="edit=detail;closeDetail()" /><PurchaseForm v-if="add||edit" :purchase="edit" @close="add=false;edit=undefined" /></template>
