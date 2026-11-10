<script setup lang="ts">
import { computed,onMounted,onUnmounted,ref } from 'vue'
import AppIcon from './AppIcon.vue'
import {inspectReceipt,SteadyReceipt} from '../lib/receiptCapture'

const emit=defineEmits<{close:[];photo:[file:File]}>()
const dialog=ref<HTMLDialogElement>(),video=ref<HTMLVideoElement>(),library=ref<HTMLInputElement>()
const zoom=ref(1)
const stage=ref<HTMLElement>(),stageWidth=ref(0),stageHeight=ref(0),aspect=3/4
let observer:ResizeObserver|undefined
let monitor:ReturnType<typeof setInterval>|undefined,picking=false
const steady=new SteadyReceipt(),autoStatus=ref('Fit receipt inside the frame')
const preview=document.createElement('canvas');preview.width=240;preview.height=320
function monitorReceipt(){
 if(!ready.value||!video.value||capturing.value||picking||document.hidden||points.size){steady.reset();return}
 try{
  const ctx=preview.getContext('2d',{willReadFrequently:true});if(!ctx)return
  const v=video.value,w=Math.min(v.videoWidth,v.videoHeight*aspect)/zoom.value,h=w/aspect
  ctx.drawImage(v,(v.videoWidth-w)/2,(v.videoHeight-h)/2,w,h,0,0,240,320)
  const frame=inspectReceipt(ctx.getImageData(0,0,240,320).data,240,320)
  autoStatus.value=!frame?'Fit receipt inside the frame':!frame.sharp?'Hold still for a clear photo':'Hold steady'
  if(steady.update(frame,performance.now())){steady.reset();void capture()}
 }catch{steady.reset()}
}
function openLibrary(){picking=true;steady.reset();library.value?.click()}
const frameStyle=computed(()=>{
 const width=Math.min(stageWidth.value,stageHeight.value*aspect)
 return {width:width+'px',height:width/aspect+'px'}
})
function loaded(){if(video.value?.videoWidth){ready.value=true}}
const points=new Map<number,{x:number;y:number}>()
function setZoom(value:number){steady.reset();zoom.value=Math.max(1,Math.min(4,value))}
function pointerDown(e:PointerEvent){
 if(e.pointerType==='mouse'&&e.button!==0)return
 ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
 points.set(e.pointerId,{x:e.clientX,y:e.clientY})
}
function pointerMove(e:PointerEvent){
 if(!points.has(e.pointerId))return
 const before=[...points.values()]
 points.set(e.pointerId,{x:e.clientX,y:e.clientY})
 const after=[...points.values()]
 if(before.length===2&&after.length===2){
  const oldDistance=Math.hypot(before[0]!.x-before[1]!.x,before[0]!.y-before[1]!.y)
  if(oldDistance>0)setZoom(zoom.value*Math.hypot(after[0]!.x-after[1]!.x,after[0]!.y-after[1]!.y)/oldDistance)
 }
}
function pointerUp(e:PointerEvent){points.delete(e.pointerId)}
function preventGesture(e:Event){e.preventDefault()}
const error=ref(''),ready=ref(false),capturing=ref(false)
let stream:MediaStream|undefined,disposed=false,generation=0
function stop(){
 generation++;points.clear();steady.reset()
 stream?.getTracks().forEach(track=>track.stop())
 stream=undefined;ready.value=false
 if(video.value)video.value.srcObject=null
}
async function start(){
 stop();error.value=''
 const attempt=generation
 try{
  if(!navigator.mediaDevices?.getUserMedia)throw new Error('unavailable')
  const constraints:MediaTrackConstraints & {resizeMode:string}={facingMode:{ideal:'environment'},width:{ideal:1920},height:{ideal:1920},resizeMode:'none'}
  const camera=await navigator.mediaDevices.getUserMedia({audio:false,video:constraints})
  if(disposed||attempt!==generation){camera.getTracks().forEach(track=>track.stop());return}
  stream=camera
  if(video.value){video.value.srcObject=camera;await video.value.play()}
 }catch{
  if(disposed||attempt!==generation)return
  stop();error.value='Camera unavailable. Allow camera access or choose a photo.'
 }
}
function pickerCanceled(){picking=false;steady.reset();if(!stream&&!document.hidden)void start()}
function cancelDialog(event:Event){if(event.target===dialog.value)emit('close')}
function select(event:Event){
 picking=false;steady.reset()
 const input=event.target as HTMLInputElement
 const photo=input.files?.[0]
 if(photo){stop();emit('photo',photo)}
 input.value=''
}
async function capture(){
 if(!ready.value||!video.value||capturing.value)return
 capturing.value=true
 try{
  const canvas=document.createElement('canvas')
  const sourceWidth=video.value.videoWidth,sourceHeight=video.value.videoHeight
  const cropWidth=Math.min(sourceWidth,sourceHeight*aspect)/zoom.value,cropHeight=cropWidth/aspect
  canvas.width=Math.round(cropWidth);canvas.height=Math.round(cropHeight)
  const ctx=canvas.getContext('2d')
  if(!ctx)throw new Error('capture')
  ctx.drawImage(video.value,(sourceWidth-cropWidth)/2,(sourceHeight-cropHeight)/2,cropWidth,cropHeight,0,0,canvas.width,canvas.height)
  const blob=await new Promise<Blob|null>(resolve=>canvas.toBlob(resolve,'image/jpeg',0.92))
  if(!blob)throw new Error('capture')
  if(!disposed){stop();emit('photo',new File([blob],'receipt.jpg',{type:'image/jpeg'}))}
 }catch{error.value='Could not take the photo. Try again or choose an existing photo.'}
 finally{capturing.value=false}
}
function visibility(){if(document.hidden)stop();else if(!disposed)void start()}
onMounted(()=>{dialog.value?.addEventListener('gesturestart',preventGesture,{passive:false});dialog.value?.addEventListener('gesturechange',preventGesture,{passive:false});dialog.value?.showModal();observer=new ResizeObserver(()=>{stageWidth.value=stage.value?.clientWidth??0;stageHeight.value=stage.value?.clientHeight??0});if(stage.value)observer.observe(stage.value);void start();monitor=setInterval(monitorReceipt,250);document.addEventListener('visibilitychange',visibility)})
onUnmounted(()=>{disposed=true;clearInterval(monitor);stop();observer?.disconnect();document.removeEventListener('visibilitychange',visibility)})
</script>

