<script setup lang="ts">
import {computed,nextTick,onBeforeUnmount,onMounted,ref,watch} from 'vue'
import type {Wish} from '../api/models'
const props=defineProps<{rows:Wish[];disabled:boolean}>()
const emit=defineEmits<{reorder:[ids:string[]]}>()
const list=ref<HTMLElement>()
const order=ref<string[]>([]),dragging=ref(''),floating=ref(''),settling=ref(false),announcement=ref('')
const position=ref({x:0,y:0,width:0,height:0})
const items=computed(()=>[...props.rows].sort((a,b)=>order.value.indexOf(a.id)-order.value.indexOf(b.id)))
watch(()=>props.rows,rows=>{if(!dragging.value)order.value=rows.map(row=>row.id)},{immediate:true})
watch(()=>props.disabled,disabled=>{if(!disabled&&!dragging.value)order.value=props.rows.map(row=>row.id)})
let pointer:number|undefined,initial:string[]=[],offset={x:0,y:0},dropTimer:ReturnType<typeof setTimeout>|undefined
let slots:ReturnType<typeof layoutBox>[]=[],scrollOrigin={x:0,y:0},last={x:0,y:0},suppressClickUntil=0
function clearClickGuard(){suppressClickUntil=0}
function guardClick(event:MouseEvent){
 if(performance.now()<suppressClickUntil&&event.detail>0){event.preventDefault();event.stopImmediatePropagation()}
}
const floatStyle=computed(()=>({transform:`translate3d(${position.value.x}px,${position.value.y}px,0)`,width:`${position.value.width}px`,height:`${position.value.height}px`}))
function element(id:string){return list.value?.querySelector<HTMLElement>(`[data-sort-wish="${id}"]`)}
function layoutBox(node:HTMLElement){
 const box=node.getBoundingClientRect(),transform=new DOMMatrixReadOnly(getComputedStyle(node).transform)
 return {left:box.left-transform.m41,top:box.top-transform.m42,width:box.width,height:box.height}
}
function move(id:string,target:string,after:boolean){
 const rows=items.value,source=rows.find(row=>row.id===id),destination=rows.find(row=>row.id===target)
 if(!source||!destination||id===target)return
 const ids=rows.map(row=>row.id),from=ids.indexOf(id)
 ids.splice(from,1);ids.splice(ids.indexOf(target)+(after?1:0),0,id)
 order.value=ids
 announcement.value=`${source.name} moved to position ${ids.indexOf(id)+1}`
}
function start(event:PointerEvent,id:string){
 if(props.disabled||floating.value||!event.isPrimary||event.button!==0)return
 event.preventDefault();event.stopPropagation()
 const box=element(id)!.getBoundingClientRect()
 position.value={x:box.left,y:box.top,width:box.width,height:box.height}
 offset={x:event.clientX-box.left,y:event.clientY-box.top}
 slots=[...list.value!.querySelectorAll<HTMLElement>('[data-sort-wish]')].map(layoutBox)
 scrollOrigin={x:window.scrollX,y:window.scrollY};last={x:event.clientX,y:event.clientY}
 initial=[...order.value];dragging.value=id;floating.value=id;pointer=event.pointerId
 list.value!.setPointerCapture(event.pointerId)
}
function drag(event:PointerEvent){
 if(event.pointerId!==pointer||!dragging.value)return
 event.preventDefault();event.stopPropagation()
 position.value={...position.value,x:event.clientX-offset.x,y:event.clientY-offset.y}
 // Slot geometry stays fixed through neighbor animations, preventing swaps back
 // into the slot just vacated while the pointer continues in the same direction.
 const dx=event.clientX-last.x,dy=event.clientY-last.y
 last={x:event.clientX,y:event.clientY}
 const from=items.value.findIndex(row=>row.id===dragging.value)
 let target=from,best=0
 slots.forEach((slot,index)=>{
  const current=slots[from]!
  if(index===from||(slot.left-current.left)*dx+(slot.top-current.top)*dy<=0)return
  const left=slot.left-(window.scrollX-scrollOrigin.x),top=slot.top-(window.scrollY-scrollOrigin.y)
  const width=Math.min(position.value.x+position.value.width,left+slot.width)-Math.max(position.value.x,left)
  const height=Math.min(position.value.y+position.value.height,top+slot.height)-Math.max(position.value.y,top)
  const overlap=Math.max(0,width)*Math.max(0,height)
  if(overlap>best){best=overlap;target=index}
 })
 if(target!==from)move(dragging.value,items.value[target]!.id,target>from)
 if(event.clientY>window.innerHeight-90)window.scrollBy(0,16)
 else if(event.clientY<90)window.scrollBy(0,-16)
}
async function finish(event:PointerEvent,cancel=false){
 if(event.pointerId!==pointer)return
 event.preventDefault();event.stopPropagation()
 suppressClickUntil=performance.now()+700
 const id=dragging.value,captured=pointer
 pointer=undefined;dragging.value=''
 if(list.value?.hasPointerCapture(captured))list.value.releasePointerCapture(captured)
 if(cancel)order.value=initial
 await nextTick()
 const node=element(id),box=node?layoutBox(node):undefined
 if(!box){floating.value='';return}
 settling.value=true
 position.value={x:box.left,y:box.top,width:box.width,height:box.height}
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches
 dropTimer=setTimeout(()=>{floating.value='';settling.value=false;dropTimer=undefined},reduced?0:200)
 if(!cancel&&order.value.some((value,index)=>value!==initial[index]))save()
}
function save(){emit('reorder',items.value.map(row=>row.id))}
function keyboard(event:KeyboardEvent,id:string){
 if(props.disabled||floating.value||!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(event.key))return
 event.preventDefault();event.stopPropagation()
 const own=items.value,forward=['ArrowDown','ArrowRight'].includes(event.key)
 const target=own[own.findIndex(row=>row.id===id)+(forward?1:-1)]
 if(target){move(id,target.id,forward);save()}
}
onMounted(()=>{document.addEventListener('click',guardClick,true);document.addEventListener('pointerdown',clearClickGuard,true)})
onBeforeUnmount(()=>{clearTimeout(dropTimer);document.removeEventListener('click',guardClick,true);document.removeEventListener('pointerdown',clearClickGuard,true)})
</script>
<template>
 <div ref="list" @pointermove="drag" @pointerup="finish($event)" @pointercancel="finish($event,true)" @lostpointercapture.self="finish($event,true)">
 <TransitionGroup tag="div" name="wish-order" class="cards-grid">
  <div v-for="wish in items" :key="wish.id" :data-sort-wish="wish.id" :data-wish-owner="wish.owner_id" class="sortable-wish" :class="{dragging:dragging===wish.id,floating:floating===wish.id}" :style="floating===wish.id?{height:position.height+'px'}:undefined">
   <Teleport to="body" :disabled="floating!==wish.id">
    <div class="wish-drag-surface" :class="{'wish-floating':floating===wish.id,'wish-settling':floating===wish.id&&settling}" :style="floating===wish.id?floatStyle:undefined">
     <slot :wish="wish" :reorder-disabled="disabled||!!floating" :start-reorder="start" :move-with-keyboard="keyboard" />
    </div>
   </Teleport>
  </div>
 </TransitionGroup>
 </div>
 <span class="sr-only" aria-live="polite">{{announcement}}</span>
</template>
<style scoped>
.sortable-wish{position:relative;min-width:0}
.wish-drag-surface{position:relative;display:grid;min-width:0;height:100%;border-radius:var(--radius,12px)}
.wish-drag-surface :deep(.plan-card-top){padding-right:36px}
.wish-order-move{transition:transform 200ms cubic-bezier(.2,.8,.2,1)}
.sortable-wish.floating::before{content:'';position:absolute;inset:0;border:2px dashed var(--rose);border-radius:var(--radius,12px);background:var(--blush);opacity:.5}
.wish-floating{position:fixed;left:0;top:0;z-index:2000;pointer-events:none;user-select:none;box-shadow:0 12px 32px #63334330;will-change:transform;transition:none}
.wish-settling{transition:transform 180ms cubic-bezier(.2,.8,.2,1)}
.wish-drag-surface :deep(.wish-drag-handle){position:absolute;right:14px;top:18px;min-width:44px;min-height:44px;touch-action:none;user-select:none;cursor:grab;border:0;background:transparent;color:var(--muted);font-size:26px}
.wish-drag-surface :deep(.wish-drag-handle:active){cursor:grabbing}
@media(prefers-reduced-motion:reduce){.wish-order-move,.wish-settling{transition:none}}
</style>
