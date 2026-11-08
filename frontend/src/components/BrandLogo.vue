<script setup lang="ts">
import { useId } from 'vue'
import horizontalLogo from '../assets/pigpen-horizontal.png'

const id = useId()
</script>

<template>
 <svg class="brand-logo" viewBox="230 135 1820 450" aria-hidden="true" focusable="false">
  <defs>
   <clipPath :id="`${id}-pig`"><rect x="220" y="130" width="650" height="460" /></clipPath>
   <clipPath :id="`${id}-name`"><rect x="875" y="190" width="1170" height="380" /></clipPath>
   <filter :id="`${id}-rose`" color-interpolation-filters="sRGB">
    <!-- Separate the darker lettering from its pale paper background. -->
    <feColorMatrix result="ink" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 -2.5 0 0 2.3" />
    <feFlood flood-color="currentColor" />
    <feComposite in2="ink" operator="in" />
   </filter>
  </defs>
  <image class="brand-pig" :href="horizontalLogo" width="2172" height="724" :clip-path="`url(#${id}-pig)`" />
  <image :href="horizontalLogo" width="2172" height="724" :clip-path="`url(#${id}-name)`" :filter="`url(#${id}-rose)`" />
 </svg>
</template>
