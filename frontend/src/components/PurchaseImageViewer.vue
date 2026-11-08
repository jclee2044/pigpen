<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import AppIcon from './AppIcon.vue'
const props = defineProps<{ src: string; filename: string }>()
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLDialogElement>()
const stage = ref<HTMLDivElement>()
const scale = ref(1), x = ref(0), y = ref(0)
const width = ref(0), height = ref(0), naturalWidth = ref(0), naturalHeight = ref(0)
const failed = ref(false)
const pullX = ref(0), pullY = ref(0), settling = ref(false), dismissing = ref(false)
const shade = computed(() => Math.max(0, 1 - pullY.value / Math.max(1, height.value * .65)))
const transform = computed(() => `translate(${x.value + pullX.value}px, ${y.value + pullY.value}px) scale(${scale.value * (1 - Math.min(.15, pullY.value / Math.max(1, height.value) * .3))})`)
let canDismiss = false
let closeTimer: ReturnType<typeof setTimeout> | undefined
function restorePull() { settling.value = true; pullX.value = 0; pullY.value = 0 }
function dismissPull() {
  dismissing.value = true; settling.value = true
  pullY.value = height.value + 100
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) emit('close')
  else closeTimer = setTimeout(() => emit('close'), 180)
}
const points = new Map<number, { x: number; y: number }>()
let observer: ResizeObserver | undefined
let previousFocus: HTMLElement | null = null
let controlTouch: { x: number; y: number; button: HTMLButtonElement } | undefined
function controlStart(e: TouchEvent) {
  const button = (e.target as Element).closest('button')
  const touch = e.touches[0]
  controlTouch = e.touches.length === 1 && button && touch ? { x: touch.clientX, y: touch.clientY, button } : undefined
}
function controlEnd(e: TouchEvent) {
  const start = controlTouch, touch = e.changedTouches[0]
  controlTouch = undefined
  if (start && touch && !e.touches.length && Math.hypot(touch.clientX - start.x, touch.clientY - start.y) < 10) {
    e.preventDefault()
    start.button.click()
  }
}
let lastTap = { time: 0, x: 0, y: 0 }
let moved = false
let start = { x: 0, y: 0 }
function clamp() {
  const fit = Math.min(width.value / naturalWidth.value, height.value / naturalHeight.value)
  const boundX = Math.max(0, (naturalWidth.value * fit * scale.value - width.value) / 2)
  const boundY = Math.max(0, (naturalHeight.value * fit * scale.value - height.value) / 2)
  x.value = Math.max(-boundX, Math.min(boundX, x.value)) || 0
  y.value = Math.max(-boundY, Math.min(boundY, y.value)) || 0
}
function reset() { restorePull(); scale.value = 1; x.value = 0; y.value = 0 }
function zoom(value: number, clientX?: number, clientY?: number) {
  const rect = stage.value!.getBoundingClientRect()
  const ax = clientX === undefined ? 0 : clientX - rect.left - rect.width / 2
  const ay = clientY === undefined ? 0 : clientY - rect.top - rect.height / 2
  const next = Math.max(1, Math.min(6, value)), ratio = next / scale.value
  x.value = ax - (ax - x.value) * ratio
  y.value = ay - (ay - y.value) * ratio
  scale.value = next
  clamp()
}
function down(e: PointerEvent) {
  if (dismissing.value || (e.pointerType === 'mouse' && e.button !== 0)) return
  stage.value!.setPointerCapture(e.pointerId)
  points.set(e.pointerId, { x: e.clientX, y: e.clientY })
  if (points.size === 1) { moved = false; settling.value = false; canDismiss = scale.value === 1; start = { x: e.clientX, y: e.clientY } }
  else { moved = true; canDismiss = false; settling.value = false; pullX.value = 0; pullY.value = 0; lastTap.time = 0 }
}
function move(e: PointerEvent) {
  const before = points.get(e.pointerId)
  if (!before) return
  const old = [...points.values()]
  points.set(e.pointerId, { x: e.clientX, y: e.clientY })
  if (Math.hypot(e.clientX - start.x, e.clientY - start.y) > 8) moved = true
  if (points.size === 1) {
    const dx = e.clientX - start.x, dy = e.clientY - start.y
    if (canDismiss && scale.value === 1 && (pullY.value > 0 || (dy > 8 && dy > Math.abs(dx)))) {
      pullX.value = dx; pullY.value = Math.max(0, dy)
    } else { x.value += e.clientX - before.x; y.value += e.clientY - before.y; clamp() }
  }
  else {
    const now = [...points.values()]
    const a = old[0]!, b = old[1]!, c = now[0]!, d = now[1]!
    const previousDistance = Math.hypot(a.x - b.x, a.y - b.y)
    if (previousDistance > 0) zoom(scale.value * Math.hypot(c.x - d.x, c.y - d.y) / previousDistance, (a.x + b.x) / 2, (a.y + b.y) / 2)
    x.value += (c.x + d.x - a.x - b.x) / 2
    y.value += (c.y + d.y - a.y - b.y) / 2
    clamp()
  }
}
function up(e: PointerEvent) {
  if (!points.has(e.pointerId)) return
  points.delete(e.pointerId)
  if (pullY.value > 0) {
    lastTap.time = 0; canDismiss = false
    if (e.type === 'pointerup' && pullY.value >= Math.min(120, height.value * .18)) dismissPull()
    else restorePull()
    return
  }
  if (e.type !== 'pointerup' || moved) { lastTap.time = 0; return }
  const time = Date.now()
  if (time - lastTap.time < 320 && Math.hypot(e.clientX - lastTap.x, e.clientY - lastTap.y) < 30) {
    zoom(scale.value > 1 ? 1 : 2.5, e.clientX, e.clientY); lastTap.time = 0
  } else lastTap = { time, x: e.clientX, y: e.clientY }
}
function loaded(e: Event) {
  const img = e.target as HTMLImageElement
  naturalWidth.value = img.naturalWidth; naturalHeight.value = img.naturalHeight; clamp()
}
function keys(e: KeyboardEvent) {
  if (e.target instanceof HTMLButtonElement) return
  if (e.key === '+' || e.key === '=') zoom(scale.value * 1.5)
  else if (e.key === '-') zoom(scale.value / 1.5)
  else if (e.key === '0') reset()
  else if (e.key.startsWith('Arrow')) {
    e.preventDefault()
    x.value += e.key === 'ArrowLeft' ? 50 : e.key === 'ArrowRight' ? -50 : 0
    y.value += e.key === 'ArrowUp' ? 50 : e.key === 'ArrowDown' ? -50 : 0
    clamp()
  }
}
onMounted(() => {
  previousFocus = document.activeElement as HTMLElement | null
  dialog.value!.showModal()
  observer = new ResizeObserver(() => { width.value = stage.value!.clientWidth; height.value = stage.value!.clientHeight; clamp() })
  observer.observe(stage.value!)
})
onBeforeUnmount(() => { clearTimeout(closeTimer); observer?.disconnect(); dialog.value?.close(); previousFocus?.focus() })
</script>
<template>
  <Teleport to="body">
    <dialog ref="dialog" :class="['photo-viewer', { 'photo-settling': settling }]" :style="{ backgroundColor: `rgba(8,8,8,${shade})` }" aria-label="Purchase image viewer" @cancel.prevent="emit('close')" @keydown="keys">
      <header class="photo-toolbar" @touchstart.passive="controlStart" @touchend="controlEnd" @touchcancel="controlTouch=undefined">
        <span class="photo-filename">{{ props.filename }}</span>
        <button type="button" aria-label="Close image viewer" @click="emit('close')"><AppIcon name="close" /></button>
      </header>
      <div ref="stage" class="photo-stage" data-touch-interactive tabindex="0" aria-label="Image. Pinch or double tap to zoom, then drag to move. Drag down at full fit to close. Arrow keys move; plus and minus zoom."
        @pointerdown="down" @pointermove="move" @pointerup="up" @pointercancel="up" @lostpointercapture="up"
        @wheel.prevent="e => zoom(scale * Math.exp(-e.deltaY * .002), e.clientX, e.clientY)">
        <p v-if="failed" role="alert">Could not load this image. Close and try again.</p>
        <img v-else :src="src" :alt="filename" draggable="false" :style="{ transform }" @load="loaded" @error="failed = true" />
      </div>
      <footer class="photo-controls" @touchstart.passive="controlStart" @touchend="controlEnd" @touchcancel="controlTouch=undefined">
        <button type="button" aria-label="Zoom out" :disabled="scale <= 1" @click="zoom(scale / 1.5)">−</button>
        <button type="button" aria-label="Reset image zoom" @click="reset">{{ Math.round(scale * 100) }}%</button>
        <button type="button" aria-label="Zoom in" :disabled="scale >= 6" @click="zoom(scale * 1.5)">+</button>
      </footer>
    </dialog>
  </Teleport>
