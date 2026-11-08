<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'
import FitMoney from './FitMoney.vue'
import { money } from '../lib/money'
const props=defineProps<{expected:number;rows:{id:string;name:string;allocated:number;active:boolean;kind?:string}[]}>()
const colors=['#a94665','#6a8261','#d99b47','#718eb4','#9b79ab','#c66e50','#4b9392','#b98091','#858044','#827169']
const entries=computed(()=>{
 const rows=props.rows.filter(x=>x.active||x.allocated).map(x=>({...x,name:x.name.toLowerCase()==='uncategorized'?x.name+' (allocated)':x.name}))
 const allocated=rows.reduce((n,x)=>n+x.allocated,0)
 const personalIndex=rows.findIndex(x=>x.kind==='personal')
 rows.splice(personalIndex<0?rows.length:personalIndex,0,{id:'unallocated-income',name:'Uncategorized',allocated:Math.max(0,props.expected-allocated),active:true})
 const total=rows.reduce((n,x)=>n+x.allocated,0)
 let offset=0
 return rows.map((row,index)=>{const percent=total?row.allocated/total*100:0;const entry={...row,percent,offset,color:colors[index]??`hsl(${(index*137.5)%360} 35% 48%)`};offset+=percent;return entry})
})
const chartId=useId()
const selectedId=ref<string|null>(null)
const wheel=ref<SVGSVGElement>()
function dismissOutside(event:PointerEvent){
 if(event.isPrimary&&event.button===0&&dragging===undefined&&event.target instanceof Node&&!wheel.value?.contains(event.target)&&!legend.value?.contains(event.target))selectedId.value=null
}
const pointerFocus=ref(false)
const selected=computed(()=>entries.value.find(entry=>entry.id===selectedId.value))
const segments=computed(()=>entries.value.filter(entry=>entry.percent>0))
const incomePercent=(amount:number)=>props.expected>0?`${(amount/props.expected*100).toFixed(1)}% of expected income`:'No expected income set'
const description=(entry:typeof entries.value[number])=>`${entry.name}, ${money(entry.allocated)}, ${incomePercent(entry.allocated)}`
let dragging:number|undefined
function selectAt(event:PointerEvent,starting=false){
 const svg=event.currentTarget as SVGSVGElement
 const box=svg.getBoundingClientRect()
 const x=(event.clientX-box.left)/box.width*120-60
 const y=(event.clientY-box.top)/box.height*120-60
 const radius=Math.hypot(x,y)
 if(starting&&(radius<37.5||radius>54.5))return false
 // Drawing starts at twelve o'clock and proceeds clockwise.
 const position=((Math.atan2(y,x)*180/Math.PI+450)%360)/360*100
 const entry=segments.value.find(entry=>position>=entry.offset&&position<entry.offset+entry.percent)
 if(!entry)return false
 selectedId.value=entry.id
 return true
}
function startSelection(event:PointerEvent){
 pointerFocus.value=true
 if(dragging!==undefined||!event.isPrimary||event.button!==0)return
 if(!selectAt(event,true)){selectedId.value=null;return}
 dragging=event.pointerId
 ;(event.currentTarget as SVGSVGElement).setPointerCapture(event.pointerId)
}
function moveSelection(event:PointerEvent){if(dragging===event.pointerId)selectAt(event)}
function endSelection(event:PointerEvent){if(dragging===event.pointerId)dragging=undefined}
function selectWithKeyboard(event:KeyboardEvent){
 pointerFocus.value=false
 const list=segments.value
 if(event.key==='Escape'){selectedId.value=null;return}
 if(!list.length||!['ArrowRight','ArrowDown','ArrowLeft','ArrowUp','Home','End'].includes(event.key))return
 event.preventDefault()
 const index=list.findIndex(entry=>entry.id===selectedId.value)
 const next=event.key==='Home'?0:event.key==='End'?list.length-1:index<0?0:(index+(['ArrowLeft','ArrowUp'].includes(event.key)?-1:1)+list.length)%list.length
 selectedId.value=list[next]!.id
}
watch(()=>JSON.stringify([props.expected,entries.value.map(({id,name,allocated})=>[id,name,allocated])]),()=>{selectedId.value=null})
const legend=ref<HTMLElement>()
const legendWidth=ref(0)
// Prefer even rows over filling the first row and leaving one category alone.
const legendColumns=computed(()=>{
 const capacity=Math.max(1,Math.min(4,Math.floor((legendWidth.value+24)/164)))
 return Math.ceil(entries.value.length/Math.ceil(entries.value.length/capacity))
})
const legendPositions=computed(()=>{
 const columns=legendColumns.value
 const perColumn=Math.floor(entries.value.length/columns)
 const extra=entries.value.length%columns
 return Array.from({length:columns},(_,column)=>{
  const count=perColumn+(column<extra?1:0)
  return Array.from({length:count},(_,row)=>({gridRow:row+1,gridColumn:`${column*2+1} / span 2`}))
 }).flat()
})
let observer:ResizeObserver|undefined
onMounted(()=>{
 document.addEventListener('pointerdown',dismissOutside,true)
 observer=new ResizeObserver(([entry])=>{if(entry)legendWidth.value=entry.contentRect.width})
 if(legend.value)observer.observe(legend.value)
})
onBeforeUnmount(()=>{observer?.disconnect();document.removeEventListener('pointerdown',dismissOutside,true)})
const total=computed(()=>entries.value.reduce((n,x)=>n+x.allocated,0))
const overBudget=computed(()=>Math.max(0,props.rows.reduce((n,x)=>n+x.allocated,0)-props.expected))
</script>
<template>
<section class="card budget-chart" aria-label="Budget allocation by category">
 <div class="budget-donut"><svg ref="wheel" data-touch-interactive viewBox="0 0 120 120" role="listbox" tabindex="0" :class="{'pointer-focus':pointerFocus}" @blur="pointerFocus=false" aria-label="Budget categories. Tap or drag around the wheel, or use arrow keys to select." :aria-activedescendant="selected&&selected.percent>0?`${chartId}-${selected.id}`:undefined" @pointerdown="startSelection" @pointermove="moveSelection" @pointerup="endSelection" @pointercancel="endSelection" @lostpointercapture="endSelection" @keydown="selectWithKeyboard"><circle aria-hidden="true" cx="60" cy="60" r="46" fill="none" stroke="var(--line)" stroke-width="17"/><circle v-for="entry in segments" :id="`${chartId}-${entry.id}`" :key="entry.id" role="option" :aria-label="description(entry)" :aria-selected="selected?.id===entry.id" :class="{'segment-muted':selected&&selected.percent>0&&selected.id!==entry.id}" cx="60" cy="60" r="46" fill="none" :stroke="entry.color" :stroke-width="selected?.id===entry.id?20:17" pathLength="100" :stroke-dasharray="`${entry.percent} ${100-entry.percent}`" :stroke-dashoffset="-entry.offset" transform="rotate(-90 60 60)" /></svg><div class="donut-center" role="status" aria-live="polite" aria-atomic="true"><div v-if="selected" class="donut-callout" :aria-label="description(selected)"><small class="donut-category" :title="selected.name">{{selected.name}}</small><FitMoney class="donut-total" :amount="selected.allocated" /><small class="donut-share">{{expected>0?`${(selected.allocated/expected*100).toFixed(1)}%`:'No expected income'}}</small></div><template v-else><small>Expected income</small><FitMoney class="donut-total" :amount="expected" /></template></div></div>
 <ul ref="legend" class="budget-legend" @keydown.esc="selectedId=null" :style="{'--legend-columns':legendColumns}"><li v-for="(entry,index) in entries" :key="entry.id" :style="legendPositions[index]"><button type="button" :aria-pressed="selected?.id===entry.id" @click="selectedId=entry.id"><span class="legend-swatch" :style="{background:entry.color}"/><span>{{entry.name}}</span></button></li></ul>
 <p v-if="overBudget" class="text-small chart-empty">Budgets exceed expected income by {{money(overBudget)}}. Percentages show shares of total allocations; Uncategorized is 0%.</p>
 <p v-if="!total" class="text-small chart-empty">Set category amounts to see your budget breakdown.</p>
