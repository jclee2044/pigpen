<script setup lang="ts">
import AppLoading from '../components/AppLoading.vue'
import { computed,ref } from 'vue'
import { state,mutate } from '../state/household'
import { shell } from '../state/shell'
import { summary } from '../lib/selectors'
import { orderCategories } from '../lib/categoryOrder'
import { amountToPercent,percentToAmount } from '../lib/budgetPercent'
import { money,inputMoney,parseMoney } from '../lib/money'
import AppDialog from '../components/AppDialog.vue'
import { useSubmission } from '../lib/submission'
import FinancePanel from '../components/FinancePanel.vue'
import BudgetMoneyInput from '../components/BudgetMoneyInput.vue'
import FitMoney from '../components/FitMoney.vue'
import BudgetDonut from '../components/BudgetDonut.vue'
import CategoryForm from '../components/CategoryForm.vue'
import CategoryManager from '../components/CategoryManager.vue'
import CategoryOrderList from '../components/CategoryOrderList.vue'
import type { Category } from '../api/models'
const totals=computed(()=>summary(state.records,shell.month)),editing=ref(false),expected=ref('0.00'),values=ref<Record<string,string>>({})
const managingCategories=ref(false)
const allocationMode=ref<'dollars'|'percentages'>('dollars')
const incomeMinor=computed(()=>{try{return parseAmount(expected.value)}catch{return 0}})
function switchAllocationTab(event:KeyboardEvent){
 if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return
 event.preventDefault()
 allocationMode.value=event.key==='Home'?'dollars':event.key==='End'?'percentages':allocationMode.value==='dollars'?'percentages':'dollars'
 const tabs=event.currentTarget as HTMLElement
 tabs.querySelector<HTMLButtonElement>(allocationMode.value==='dollars'?'#dollar-tab':'#percentage-tab')?.focus()
}
function allocationValue(id:string){
 const amount=values.value[id]??'0.00'
 if(allocationMode.value==='dollars')return amount
 try{return amountToPercent(parseAmount(amount),incomeMinor.value)}catch{return '0.00'}
}
function setAllocation(id:string,value:string){
 values.value[id]=allocationMode.value==='dollars'?value:inputMoney(percentToAmount(value,incomeMinor.value))
}
const {saving,error,retryId,run}=useSubmission()
const budgetId=ref<string>(),budgetRevision=ref(0),addingCategory=ref(false)
const categorySubmission=useSubmission()
const orderSubmission=useSubmission(),orderDraft=ref<string[]>()
const orderedRows=computed(()=>{
 const order=orderDraft.value??state.records.household[0]?.category_order??[]
 return orderCategories(totals.value.rows,order)
})
async function reorderCategories(ids:string[]){
 orderDraft.value=ids
 const household=state.records.household[0]
 if(!household)return
 await orderSubmission.run(()=>mutate('category.reorder',{expected_revision:household.revision,category_ids:ids},household.id),()=>{orderDraft.value=undefined})
}
const deletingCategory=ref<Category>()
async function deleteCategory(){
 const category=deletingCategory.value
 if(!category)return
 await categorySubmission.run(()=>mutate('category.update',{name:category.name,active:false,expected_revision:category.revision},category.id),()=>{
  const original=totals.value.rows.find(x=>x.id===category.id)?.allocated??0
  if(original&&budgetId.value)values.value[category.id]=inputMoney(original)
  else delete values.value[category.id]
  deletingCategory.value=undefined
 })
}
function categoryAdded(){
 addingCategory.value=false
 for(const row of totals.value.rows.filter(x=>x.active))if(!(row.id in values.value))values.value[row.id]='0.00'
}
function parseAmount(value:string){const [whole,fraction='']=value.split('.');return parseMoney((whole?.replace(/^0+(?=\d)/,'')||'0')+'.'+fraction.padEnd(2,'0'))}
function edit(){allocationMode.value='dollars';budgetId.value=totals.value.budget?.id;budgetRevision.value=totals.value.budget?.revision??0;retryId.value='';values.value=Object.fromEntries(totals.value.rows.filter(x=>x.active||state.records.allocations.some(a=>!a.deleted&&a.budget_month_id===budgetId.value&&a.category_id===x.id)).map(x=>[x.id,inputMoney(x.allocated)]));expected.value=inputMoney(totals.value.expected);error.value='';editing.value=true}
async function save(){await run(()=>mutate('budget.set',{month:shell.month,expected_revision:budgetRevision.value,expected_income_minor:parseAmount(expected.value),allocations:Object.entries(values.value).map(([category_id,value])=>({category_id,amount_minor:parseAmount(value)}))},budgetId.value),()=>{editing.value=false})}
</script>
<template><div class="page-heading"><div><h1>Budget</h1></div><div class="actions"><button class="button" :disabled="!state.online" @click="managingCategories=true">Manage categories</button><button class="button primary" :disabled="!state.online" @click="edit">Edit</button></div></div><BudgetDonut :rows="orderedRows" :expected="totals.expected" /><div class="toolbar"><label>Budget month<input v-model="shell.month" type="month" /></label></div><div v-if="error&&!editing" role="alert" class="notice error">{{error}}</div><div class="metrics budget-metrics"><section class="card"><small>Budgeted</small><FitMoney class="metric-value" :amount="totals.allocated" /></section><section class="card"><small>Spent</small><FitMoney class="metric-value" :amount="totals.spent" /></section><section class="card sage"><small>Unbudgeted income</small><FitMoney class="metric-value" :amount="totals.expected-totals.allocated" /></section></div><section class="card budget-table"><div class="table-wrap"><table><thead><tr><th>Category</th><th class="right">Budgeted</th><th class="right">Actual</th><th class="right">Remaining</th></tr></thead><tbody><tr v-for="c in orderedRows.filter(x=>x.active||x.actual||x.allocated)" :key="c.id"><td><strong>{{c.name}}</strong><small v-if="c.kind==='savings'" style="display:block">Net savings contribution</small><small v-if="!c.active"> · Archived</small></td><td class="right">{{money(c.allocated)}}</td><td class="right">{{money(c.actual)}}</td><td class="right" :class="{negative:c.remaining<0}">{{money(c.remaining)}}</td></tr></tbody></table></div></section><p class="text-small section-space">Your budget continues each month until you edit it. Subcategories share their parent budget. Unused budgets do not carry forward.</p><FinancePanel /><AppDialog v-if="editing&&!addingCategory&&!deletingCategory" title="Edit budget" @close="editing=false"><AppLoading v-if="saving" compact /><form @submit.prevent="save"><div v-if="error" role="alert" class="notice error">{{error}}</div><fieldset class="budget-fields" :disabled="saving||!!retryId||categorySubmission.saving.value"><label>Expected income ($)<BudgetMoneyInput v-model="expected" /></label><div class="allocation-tabs" role="tablist" aria-label="Allocation units" @keydown="switchAllocationTab"><button id="dollar-tab" type="button" role="tab" :aria-selected="allocationMode==='dollars'" aria-controls="allocation-panel" :tabindex="allocationMode==='dollars'?0:-1" @click="allocationMode='dollars'">Dollars ($)</button><button id="percentage-tab" type="button" role="tab" :aria-selected="allocationMode==='percentages'" aria-controls="allocation-panel" :tabindex="allocationMode==='percentages'?0:-1" @click="allocationMode='percentages'">Percentages (%)</button></div><p v-if="allocationMode==='percentages'&&!incomeMinor" id="percentage-help" class="text-small">Enter expected income above $0 to edit percentages. Dollar amounts are kept.</p><div id="allocation-panel" role="tabpanel" :aria-labelledby="allocationMode==='dollars'?'dollar-tab':'percentage-tab'"><CategoryOrderList :rows="orderedRows.filter(x=>x.id in values)" :disabled="saving||!!retryId||orderSubmission.saving.value||!!orderSubmission.retryId.value||!state.online" @preview="orderDraft=$event" @reorder="reorderCategories"><template #default="{category:c}"><div class="allocation-row"><label :for="'allocation-'+c.id">{{c.name}}<span v-if="!c.active"> · Archived</span></label><div class="allocation-input"><BudgetMoneyInput :key="allocationMode" :disabled="!c.active||(allocationMode==='percentages'&&!incomeMinor)" :id="'allocation-'+c.id" :model-value="allocationValue(c.id)" :aria-describedby="allocationMode==='percentages'&&!incomeMinor?'percentage-help':undefined" @update:model-value="setAllocation(c.id,$event)" /><span v-if="allocationMode==='percentages'" aria-hidden="true">%</span></div><button v-if="c.active&&c.kind!=='personal'" type="button" class="icon-button delete-category" :aria-label="'Delete '+c.name+' category'" @click="deletingCategory=c">×</button></div></template></CategoryOrderList></div><div v-if="orderSubmission.error.value" role="alert" class="notice error">{{orderSubmission.error.value}}<button type="button" class="button small" :disabled="orderSubmission.saving.value" @click="reorderCategories(orderDraft??[])">Retry category order</button></div><button type="button" class="button small" @click="addingCategory=true">Add category</button></fieldset><p class="text-small">Budgets may exceed expected income.</p><button class="button primary" :disabled="saving">{{saving?'Saving…':retryId?'Retry saved submission':'Save budget'}}</button></form></AppDialog>
<CategoryManager v-if="managingCategories" @close="managingCategories=false" />
<CategoryForm v-if="addingCategory" shared-only @close="categoryAdded" />
<AppDialog v-if="deletingCategory" title="Delete category" @close="deletingCategory=undefined"><AppLoading v-if="saving" compact /><form @submit.prevent="deleteCategory"><p>Delete {{deletingCategory.name}} from available categories? Past purchases and saved budgets keep their history. Future months will skip this category.</p><div v-if="categorySubmission.error.value" role="alert" class="notice error">{{categorySubmission.error.value}}</div><button class="button danger" :disabled="categorySubmission.saving.value">{{categorySubmission.saving.value?'Deleting…':categorySubmission.retryId.value?'Retry deletion':'Delete category'}}</button></form></AppDialog>
</template>
<style scoped>
.allocation-tabs{display:flex;gap:4px;padding:4px;border-radius:12px;background:var(--paper);border:1px solid var(--line);margin-bottom:8px}.allocation-tabs button{flex:1;min-height:44px;border:0;border-radius:8px;background:transparent;color:var(--ink);font:inherit;font-weight:700;cursor:pointer}.allocation-tabs button[aria-selected=true]{background:var(--blush);color:var(--ink)}.allocation-input{display:flex;align-items:center;gap:4px;min-width:0}.allocation-input input{min-width:0;width:100%}.allocation-input span{font-weight:700}.budget-fields{gap:8px}.budget-fields>label{margin-bottom:12px}.allocation-row{grid-template-columns:minmax(0,1fr) minmax(0,150px) 36px;padding:2px 0;border:0;gap:8px}.allocation-row input{text-align:right}.delete-category{width:36px;height:44px;font-size:24px;padding:0;color:var(--rose)}.budget-fields>.button{justify-self:start;margin-top:12px}.budget-table td{border:0;padding-top:9px;padding-bottom:9px}.budget-metrics .metric-value{overflow-wrap:normal;white-space:nowrap}
@media(max-width:480px){.allocation-row{grid-template-columns:minmax(0,1fr) minmax(0,115px) 32px;gap:6px}.budget-metrics .card{padding:16px}}
</style>
