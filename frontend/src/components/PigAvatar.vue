<script setup lang="ts">
import { computed } from 'vue'
import type { Avatar } from '../api/generated'
const props = withDefaults(defineProps<{ avatar?: Avatar; size?: number; label?: string }>(),{size:44,label:'Pig avatar'})
const files = import.meta.glob('../../../assets/avatars/pig-v1/**/*.svg',{eager:true,query:'?url',import:'default'}) as Record<string,string>
const defaults = {background:'cream',bandana:'grass',glasses:'none',hat:'none',eyelashes:'none'}
const layers = computed(()=>{
 const value={...defaults,...props.avatar}
 return ['background/'+value.background,'base/pig','bandana/'+value.bandana,'eyelashes/'+value.eyelashes,'glasses/'+value.glasses,'hat/'+value.hat].filter(x=>!x.endsWith('/none')).map(x=>files['../../../assets/avatars/pig-v1/'+x+'.svg']).filter(Boolean)
})
</script>
<template><span class="pig-avatar" role="img" :aria-label="label" :style="{width:size+'px',height:size+'px'}"><img v-for="(src,i) in layers" :key="i" :src="src" alt="" /></span></template>
<style scoped>.pig-avatar{position:relative;display:inline-block;flex-shrink:0;border-radius:50%;overflow:hidden;background:var(--blush)}img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}</style>