</section>
</template>
<style scoped>
.budget-chart{display:flex;flex-direction:column;align-items:center;gap:28px;margin-bottom:22px}
.budget-donut{position:relative;width:75%;max-width:300px;aspect-ratio:1;flex-shrink:0}
.budget-donut svg{display:block;width:100%;height:100%;touch-action:none;cursor:crosshair;border-radius:50%;outline:none;-webkit-tap-highlight-color:transparent}
.budget-donut svg:focus-visible:not(.pointer-focus){outline:3px solid var(--focus);outline-offset:4px}
.segment-muted{opacity:.35}
.donut-callout{width:100%;min-width:0;display:flex;flex-direction:column;align-items:center;gap:4px}
.donut-category{max-width:100%;font-size:12px;line-height:1.2;overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden}
.donut-share{font-size:12px;line-height:1.2}
.donut-center{position:absolute;inset:27%;pointer-events:none;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:4px}
.donut-total{width:100%;font-size:24px;font-weight:400}
.budget-legend{list-style:none;padding:0;margin:0;width:100%;max-width:880px;display:grid;grid-template-columns:repeat(calc(var(--legend-columns)*2),minmax(0,1fr));gap:14px 12px}
.budget-legend li{min-width:0}
.budget-legend button{display:grid;grid-template-columns:10px minmax(0,1fr);gap:8px;align-items:center;width:100%;min-height:0;padding:0;border:0;border-radius:8px;background:transparent;color:var(--ink);font-size:13px;text-align:left}
.budget-legend button:hover{background:var(--hover)}
.budget-legend button[aria-pressed="true"]{background:var(--selected);color:var(--rose);font-weight:700}
.budget-legend button>span:nth-child(2){overflow-wrap:anywhere}
.legend-swatch{width:10px;height:10px;border-radius:50%}
.chart-empty{align-self:stretch;margin:0}
@media(max-width:480px){.budget-chart{gap:22px;padding:16px}.budget-donut{max-width:240px}.donut-total{font-size:20px}.donut-center small{font-size:10px}}
</style>