<template>
 <Teleport to="body">
  <dialog ref="dialog" class="receipt-camera" aria-label="Scan receipt" @cancel.prevent="cancelDialog">
   <div ref="stage" class="camera-viewfinder" data-touch-interactive @pointerdown="pointerDown" @pointermove="pointerMove" @pointerup="pointerUp" @pointercancel="pointerUp" @lostpointercapture="pointerUp" @wheel.prevent="e=>setZoom(zoom*Math.exp(-e.deltaY*.002))">
    <div class="camera-frame" :style="frameStyle"><video ref="video" autoplay muted playsinline aria-label="Receipt camera preview" :style="{transform:'scale('+zoom+')'}" @loadeddata="loaded" @resize="loaded" /></div>
    <p v-if="ready" class="auto-capture-status" role="status">{{autoStatus}}</p>
   </div>
   <div class="camera-heading"><h2>Scan receipt</h2><button type="button" class="camera-button" aria-label="Close dialog" @click="emit('close')"><AppIcon name="close" /></button></div>
   <div v-if="error" class="camera-error" role="alert"><p>{{error}}</p><button type="button" class="button" @click="start">Try camera again</button></div>
   <div class="camera-zoom" aria-label="Camera zoom">
    <button v-for="level in [1,2,3]" :key="level" type="button" :aria-label="'Camera zoom '+level+'x'" :aria-pressed="Math.abs(zoom-level)<.05" @click="setZoom(level)">{{level}}×</button>
    <label class="sr-only" for="camera-zoom-range">Camera zoom</label><input id="camera-zoom-range" type="range" min="1" max="4" step=".1" :value="zoom" @input="e=>setZoom(Number((e.target as HTMLInputElement).value))" />
    <output>{{zoom.toFixed(1)}}×</output>
   </div>
   <div class="camera-controls">
    <button type="button" class="camera-button library-button" aria-label="Choose existing photo" @click="openLibrary"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="3" /><circle cx="8" cy="8" r="2" /><path d="m3 18 6-6 4 4 3-4 5 6" /></svg></button>
    <button type="button" class="shutter" aria-label="Take receipt photo" :disabled="!ready||capturing" @click="capture"><span /></button>
   </div>
   <input ref="library" hidden type="file" aria-label="Or choose an image" accept="image/jpeg,image/png,image/webp" @change="select" @cancel.stop="pickerCanceled" />
  </dialog>
 </Teleport>