</template>
<style scoped>
.photo-viewer{position:fixed;inset:0;margin:0;width:100%;height:100dvh;max-width:none;max-height:none;padding:0;border:0;border-radius:0;background:#080808;color:#fff;overflow:hidden;overscroll-behavior:none}
.photo-viewer::backdrop{background:transparent}
.photo-settling,.photo-settling img{transition:background-color 180ms ease-out,transform 180ms ease-out}
@media(prefers-reduced-motion:reduce){.photo-settling,.photo-settling img{transition:none}}
.photo-viewer[open]{display:flex;flex-direction:column}
.photo-toolbar{display:flex;align-items:center;gap:16px;padding:calc(8px + env(safe-area-inset-top)) 12px 8px;flex-shrink:0}
.photo-filename{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.photo-viewer button{border:0;border-radius:10px;background:#292929;color:#fff;min-width:44px;height:44px;padding:8px 12px;display:inline-flex;align-items:center;justify-content:center}
.photo-stage{flex:1;min-height:0;position:relative;overflow:hidden;touch-action:none;user-select:none;cursor:grab;display:grid;place-items:center}
.photo-stage:active{cursor:grabbing}
.photo-stage img{position:absolute;width:100%;height:100%;object-fit:contain;pointer-events:none;transform-origin:center;will-change:transform}
.photo-stage p{color:#fff;padding:24px}
.photo-controls{display:flex;justify-content:center;gap:12px;padding:10px 12px calc(12px + env(safe-area-inset-bottom));flex-shrink:0}
</style>
