<script setup lang="ts">
import { nextTick,onBeforeUnmount,onMounted,ref,watch } from 'vue'
import { money } from '../lib/money'
import type { summary } from '../lib/selectors'
const props=defineProps<{rows:ReturnType<typeof summary>['rows']}>()
const box=ref<HTMLElement>(),table=ref<HTMLTableElement>()
let observer:ResizeObserver|undefined,lastWidth=0
function fit(){
 if(!table.value)return
 table.value.style.setProperty('--table-scale','1')
 let scale=1
 for(const text of table.value.querySelectorAll<HTMLElement>('.table-number,th span')){
  const cell=text.parentElement!
  const style=getComputedStyle(cell)
  const available=cell.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight)
  const width=text.getBoundingClientRect().width
  if(width>0)scale=Math.min(scale,Math.max(0,available-1)/width)
 }
 table.value.style.setProperty('--table-scale',String(scale))
}
onMounted(()=>{
 observer=new ResizeObserver(entries=>{
  const width=entries[0]?.contentRect.width??0
  if(width!==lastWidth){lastWidth=width;fit()}
 })
 observer.observe(box.value!)
 fit()
 void document.fonts.ready.then(fit)
})
watch(()=>props.rows,async()=>{await nextTick();fit()},{deep:true})
onBeforeUnmount(()=>observer?.disconnect())
</script>
<template>
<section ref="box" class="card budget-table">
 <table ref="table">
  <colgroup><col class="category-column" /><col /><col /><col /></colgroup>
  <thead><tr><th><span>Category</span></th><th class="right"><span>Budgeted</span></th><th class="right"><span>Actual</span></th><th class="right"><span>Remaining</span></th></tr></thead>
  <tbody><tr v-for="c in rows.filter(x=>x.active||x.actual||x.allocated)" :key="c.id"><td><strong>{{c.name}}</strong><small v-if="!c.active"> · Archived</small></td><td class="right"><span class="table-number">{{money(c.allocated)}}</span></td><td class="right"><span class="table-number">{{money(c.actual)}}</span></td><td class="right" :class="{negative:c.remaining<0}"><span class="table-number">{{money(c.remaining)}}</span></td></tr></tbody>
 </table>
</section>
</template>
<style scoped>
.budget-table{min-width:0}
table{table-layout:fixed;font-size:calc(16px * var(--table-scale,1))}
.category-column{width:28%}
th{font-size:calc(14px * var(--table-scale,1))}
th span,.table-number{display:inline-block;white-space:nowrap}
td{border:0;padding-top:9px;padding-bottom:9px}
td:first-child{overflow-wrap:anywhere}
td small{font-size:inherit}
@media(max-width:760px){th,td{padding-left:4px;padding-right:4px}}
</style>
