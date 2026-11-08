<script setup lang="ts">
import pigThinking from '../../../assets/states/pig-thinking.svg?url'
withDefaults(defineProps<{compact?:boolean;active?:boolean}>(),{compact:false,active:true})
</script>
<template>
 <div class="app-loading" :class="{compact,thinking:active}" role="status" aria-live="polite">
  <img :src="pigThinking" alt="" width="240" height="200" />
  <span>Loading...</span>
 </div>
</template>
<style scoped>
.app-loading{display:grid;justify-items:center;gap:12px;padding:24px 0;text-align:center;color:var(--ink)}
.app-loading img{display:block;width:220px;max-width:100%;height:auto;transform-origin:50% 90%}
.app-loading span{font-size:18px;font-weight:700}
.app-loading.compact{display:flex;align-items:center;justify-content:center;gap:8px;padding:0;text-align:left}
.compact img{width:56px;flex:none}.compact span{font-size:13px;font-weight:400}
.thinking img{animation:pig-think 2s ease-in-out infinite}
@keyframes pig-think{0%,100%{transform:rotate(-2deg)}50%{transform:rotate(2deg) translateY(-2px)}}
@media(prefers-reduced-motion:reduce){.thinking img{animation:none}}
</style>
