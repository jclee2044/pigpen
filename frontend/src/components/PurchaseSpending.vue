<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Category, Purchase } from '../api/models'
import { money, monthLabel, today } from '../lib/money'
import { orderCategories } from '../lib/categoryOrder'
import { shiftMonth, spendingWeeks } from '../lib/purchaseSpending'
const props = defineProps<{ month: string; purchases: Purchase[]; categories: Category[]; selectedWeek: string }>()
const emit = defineEmits<{ 'update:month': [string]; 'update:selectedWeek': [string] }>()
const currentDate = today()
const currentMonth = currentDate.slice(0, 7)
const edgeOffset = ref(0)
const sliding = ref(false)
const slideDirection = ref(1)
const weeks = computed(() => spendingWeeks(props.month, props.purchases))
const total = computed(() => props.purchases.reduce((sum, p) => sum + p.amount_minor, 0))
const maximum = computed(() => Math.max(...weeks.value.map(w => w.total), 1))
const selected = computed(() => weeks.value.find(w => w.start === props.selectedWeek))
const colors = ['#a94665', '#759b87', '#d79a63', '#839dc4', '#b48cba', '#baa257']
const categories = computed(() => [...new Set([...orderCategories(props.categories).map(c => c.id).filter(id => props.purchases.some(p => p.category_id === id)), ...props.purchases.map(p => p.category_id)])].map((id, i) => ({
  id, name: props.categories.find(c => c.id === id)?.name ?? 'Uncategorized', color: colors[i % colors.length],
})))
const breakdown = computed(() => categories.value.map(c => ({ ...c,
  total: (selected.value?.items ?? props.purchases).filter(p => p.category_id === c.id).reduce((sum, p) => sum + p.amount_minor, 0),
})).filter(c => c.total > 0).sort((a, b) => Number(props.categories.find(x => x.id === a.id)?.kind === 'personal') - Number(props.categories.find(x => x.id === b.id)?.kind === 'personal') || b.total - a.total))
function categoryTotal(items: Purchase[], id: string) { return items.filter(p => p.category_id === id).reduce((sum, p) => sum + p.amount_minor, 0) }
function move(direction: number) {
  if (sliding.value) return
  const month = shiftMonth(props.month, direction)
  if (month >= '0001-01' && month <= currentMonth) {
    slideDirection.value = direction
    sliding.value = true
    emit('update:month', month)
  }
}
watch(() => props.month, (month, previous) => {
  if (month > currentMonth) { emit('update:month', currentMonth); return }
  if (previous) slideDirection.value = month > previous ? 1 : -1
  emit('update:selectedWeek', '')
}, { immediate: true })
function hideLeavingMonth(element: Element) {
  element.setAttribute('inert', '')
  element.setAttribute('aria-hidden', 'true')
}
const gesture = ref<{ x: number; y: number; id: number }>()
let suppressClickUntil = 0
function start(event: PointerEvent) {
  if (sliding.value || !event.isPrimary || (event.pointerType === 'mouse' && event.button !== 0)) return
  edgeOffset.value = 0
  suppressClickUntil = 0
  gesture.value = { x: event.clientX, y: event.clientY, id: event.pointerId }
}
function track(event: PointerEvent) {
  const initial = gesture.value
  if (!initial || initial.id !== event.pointerId) return
  const dx = event.clientX - initial.x, dy = event.clientY - initial.y
  if (Math.abs(dy) > 10 && Math.abs(dy) > Math.abs(dx)) { cancelGesture(); return }
  if (dx < -6 && props.month >= currentMonth && Math.abs(dx) > Math.abs(dy) * 1.5) {
    // Resist a forward drag without bringing another month into view.
    edgeOffset.value = -52 * (1 - Math.exp(dx / 130))
    suppressClickUntil = performance.now() + 400
    const surface = event.currentTarget as HTMLElement
    if (!surface.hasPointerCapture(event.pointerId)) surface.setPointerCapture(event.pointerId)
    return
  }
  edgeOffset.value = 0
  if (Math.abs(dx) >= 18 && Math.abs(dx) > Math.abs(dy) * 1.5) {
    gesture.value = undefined
    suppressClickUntil = performance.now() + 400
    move(dx < 0 ? 1 : -1)
  }
}
function finish(event: PointerEvent) {
  track(event)
  cancelGesture()
}
function cancelGesture() {
  if (edgeOffset.value) suppressClickUntil = performance.now() + 400
  edgeOffset.value = 0
  gesture.value = undefined
}
function captureClick(event: MouseEvent) {
  if (event.detail > 0 && performance.now() < suppressClickUntil) { event.stopPropagation(); event.preventDefault(); suppressClickUntil = 0 }
}
function select(start: string) {
  emit('update:selectedWeek', props.selectedWeek === start ? '' : start)
}
</script>

