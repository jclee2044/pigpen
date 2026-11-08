<script setup lang="ts">
import { onMounted,onBeforeUnmount,ref,watch,nextTick } from 'vue'
import { money } from '../lib/money'
const props=defineProps<{amount:number}>()
const box=ref<HTMLElement>(),text=ref<HTMLElement>()
let observer:ResizeObserver|undefined
function fit(){
 if(!box.value||!text.value)return
 text.value.style.fontSize=''
 const size=parseFloat(getComputedStyle(text.value).fontSize)
 const width=text.value.getBoundingClientRect().width
 if(width>box.value.clientWidth)text.value.style.fontSize=`${size*box.value.clientWidth/width}px`
}
onMounted(()=>{observer=new ResizeObserver(fit);observer.observe(box.value!);fit();document.fonts.ready.then(fit)})
watch(()=>props.amount,async()=>{await nextTick();fit()})
onBeforeUnmount(()=>observer?.disconnect())
</script>
<template><strong ref="box" class="fit-money"><span ref="text">{{money(amount)}}</span></strong></template>
<style scoped>
.fit-money{display:block;min-width:0;white-space:nowrap;overflow-wrap:normal}
.fit-money>span{display:inline-block;white-space:nowrap}
</style>
