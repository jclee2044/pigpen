<script setup lang="ts">
import { ref,watch } from 'vue'
const props=defineProps<{id:string;name:string;enabled:boolean;open:boolean}>()
const emit=defineEmits<{reveal:[string];delete:[]}>()
const dragging=ref(false),offset=ref(0)
let gesture:{x:number;y:number;start:number;horizontal:boolean}|undefined
let suppressClick=false
let deleteTouch:{x:number;y:number}|undefined
watch(()=>props.enabled,enabled=>{if(!enabled){cancel();emit('reveal','')}})
function start(event:PointerEvent){
 if(!props.enabled||!event.isPrimary||event.button!==0)return
 suppressClick=false
 gesture={x:event.clientX,y:event.clientY,start:props.open?-88:0,horizontal:false}
 offset.value=gesture.start
}
function move(event:PointerEvent){
 if(!gesture)return
 const dx=event.clientX-gesture.x,dy=event.clientY-gesture.y
 if(!gesture.horizontal){
  if(Math.abs(dy)>8&&Math.abs(dy)>Math.abs(dx)){cancel();return}
  if(Math.abs(dx)<8)return
  gesture.horizontal=true;dragging.value=true;emit('reveal','')
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
 }
 suppressClick=true
 offset.value=Math.max(-88,Math.min(0,gesture.start+dx))
}
function end(){
 if(!gesture)return
 if(gesture.horizontal)emit('reveal',offset.value< -44?props.id:'')
 gesture=undefined;dragging.value=false
}
function cancel(){gesture=undefined;dragging.value=false}
function click(event:MouseEvent){
 if(suppressClick){event.preventDefault();event.stopPropagation();suppressClick=false;return}
 if(props.open){event.preventDefault();event.stopPropagation();emit('reveal','')}
}
function revealWithKeyboard(event:KeyboardEvent){
 if(props.enabled&&!(event.target as HTMLElement).closest('input,textarea,select,[contenteditable]')){event.preventDefault();emit('reveal',props.id)}
}
function remove(){emit('reveal','');emit('delete')}
function startDelete(event:TouchEvent){const touch=event.touches.length===1?event.touches[0]:undefined;deleteTouch=touch?{x:touch.clientX,y:touch.clientY}:undefined}
function tapDelete(event:TouchEvent){
 const touch=event.changedTouches[0]
 if(deleteTouch&&touch&&Math.hypot(touch.clientX-deleteTouch.x,touch.clientY-deleteTouch.y)<10)remove()
 deleteTouch=undefined
}
</script>
<template>
 <div class="wish-swipe" :class="{revealed:open,dragging,enabled}">
  <button v-if="enabled" type="button" class="wish-delete" :tabindex="open?0:-1" :aria-hidden="!open" :aria-label="'Delete '+name" @touchstart.passive="startDelete" @touchend.prevent="tapDelete" @touchcancel="deleteTouch=undefined" @click="remove">Delete</button>
  <div class="wish-surface" :style="{transform:`translateX(${dragging?offset:open?-88:0}px)`}" @pointerdown="start" @pointermove="move" @pointerup="end" @pointercancel="cancel" @lostpointercapture.self="cancel" @click.capture="click" @keydown.esc="emit('reveal','')" @keydown.left="revealWithKeyboard"><slot /></div>
 </div>
</template>
<style scoped>
.wish-swipe{--wish-radius:var(--radius);position:relative;display:grid;min-width:0;border-radius:var(--wish-radius);overflow:hidden}
.wish-swipe.enabled{touch-action:pan-y pinch-zoom}
.wish-surface{position:relative;display:grid;min-width:0;transition:transform .18s ease}
.wish-surface :deep(.plan-card){margin:0;box-sizing:border-box;border-radius:inherit}
.wish-surface{border-radius:inherit}
@media(max-width:760px){.wish-swipe{--wish-radius:17px}}
.dragging .wish-surface{transition:none;user-select:none}
.wish-delete{position:absolute;inset:0 0 0 auto;width:88px;border:0;border-radius:var(--radius);background:#9e3434;color:white;font-weight:700;visibility:hidden}
.revealed .wish-delete,.dragging .wish-delete{visibility:visible}
@media(prefers-reduced-motion:reduce){.wish-surface{transition:none}}
</style>
