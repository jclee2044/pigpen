<script setup lang="ts">
import { ref } from 'vue'
import type { Category } from '../api/models'
const props=defineProps<{rows:Category[];disabled:boolean}>()
const emit=defineEmits<{reorder:[ids:string[]];preview:[ids:string[]]}>()
const dragging=ref(''),announcement=ref('')
let pointer:number|undefined,initial:string[]=[]
function move(id:string,target:string){
 const ids=props.rows.map(row=>row.id),from=ids.indexOf(id),to=ids.indexOf(target)
 if(from<0||to<0||from===to)return
 // Personal stays below shared categories, including during drag previews.
 if((props.rows[from]?.kind==='personal')!==(props.rows[to]?.kind==='personal'))return
 ids.splice(from,1);ids.splice(to,0,id)
 emit('preview',ids)
 announcement.value=`${props.rows.find(row=>row.id===id)?.name} moved to position ${to+1}`
 return ids
}
function start(event:PointerEvent,id:string){
 if(props.disabled||event.button!==0)return
 initial=props.rows.map(row=>row.id);dragging.value=id;pointer=event.pointerId
 ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}
function drag(event:PointerEvent){
 if(event.pointerId!==pointer||!dragging.value)return
 event.preventDefault()
 const target=document.elementFromPoint(event.clientX,event.clientY)?.closest<HTMLElement>('[data-sort-category]')?.dataset.sortCategory
 if(target)move(dragging.value,target)
 const list=(event.currentTarget as HTMLElement).closest('.category-order-list')
 const dialog=list?.closest('dialog')
 if(dialog){const box=dialog.getBoundingClientRect();if(event.clientY>box.bottom-55)dialog.scrollTop+=14;else if(event.clientY<box.top+55)dialog.scrollTop-=14}
}
function finish(event:PointerEvent,cancel=false){
 if(event.pointerId!==pointer)return
 pointer=undefined;dragging.value=''
 if(cancel){emit('preview',initial);return}
 const ids=props.rows.map(row=>row.id)
 if(ids.some((id,index)=>id!==initial[index]))emit('reorder',ids)
}
function keyboard(event:KeyboardEvent,id:string){
 if(props.disabled||!['ArrowUp','ArrowDown'].includes(event.key))return
 event.preventDefault()
 const index=props.rows.findIndex(row=>row.id===id)+(event.key==='ArrowUp'?-1:1)
 const target=props.rows[index]
 if(target){const ids=move(id,target.id);if(ids)emit('reorder',ids)}
}
</script>
<template><div class="category-order-list"><div v-for="category in rows" :key="category.id" :data-sort-category="category.id" class="sortable-category" :class="{dragging:dragging===category.id}"><slot :category="category" /><button type="button" class="category-drag-handle" :disabled="disabled" :aria-label="'Reorder '+category.name" title="Drag to reorder; use arrow keys to move" @pointerdown="start($event,category.id)" @pointermove="drag" @pointerup="finish($event)" @pointercancel="finish($event,true)" @keydown="keyboard($event,category.id)">⠿</button></div><span class="sr-only" aria-live="polite">{{announcement}}</span></div></template>
<style scoped>
.category-order-list{display:grid;gap:8px}.sortable-category{display:grid;grid-template-columns:minmax(0,1fr) 28px;align-items:center;gap:4px;border-radius:10px}.sortable-category.dragging{background:var(--blush);box-shadow:0 0 0 2px var(--rose)}.category-drag-handle{touch-action:none;user-select:none;cursor:grab;min-height:44px;width:28px;border:0;background:transparent;color:var(--muted);font-size:24px;padding:0}.category-drag-handle:active{cursor:grabbing}
</style>
