<script setup lang="ts">
import { useId } from 'vue'
const screenId=useId()
import pig from '../../../assets/avatars/pig-v1/base/pig.svg?url'
</script>

<template>
  <div class="purchase-empty">
    <svg class="purchase-empty-mascot" viewBox="0 0 240 174" role="img" aria-label="Pig peeking over an empty screen">
      <defs>
        <clipPath :id="screenId"><rect width="240" height="119" /></clipPath>
      </defs>
      <ellipse cx="120" cy="163" rx="101" ry="7" fill="#ecdedb" opacity=".5" />
      <g :clip-path="`url(#${screenId})`">
        <image :href="pig" x="20" y="-8" width="200" height="200" transform="rotate(-6 120 100)" />
      </g>
      <rect x="31" y="113" width="178" height="45" rx="10" fill="#fff8f7" stroke="#b78391" stroke-width="2" />
      <path d="M103 134h34m-25 9h16" fill="none" stroke="#ecdedb" stroke-width="4" stroke-linecap="round" />
      <path d="M78 113c-2-9 15-11 17-2l1 9c-3 5-14 5-17 0zm67-2c2-9 19-7 17 2l-1 7c-3 5-14 5-17 0z" fill="#f7a9b8" stroke="#71363c" stroke-width="2.5" stroke-linejoin="round" />
      <path d="m87 115 1 6m65-6-1 6" stroke="#71363c" stroke-width="2" stroke-linecap="round" />
    </svg>
    <p>Nothing here yet</p>
  </div>
</template>

<style scoped>
.purchase-empty{display:grid;justify-items:center;padding:18px 0 24px;text-align:center}
.purchase-empty-mascot{display:block;width:220px;max-width:100%;height:auto}
.purchase-empty p{margin:14px 0 0;font-size:18px;font-weight:700;color:var(--ink)}
</style>