</template>

<style scoped>
.receipt-camera{position:fixed;inset:0;width:100%;height:100%;height:100dvh;max-width:none;max-height:none;margin:0;padding:0;border:0;border-radius:0;background:var(--page);color:var(--ink);overflow:hidden;touch-action:none;overscroll-behavior:none}
.receipt-camera[open]{display:grid;grid-template-rows:auto minmax(0,1fr) auto auto}
.receipt-camera input[hidden]{display:none}
.camera-frame{overflow:hidden;flex:none}
.receipt-camera video{width:100%;height:100%;object-fit:cover;pointer-events:none}
.auto-capture-status{position:absolute;bottom:8px;left:50%;transform:translateX(-50%);width:max-content;max-width:calc(100% - 24px);margin:0;padding:8px 12px;border-radius:16px;background:var(--paper);color:var(--ink);font-size:12px;text-align:center;pointer-events:none}
.camera-viewfinder{position:relative;grid-row:2;min-height:0;display:flex;align-items:center;justify-content:center;overflow:hidden;touch-action:none;user-select:none}
.camera-zoom{grid-row:3;justify-self:center;margin:10px 0;display:flex;align-items:center;gap:6px;padding:6px;border-radius:24px;background:var(--paper);max-width:calc(100% - 24px)}
.camera-zoom button{width:40px;height:40px;border:0;border-radius:50%;background:var(--page);color:var(--ink);flex:none;padding:0}
.camera-zoom button[aria-pressed=true]{background:var(--rose);color:white}
.camera-zoom input{width:70px;min-height:24px;padding:0;accent-color:var(--rose)}
.camera-zoom output{font-size:12px;min-width:30px;color:var(--ink)}
.camera-heading{grid-row:1;display:flex;align-items:center;justify-content:space-between;padding:calc(16px + env(safe-area-inset-top)) 20px 16px;background:var(--header-pink);border-bottom:1px solid var(--line)}
.camera-heading h2{margin:0;color:#3d3331}
.camera-button{display:grid;place-items:center;width:48px;height:48px;border:1px solid var(--line);border-radius:12px;color:var(--rose-dark);background:var(--paper);cursor:pointer}
.camera-button svg{width:26px;height:26px}
.camera-controls{grid-row:4;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));align-items:center;padding:24px 24px calc(24px + env(safe-area-inset-bottom));background:var(--page);border-top:1px solid var(--line)}
.library-button{justify-self:start}
.shutter{grid-column:2;justify-self:center;padding:0;display:grid;place-items:center;width:72px;height:72px;border:3px solid var(--rose);border-radius:50%;background:transparent;cursor:pointer}
.shutter span{width:58px;height:58px;background:var(--rose);border-radius:50%}
.shutter:disabled{opacity:.4}
.camera-error{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:min(360px,calc(100% - 40px));padding:16px;background:var(--paper);border:1px solid var(--line);border-radius:var(--radius)}
.camera-error .button{margin:4px}
</style>