<template>
  <section class="card spending-card" aria-label="Monthly spending">
    <div class="month-navigation">
      <button class="icon-button" aria-label="Previous month" :disabled="sliding || month === '0001-01'" @click="move(-1)">‹</button>
      <h2 aria-live="polite">{{ monthLabel(month) }}</h2>
      <button class="icon-button" aria-label="Next month" :disabled="sliding || month >= currentMonth" @click="move(1)">›</button>
    </div>
    <div class="month-window swipe-month" :style="{ '--slide-direction': slideDirection }" @pointerdown="start" @pointermove="track" @pointerup="finish" @pointercancel="cancelGesture" @lostpointercapture.self="cancelGesture" @click.capture="captureClick">
      <div class="month-edge-surface" :class="{ 'edge-dragging': edgeOffset !== 0 }" :style="{ transform: `translateX(${edgeOffset}px)` }">
      <Transition name="month-slide" @before-enter="sliding = true" @before-leave="hideLeavingMonth" @after-enter="sliding = false" @enter-cancelled="sliding = false">
      <div :key="month" class="month-page">
      <div class="month-total"><span>Total spent</span><strong data-testid="month-spending-total">{{ money(total) }}</strong></div>
      <p class="chart-hint">Swipe to change month · Tap a week for details</p>
      <div class="weekly-chart" aria-label="Spending by week">
        <button v-for="week in weeks" :key="week.start" class="week-column" :class="{ selected: selectedWeek === week.start, faded: selectedWeek && selectedWeek !== week.start }"
          :aria-label="`${monthLabel(month)} ${week.label}: ${money(week.total)}`" :aria-pressed="selectedWeek === week.start" :disabled="week.start > currentDate" @click="select(week.start)">
          <span class="week-value">{{ money(week.total) }}</span>
          <span class="bar-track"><span class="week-bar" :style="{ height: `${week.total / maximum * 100}%` }">
            <span v-for="c in categories" :key="c.id" :style="{ height: `${week.total ? categoryTotal(week.items, c.id) / week.total * 100 : 0}%`, background: c.color }" />
          </span><span v-if="!week.total" class="zero-bar" /></span>
          <span class="week-label">{{ week.label }}</span>
        </button>
      </div>
    <div class="breakdown-heading"><h3>{{ selected ? `${monthLabel(month).split(' ')[0]} ${selected.label}` : 'Monthly categories' }}</h3><button v-if="selected" class="inline-link" @click="emit('update:selectedWeek', '')">Show full month</button></div>
    <div aria-live="polite">
      <div v-if="selected" class="week-summary"><strong>{{ money(selected.total) }}</strong><span>{{ selected.items.length }} {{ selected.items.length === 1 ? 'purchase' : 'purchases' }}</span></div>
      <ul v-if="breakdown.length" class="category-breakdown"><li v-for="c in breakdown" :key="c.id"><span class="category-dot" :style="{ background: c.color }" /><span>{{ c.name }}</span><strong>{{ money(c.total) }}</strong></li></ul>
      <p v-else class="no-spending">No spending {{ selected ? 'this week' : 'this month' }}.</p>
    </div>
      </div>
      </Transition>
      </div>
    </div>
  </section>
