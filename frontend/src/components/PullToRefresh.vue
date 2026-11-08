<script setup lang="ts">
import { ref,onMounted,onUnmounted } from 'vue'
const props=defineProps<{refresh:()=>Promise<void>;disabled?:boolean}>()
const emit=defineEmits<{error:[error:unknown]}>()
const host=ref<HTMLElement>()
const distance=ref(0),refreshing=ref(false),dragging=ref(false)
const threshold=56
let origin:{x:number;y:number;offset:number}|undefined
let travel=0,frame=0,suppressClickUntil=0
let mounted=true
function paint(value:number){
 travel=value
 if(!frame)frame=requestAnimationFrame(()=>{distance.value=travel;frame=0})
}
function settle(value=0){cancelAnimationFrame(frame);frame=0;travel=value;distance.value=value}
function cancel(){origin=undefined;dragging.value=false;if(!refreshing.value)settle()}
function start(event:TouchEvent){
 if(refreshing.value)return
 const surface=host.value?.querySelector('.refresh-content')
 const offset=surface?Math.max(0,new DOMMatrixReadOnly(getComputedStyle(surface).transform).m42):0
 cancel()
 if(props.disabled||event.touches.length!==1||window.scrollY>4||document.querySelector('dialog[open]'))return
 const target=event.target
 if(target instanceof Element&&target.closest('input,select,textarea,[contenteditable],[data-touch-interactive],.mobile-nav,[role="dialog"]'))return
 for(let node=target instanceof Element?target:null;node&&node!==document.body;node=node.parentElement){
  if(node.scrollHeight>node.clientHeight&&/auto|scroll/.test(getComputedStyle(node).overflowY))return
 }
 const touch=event.touches[0]!
 origin={x:touch.clientX,y:touch.clientY,offset}
}
function move(event:TouchEvent){
 if(!origin)return
 if(event.touches.length!==1||props.disabled){cancel();return}
 const touch=event.touches[0]!
 const dy=touch.clientY-origin.y,dx=touch.clientX-origin.x
 if(!dragging.value){
  if(window.scrollY>4||dy< -4||(Math.abs(dx)>6&&Math.abs(dx)>Math.abs(dy))){cancel();return}
  if(dy<=0||dy<Math.abs(dx))return
 }
 // Claim the first downward move, before Safari starts its own rubber-band scroll.
 if(!event.cancelable){cancel();return}
 event.preventDefault()
 dragging.value=true
 // Continuous resistance avoids a hard stop at the maximum pull distance.
 paint(origin.offset+(110-origin.offset)*(1-Math.exp(-Math.max(0,dy)/150)))
}
async function end(){
 if(refreshing.value)return
 if(props.disabled){cancel();return}
 const ready=dragging.value&&travel>=threshold
 if(dragging.value&&travel>5)suppressClickUntil=performance.now()+350
 origin=undefined;dragging.value=false
 if(!ready){settle();return}
 refreshing.value=true;settle(threshold)
 try{await Promise.all([props.refresh(),new Promise(resolve=>setTimeout(resolve,650))])}
 catch(error){emit('error',error)}
 finally{if(mounted){refreshing.value=false;settle()}}
}
function click(event:MouseEvent){
 if(event.detail>0&&performance.now()<suppressClickUntil){event.preventDefault();event.stopImmediatePropagation()}
}
onMounted(()=>{
 document.addEventListener('touchstart',start,{passive:false,capture:true})
 document.addEventListener('touchmove',move,{passive:false,capture:true})
 document.addEventListener('touchend',end,true)
 document.addEventListener('touchcancel',cancel,true)
 document.addEventListener('click',click,true)
})
onUnmounted(()=>{
 mounted=false;cancelAnimationFrame(frame)
 document.removeEventListener('touchstart',start,true)
 document.removeEventListener('touchmove',move,true)
 document.removeEventListener('touchend',end,true)
 document.removeEventListener('touchcancel',cancel,true)
 document.removeEventListener('click',click,true)
})
</script>
<template>
 <div ref="host" class="refresh-host" :class="{refreshing,dragging}" :style="{'--pull-distance':distance+'px'}">
  <div class="pull-refresh" :class="{refreshing,active:distance>0}" role="status" aria-live="polite">
   <span class="refresh-wheel" aria-hidden="true" :style="{'--pull-turn':distance*3+'deg'}"><i v-for="n in 12" :key="n" :style="{'--spoke':n}" /></span>
   <span class="sr-only">{{refreshing?'Syncing…':distance>=threshold?'Release to sync':distance>0?'Pull to sync':''}}</span>
  </div>
  <slot name="header" />
  <div class="refresh-content"><slot /></div>
 </div>
</template>
