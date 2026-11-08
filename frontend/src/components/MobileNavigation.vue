<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppIcon from './AppIcon.vue'

const links = [
 ['/', 'Home', 'home'],
 ['/budget', 'Budget', 'budget'],
 ['/purchases', 'Purchases', 'receipt'],
 ['/approvals', 'Approvals', 'shield'],
 ['/wish-lists', 'Wish Lists', 'heart'],
] as const
const route = useRoute()
const navigation = ref<HTMLElement>()
const highlight = ref<HTMLElement>()
let animation: Animation | undefined
let observer: ResizeObserver | undefined
let positioned = false

function positionHighlight(animate = false) {
 const container = navigation.value
 const pill = highlight.value
 if (!container || !pill) return
 const selected = container.querySelector<HTMLElement>('a.active')
 if (!selected || !container.getClientRects().length) {
  animation?.cancel()
  pill.hidden = true
  positioned = false
  return
 }
 const previous = pill.getBoundingClientRect()
 const bounds = container.getBoundingClientRect()
 const shouldAnimate = animate && positioned && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
 animation?.cancel()
 pill.hidden = false
 Object.assign(pill.style, {
  left: `${selected.offsetLeft}px`, top: `${selected.offsetTop}px`,
  width: `${selected.offsetWidth}px`, height: `${selected.offsetHeight}px`,
 })
 if (shouldAnimate) {
  // Start from the visible position, including an interrupted transition.
  const dx = previous.left - bounds.left - selected.offsetLeft
  animation = pill.animate([
   { transform: `translate3d(${dx}px, 0, 0)` },
   { transform: 'translate3d(0, 0, 0)' },
  ], { duration: 420, easing: 'cubic-bezier(.4, 0, .2, 1)' })
 }
 positioned = true
}

watch(() => route.path, async () => {
 await nextTick()
 positionHighlight(true)
})
onMounted(() => {
 positionHighlight()
 observer = new ResizeObserver(() => positionHighlight())
 if (navigation.value) observer.observe(navigation.value)
})
onUnmounted(() => {
 animation?.cancel()
 observer?.disconnect()
})
</script>

<template>
 <nav ref="navigation" class="mobile-nav" aria-label="Mobile navigation">
  <span ref="highlight" class="mobile-nav-highlight" aria-hidden="true" hidden />
  <RouterLink v-for="[path, label, icon] in links" :key="path" :to="path" exact-active-class="active">
   <AppIcon :name="icon" /><span>{{ label }}</span>
  </RouterLink>
 </nav>
</template>

<style scoped>
.mobile-nav-highlight {
 position: absolute;
 pointer-events: none;
 border-radius: 10px;
 background: var(--selected);
 /* Keep its compositing layer alive before, during and after the slide. */
 transform: translate3d(0, 0, 0);
 will-change: transform;
}
/* Permanent foreground layers prevent WebKit from promoting/rasterizing the
   labels when the animated background passes underneath them. */
.mobile-nav a {
 position: relative;
 z-index: 1;
 transform: translate3d(0, 0, 0);
 will-change: transform;
}
.mobile-nav a.active { background: transparent; }
@media (max-width: 760px) {
 .mobile-nav { grid-template-columns: repeat(5, minmax(0, 1fr)); }
 /* Reserve fixed icon/label tracks while retaining selected-only bold text. */
 .mobile-nav a,
 .mobile-nav a.active {
  min-width: 0;
  height: 52.8px;
  grid-template-rows: 25.2px 14.4px;
  line-height: 14.4px;
  font-weight: 400;
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
 }
 .mobile-nav a.active { font-weight: 700; }
 .mobile-nav a > span { width: 100%; text-align: center; white-space: nowrap; }
}
</style>
