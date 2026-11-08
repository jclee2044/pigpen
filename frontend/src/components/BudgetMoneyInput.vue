<script setup lang="ts">
import { ref,watch,onMounted,onBeforeUnmount,nextTick } from 'vue'
const model=defineModel<string>({required:true})
const focused=ref(false)
const format=(value:string)=>value.replace(/\B(?=(\d{3})+(?!\d))/g,',')
const display=ref(format(model.value))
watch(model,value=>{if(!focused.value)display.value=format(value)})
const element=ref<HTMLInputElement>()
let observer:ResizeObserver|undefined
function fit(){
 const input=element.value
 if(!input)return
 input.style.fontSize='16px'
 const style=getComputedStyle(input)
 const canvas=document.createElement('canvas').getContext('2d')!
 canvas.font=style.font
 const width=canvas.measureText(input.value).width
 const available=input.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight)
 if(width>available)input.style.fontSize=`${16*available/width}px`
}
watch(display,async()=>{await nextTick();fit()})
onMounted(()=>{observer=new ResizeObserver(fit);observer.observe(element.value!);fit()})
onBeforeUnmount(()=>observer?.disconnect())
function focus(event:FocusEvent){
 focused.value=true
 if(Number(model.value)===0)(event.target as HTMLInputElement).select()
}
function input(event:Event){
 const target=event.target as HTMLInputElement
 const start=target.selectionStart??target.value.length
 const clean=(value:string)=>{const [whole,...fraction]=value.replace(/[^0-9.]/g,'').split('.');return whole+(fraction.length?'.'+fraction.join('').slice(0,2):'')}
 const position=clean(target.value.slice(0,start)).length
 const cleaned=clean(target.value)
 model.value=cleaned
 display.value=cleaned
 target.value=cleaned
 target.setSelectionRange(position,position)
}
function blur(){
 focused.value=false
 const [whole='',fraction='']=model.value.split('.')
 const normalized=(whole.replace(/^0+(?=\d)/,'')||'0')+'.'+fraction.padEnd(2,'0')
 model.value=normalized
 display.value=format(normalized)
}
</script>
<template><input ref="element" :value="display" inputmode="decimal" required @focus="focus" @input="input" @blur="blur" @keydown="event=>{if(event.key.length===1&&!event.ctrlKey&&!event.metaKey&&!/^[0-9.]$/.test(event.key))event.preventDefault()}" /></template>