</template>

<style scoped>
.month-window{display:grid;overflow:hidden;margin:0 -6px;padding:0 6px}
.month-edge-surface{display:grid;min-width:0;transition:transform 320ms cubic-bezier(.22,1,.36,1)}
.month-edge-surface.edge-dragging{transition:none}
.month-page{grid-area:1/1;min-width:0}
.month-slide-enter-active,.month-slide-leave-active{transition:transform 280ms cubic-bezier(.22,1,.36,1),opacity 280ms ease;will-change:transform,opacity}
.month-slide-leave-active{pointer-events:none}
.month-slide-enter-from{transform:translateX(calc(var(--slide-direction) * 105%));opacity:.35}
.month-slide-leave-to{transform:translateX(calc(var(--slide-direction) * -105%));opacity:.15}
@media(prefers-reduced-motion:reduce){.month-edge-surface{transition:none;transform:none!important}.month-slide-enter-active,.month-slide-leave-active{transition:none}.month-slide-enter-from,.month-slide-leave-to{transform:none;opacity:1}}

.spending-card{margin-bottom:24px}.month-navigation{display:flex;align-items:center;justify-content:space-between;gap:8px}.month-navigation h2{margin:0;text-align:center;font-size:24px}.month-navigation button{font-size:32px}.swipe-month{touch-action:pan-y;user-select:none}.month-total{display:grid;gap:8px;margin-top:20px}.month-total>span{font-size:13px;color:var(--muted)}.month-total strong{font-size:clamp(28px,6vw,48px);font-weight:400;letter-spacing:-.04em;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}.chart-hint{font-size:12px;margin:12px 0 22px}.weekly-chart{display:flex;gap:12px;padding-bottom:18px;border-bottom:1px solid var(--line);background:repeating-linear-gradient(to top,transparent 0,transparent 49px,var(--line) 50px,transparent 51px);background-clip:content-box}.week-column{flex:1;min-width:0;display:flex;align-items:center;flex-direction:column;gap:10px;border:0;background:transparent;color:var(--ink);padding:6px 2px;border-radius:8px;min-height:210px}.week-value{font-size:12px;max-width:100%;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}.bar-track{height:144px;display:flex;align-items:end;justify-content:center;width:100%;position:relative;margin-top:auto}.week-bar{display:flex;flex-direction:column-reverse;width:min(100%,56px);overflow:hidden;border-radius:5px 5px 0 0}.week-bar>span{display:block;width:100%;flex-shrink:0}.zero-bar{height:3px;width:min(100%,56px);background:var(--line)}.week-label{font-size:12px;white-space:nowrap}.week-column.selected{background:var(--selected);outline:2px solid var(--rose);outline-offset:1px}.week-column.faded .week-bar{opacity:.35}.breakdown-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:20px}.breakdown-heading h3{margin:0}.week-summary{display:flex;align-items:baseline;gap:12px;margin:12px 0}.week-summary strong{font-size:26px;font-weight:400}.week-summary>span{font-size:13px;color:var(--muted)}.category-breakdown{list-style:none;margin:12px 0 0;padding:0;display:grid;gap:14px}.category-breakdown li{display:flex;align-items:center;gap:10px;font-size:14px}.category-breakdown li>span:nth-child(2){overflow-wrap:anywhere;min-width:0}.category-breakdown strong{margin-left:auto;white-space:nowrap;font-variant-numeric:tabular-nums}.category-dot{width:10px;height:10px;border-radius:50%;flex:none}.no-spending{margin:14px 0 0;font-size:14px}@media(max-width:380px){.weekly-chart{gap:5px}.week-value{font-size:10px}.week-label{font-size:11px}.month-navigation h2{font-size:21px}}
</style>
