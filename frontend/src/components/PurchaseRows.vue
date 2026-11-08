<script setup lang="ts">
import { ref } from 'vue'
import type { Purchase } from '../api/models'
import { rows } from '../state/household'
import { money } from '../lib/money'
import PigAvatar from './PigAvatar.vue'
import PurchaseEmptyState from './PurchaseEmptyState.vue'
const props=defineProps<{purchases:Purchase[];swipeToDelete?:boolean}>()
const emit=defineEmits<{select:[Purchase];delete:[Purchase]}>()
const category=(id:string)=>rows('categories').find(c=>c.id===id)
const person=(id:string)=>rows('users').find(u=>u.id===id)
const openId=ref(''),dragId=ref(''),offset=ref(0)
let gesture:{id:string;x:number;y:number;start:number;horizontal:boolean}|undefined
let suppressClick=false
let deleteTouch:{x:number;y:number}|undefined
function startDelete(event:TouchEvent){const touch=event.touches.length===1?event.touches[0]:undefined;deleteTouch=touch?{x:touch.clientX,y:touch.clientY}:undefined}
function tapDelete(event:TouchEvent,purchase:Purchase){
 const touch=event.changedTouches[0]
 if(deleteTouch&&touch&&Math.hypot(touch.clientX-deleteTouch.x,touch.clientY-deleteTouch.y)<10)remove(purchase)
 deleteTouch=undefined
}
function start(event:PointerEvent,id:string){
 if(!props.swipeToDelete||!event.isPrimary||event.button!==0)return
 suppressClick=false
 const start=openId.value===id?-88:0
 openId.value='';dragId.value=id;offset.value=start
 gesture={id,x:event.clientX,y:event.clientY,start,horizontal:false}
 ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}
function move(event:PointerEvent){
 if(!gesture)return
 const dx=event.clientX-gesture.x,dy=event.clientY-gesture.y
 if(!gesture.horizontal){
  if(Math.abs(dy)>8&&Math.abs(dy)>Math.abs(dx)){cancel();return}
  if(Math.abs(dx)<8)return
  gesture.horizontal=true
 }
 suppressClick=true
 offset.value=Math.max(-88,Math.min(0,gesture.start+dx))
}
function end(){
 if(!gesture)return
 openId.value=offset.value< -44?gesture.id:''
 gesture=undefined;dragId.value=''
}
function cancel(){gesture=undefined;dragId.value=''}
function select(purchase:Purchase){
 if(suppressClick){suppressClick=false;return}
 if(openId.value===purchase.id){openId.value='';return}
 openId.value='';emit('select',purchase)
}
function remove(purchase:Purchase){openId.value='';emit('delete',purchase)}
</script>
<template>
 <PurchaseEmptyState v-if="!purchases.length" />
 <div v-for="p in purchases" :key="p.id" class="purchase-row" :class="{revealed:openId===p.id,swipeable:swipeToDelete}">
  <button v-if="swipeToDelete" type="button" class="swipe-delete" :tabindex="openId===p.id?0:-1" :aria-hidden="openId!==p.id" :aria-label="'Delete '+p.item" @touchstart.passive="startDelete" @touchend.prevent="tapDelete($event,p)" @touchcancel="deleteTouch=undefined" @click="remove(p)">Delete</button>
  <button type="button" class="row purchase-card" :class="{swipeable:swipeToDelete,dragging:dragId===p.id}" :aria-label="p.item" :style="{transform:`translateX(${dragId===p.id?offset:openId===p.id?-88:0}px)`}" @pointerdown="start($event,p.id)" @pointermove="move" @pointerup="end" @pointercancel="cancel" @lostpointercapture="cancel" @click="select(p)" @keydown.delete.prevent="swipeToDelete&&remove(p)" @keydown.esc="openId=''">
   <PigAvatar :avatar="person(p.purchaser_id)?.avatar" :size="40" :label="(person(p.purchaser_id)?.name??'Archived profile')+' avatar'" />
   <span class="row-main"><span class="purchase-title">{{p.item}}</span><span class="purchase-meta">{{person(p.purchaser_id)?.name??'Archived profile'}} · {{p.transaction_date}}</span></span>
   <span class="row-end"><strong>{{money(p.amount_minor)}}</strong><small>{{category(p.category_id)?.name}}</small></span>
  </button>
 </div>
</template>
<style scoped>
.purchase-row{position:relative;overflow:hidden;border-bottom:1px solid var(--line);border-radius:10px}
.purchase-row:last-child{border-bottom:0}
.purchase-card{position:relative;width:100%;border:0;margin:0;padding:16px 0;background:var(--paper);color:var(--ink);text-align:left;transition:transform .18s ease;min-height:82px}
.purchase-row.swipeable{touch-action:pan-y pinch-zoom}
.purchase-card.dragging{transition:none}
.purchase-card:focus-visible{outline-offset:-3px}
.purchase-title{display:block;color:var(--rose);font-size:13px;font-weight:700;padding:8px 0;overflow-wrap:anywhere}
.purchase-meta{display:block;color:var(--muted);font-size:12px;line-height:1.6}
.swipe-delete{position:absolute;inset:0 0 0 auto;width:88px;border:0;border-radius:10px;background:#9e3434;color:white;font-weight:700;visibility:hidden}
.purchase-row.revealed .swipe-delete,.purchase-row:has(.dragging) .swipe-delete{visibility:visible}
@media(prefers-reduced-motion:reduce){.purchase-card{transition:none}}
</style>
