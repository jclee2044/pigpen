<script setup lang="ts">
import { computed, nextTick, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { getInsights, type Insights } from '../api/advisor'
import { activeUser, state } from '../state/household'
import { shell } from '../state/shell'
import { ask, exchanges, thinking, questionError } from '../state/advisor'
import pigFace from '../../../assets/advisor/pig-face.webp'
import AppIcon from './AppIcon.vue'
import { monthLabel } from '../lib/money'

const expanded = defineModel<boolean>('expanded', { required: true })
const frame = ref<HTMLElement>()
const transcript = ref<HTMLElement>()
const pendingQuestion = ref('')
// Keep the outgoing bubble mounted when its reply arrives.
const messages = computed(() => {
  const turns = exchanges.value.map(turn => ({ question: turn.question, reply: turn }))
  return pendingQuestion.value && thinking.value
    ? [...turns, { question: pendingQuestion.value, reply: null }]
    : turns
})
let motion: Animation | undefined
onBeforeUnmount(() => motion?.cancel())

const composing = ref(false)
let followLatest = true
function showLatest() {
  const log = transcript.value
  if (log) log.scrollTop = log.scrollHeight
}
function trackReadingPosition() {
  const log = transcript.value
  if (log) followLatest = log.scrollHeight - log.scrollTop - log.clientHeight < 8
}
function focusComposer() {
  composing.value = true
  followLatest = true
  showLatest()
}

const root = document.documentElement
const viewport = window.visualViewport
let restingHeight = window.innerHeight
let keyboardVisible = false
let savedScroll = 0
let navTimer = 0
function rememberViewport() {
  if (!keyboardVisible && !composing.value) restingHeight = viewport?.height ?? window.innerHeight
}

// Handle the first tap inside the user gesture so the browser opens the native
// keyboard without first centering the input. Drags and caret edits stay native.
let touchOrigin: Touch | undefined
function startTouch(event: TouchEvent) {
  touchOrigin = event.touches.length === 1 && event.target !== document.activeElement ? event.touches[0] : undefined
}
function moveTouch(event: TouchEvent) {
  const touch = event.touches[0]
  if (!touchOrigin || !touch || event.touches.length !== 1 ||
      Math.hypot(touch.clientX - touchOrigin.clientX, touch.clientY - touchOrigin.clientY) > 8) touchOrigin = undefined
}
function endTouch(event: TouchEvent) {
  const tap = touchOrigin
  touchOrigin = undefined
  if (!tap || event.touches.length || !event.cancelable) return
  event.preventDefault()
  rememberViewport()
  root.classList.add('advisor-awaiting-keyboard')
  clearTimeout(navTimer)
  navTimer = window.setTimeout(() => root.classList.remove('advisor-awaiting-keyboard'), 500)
  const input = event.currentTarget as HTMLInputElement
  input.focus({ preventScroll: true })
}

watch(transcript, (log, _, cleanup) => {
  if (!log) return
  const observer = new ResizeObserver(() => { if (followLatest) showLatest() })
  observer.observe(log)
  cleanup(() => observer.disconnect())
}, { flush: 'post' })

// Only the content between the two bars is resized. Keep listening through
// blur, since the keyboard can finish closing after the input loses focus.
let layoutWidth = window.innerWidth
function layout() {
  const visible = viewport?.height ?? window.innerHeight
  if (window.innerWidth !== layoutWidth || (!composing.value && !keyboardVisible)) {
    layoutWidth = window.innerWidth
    restingHeight = window.innerHeight
  }
  const pan = Math.max(0, viewport?.offsetTop ?? 0)
  const lostHeight = restingHeight - visible
  const editing = composing.value || keyboardVisible
  keyboardVisible = editing && (lostHeight > (keyboardVisible ? 2 : 65) || pan > 64)
  const locked = expanded.value || keyboardVisible
  const wasLocked = root.classList.contains('chat-open')
  if (locked && !wasLocked) savedScroll = window.scrollY
  const dashboardBottom = !wasLocked && keyboardVisible && !expanded.value
    ? frame.value?.getBoundingClientRect().bottom : undefined
  root.classList.toggle('advisor-keyboard', keyboardVisible)
  root.classList.toggle('chat-open', locked)
  if (keyboardVisible) root.classList.remove('advisor-awaiting-keyboard')
  if (editing && pan) root.style.setProperty('--chat-pan', pan + 'px')
  else root.style.removeProperty('--chat-pan')
  if (!locked) {
    root.style.removeProperty('--chat-height')
    if (wasLocked && savedScroll) window.scrollTo(0, savedScroll)
    return
  }
  const nav = document.querySelector<HTMLElement>('.mobile-nav')
  const gap = (nav?.offsetHeight ?? 0) + 4
  const height = keyboardVisible ? visible : Math.min(visible, window.innerHeight - gap)
  if (dashboardBottom !== undefined) {
    // Start docking at the card's existing edge, including on a scrolled Home.
    root.style.setProperty('--chat-height', Math.max(1, dashboardBottom - pan) + 'px')
    frame.value?.getBoundingClientRect()
  }
  root.style.setProperty('--chat-height', height + 'px')
}
watch([expanded, composing], layout, { flush: 'post' })
onMounted(() => {
  viewport?.addEventListener('resize', layout)
  viewport?.addEventListener('scroll', layout)
  window.addEventListener('resize', layout)
})
onBeforeUnmount(() => {
  viewport?.removeEventListener('resize', layout)
  viewport?.removeEventListener('scroll', layout)
  window.removeEventListener('resize', layout)
  clearTimeout(navTimer)
  root.classList.remove('chat-open', 'advisor-keyboard', 'advisor-awaiting-keyboard')
  root.style.removeProperty('--chat-pan')
  root.style.removeProperty('--chat-height')
})
function tapFrame(event: MouseEvent) {
  if (!expanded.value && event.target instanceof Element && !event.target.closest('button,input,label,a')) void showChat(true)
}

async function showChat(open: boolean, fromComposer = false) {
  const panel = frame.value
  if (!panel || expanded.value === open) return
  const editing = open && panel.querySelector('input') === document.activeElement
  if (open && !composing.value && document.activeElement?.tagName !== 'INPUT'
      && (window.visualViewport?.height ?? window.innerHeight) >= window.innerHeight) rememberViewport()
  const before = panel.getBoundingClientRect()
  const portrait = panel.querySelector('.pig')?.getBoundingClientRect()
  motion?.cancel()
  expanded.value = open
  await nextTick()
  if (!panel.isConnected || expanded.value !== open) return
  const after = panel.getBoundingClientRect()
  if (!(editing && fromComposer) && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const deltaX = before.left - after.left
    const deltaY = before.top - after.top
    const translate = `translate(${deltaX}px, ${deltaY}px)`
    if (open) {
      // Grow the actual border and grid. Scaling the full conversation also
      // squashes its text and makes the newly mounted header jump into view.
      const options = { duration: 460, easing: 'cubic-bezier(.32,0,.18,1)' }
      const avatar = panel.querySelector<HTMLElement>('.pig')
      const endPortrait = avatar?.getBoundingClientRect()
      motion = panel.animate([
        { transform: translate, width: before.width + 'px', marginBottom: after.height - before.height + 'px' },
        { transform: 'none', width: '100%', marginBottom: '0px' },
      ], options)
      if (avatar && portrait && endPortrait) {
        const x = portrait.left - endPortrait.left - deltaX
        const y = portrait.top - endPortrait.top - deltaY
        avatar.animate([{ transform: `translate(${x}px, ${y}px)` }, { transform: 'none' }], options)
      }
      for (const part of panel.querySelectorAll('.chat-header div,.chat-header button,.transcript,footer')) {
        part.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 230, delay: 80, fill: 'backwards' })
      }
    } else {
      motion = panel.animate([
        { transform: `${translate} scale(${before.width / after.width}, ${before.height / after.height})` },
        { transform: 'none' },
      ], { duration: 320, easing: 'ease-out' })
    }
  }
  if (open) showLatest()
  if (!editing) panel.querySelector<HTMLElement>(open ? '.chat-header button' : '#advisor-title')?.focus({ preventScroll: true })
}
watch([() => exchanges.value.length, thinking], () => {
  if (followLatest) showLatest()
}, { flush: 'post' })
const insights = ref<Insights>()
const draft = ref('')
const loadError = ref(false)
const retry = ref(0)
const available = computed(() => insights.value?.enabled && state.online && activeUser.value)
watch([() => shell.month, () => state.selectedId], () => { draft.value = ''; insights.value = undefined; expanded.value = false })
watch([() => shell.month, () => state.online, () => state.lastSync, () => state.selectedId, retry], async (_, __, onCleanup) => {
  let current = true
  onCleanup(() => { current = false })
  loadError.value = false
  if (!state.online || !activeUser.value) return
  try {
    const result = await getInsights(shell.month)
    if (current) insights.value = result
  } catch {
    if (current) loadError.value = true
  }
}, { immediate: true })
async function send(question: string) {
  if (!question.trim() || thinking.value || !available.value) return
  followLatest = true
  void showChat(true, true)
  pendingQuestion.value = question.trim()
  draft.value = ''
  const actor = state.selectedId
  const month = shell.month
  if (!await ask(question.trim()) && state.selectedId === actor && shell.month === month && !draft.value) draft.value = question
  pendingQuestion.value = ''
}
</script>

<template>
  <section ref="frame" class="card advisor" :class="{ 'pig-chat': expanded }" :aria-label="expanded ? 'Chat with Sir Pennington' : 'Ask Sir Pennington'" :data-defer-app-update="expanded || undefined" @click="tapFrame" @keydown.esc="showChat(false)">
   <div v-if="!expanded" class="advisor-summary" :data-touch-interactive="composing || undefined">
    <header><img :src="pigFace" alt="" class="pig"><div><h2 id="advisor-title" tabindex="-1"><button class="open-card" @click="showChat(true)">Ask Sir Pennington</button></h2><small>{{ monthLabel(shell.month) }}</small></div></header>
    <ul v-if="insights"><li v-for="line in insights.insights.slice(0, 2)" :key="line">{{ line }}</li></ul>
    <p v-if="!state.online" role="status">Reconnect to refresh insights or ask a question.</p>
    <p v-else-if="loadError" role="status">Insights couldn’t load. <button class="button small" @click="retry++">Retry</button></p>
    <p v-else-if="!insights" role="status">Loading insights…</p>
    <p v-else-if="!insights.enabled" class="text-small">Chat is currently unavailable.</p>
    <template v-if="available">
      <div class="prompts">
        <button v-for="prompt in ['Where could we reallocate money?', 'Which purchases drove spending?']" :key="prompt" class="button small" :disabled="thinking" @click="send(prompt)">{{ prompt }}</button>
      </div>
    </template>
   </div>
   <template v-else>
      <header class="chat-header"><img :src="pigFace" alt="" class="pig"><div><h2>Sir Pennington</h2><small>{{ monthLabel(shell.month) }}</small></div><button class="icon-button" data-touch-interactive aria-label="Close chat" @click="showChat(false)"><AppIcon name="close" /></button></header>
      <div ref="transcript" class="transcript" data-touch-interactive @scroll.passive="trackReadingPosition" role="log" aria-label="Conversation" aria-live="polite">
        <div class="received message">Hi! Let’s find a little more room in your budget.</div>
        <template v-for="(turn, index) in messages" :key="index">
          <div class="sent message">{{ turn.question }}</div>
          <div v-if="turn.reply" class="pig-reply"><img :src="pigFace" alt="" class="reply-pig"><div class="received message">{{ turn.reply.answer }}<nav aria-label="Supporting records"><RouterLink v-for="source in turn.reply.sources" :key="source.path" :to="source.path" @click="expanded = false">{{ source.label }}</RouterLink></nav></div></div>
        </template>
        <div v-if="thinking" class="received message"><span class="typing" role="status" aria-label="Sir Pennington is typing"><i/><i/><i/></span></div>
        <p v-if="questionError" class="notice error" role="alert">{{ questionError }}</p>
      </div>
   </template>
   <footer v-if="available || expanded">
     <p v-if="expanded && !available" role="status">{{ state.online ? 'Chat is currently unavailable.' : 'Reconnect to send a message.' }}</p>
     <form @submit.prevent="send(draft)">
       <div class="composer">
         <input id="advisor-question" v-model="draft" maxlength="1000" autocomplete="off" aria-label="Message Sir Pennington" placeholder="Message Sir Pennington…" @pointerdown="rememberViewport" @touchstart.passive="startTouch" @touchmove.passive="moveTouch" @touchcancel="touchOrigin = undefined" @touchend="endTouch" @focus="focusComposer" @blur="composing = false">
         <button class="button primary" data-touch-interactive :disabled="!available || thinking || !draft.trim()" :aria-label="expanded ? 'Send message' : 'Ask'" @pointerdown="event => { if (composing) event.preventDefault() }"><AppIcon v-if="expanded" name="arrow" /><template v-else>Ask</template></button>
       </div>
     </form>
   </footer>
  </section>
</template>
<style scoped>
.advisor{border:2px solid var(--brand-rose);transform-origin:top left;margin:0 0 24px auto;width:min(100%,560px);overflow-wrap:anywhere}
.advisor:not(.pig-chat){cursor:pointer}
.open-card{font:inherit;letter-spacing:inherit;color:inherit;border:0;background:none;padding:0}
.advisor header,.chat-header{display:flex;align-items:center;gap:12px}
.pig{width:64px;height:54px;object-fit:contain;flex:none}
.advisor h2,.chat-header h2{margin:0}
.advisor ul{padding-left:20px;margin:12px 0;line-height:1.5;font-size:14px}
.prompts{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}
.prompts .button{white-space:normal;text-align:left;border-radius:20px}
form{margin:10px 0 0}.composer{display:flex;gap:8px;align-items:center}
.composer input{font-size:16px;flex:1;min-width:0;border-radius:24px}.composer .button{border-radius:24px}
.advisor label{font-size:13px;display:block;margin-bottom:6px}
.advisor.pig-chat{display:grid;grid-template-rows:auto minmax(0,1fr) auto;width:100%;flex:1;min-height:0;margin:0;overflow:clip;padding:0}
.typing{display:inline-flex;align-items:center;gap:4px;height:16px}
.typing i{width:6px;height:6px;border-radius:50%;background:var(--muted)}
@media(prefers-reduced-motion:no-preference){.typing i{animation:pulse 1.2s ease-in-out infinite alternate}.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}}
@keyframes pulse{from{opacity:.35}to{opacity:1}}
.chat-header{padding:12px 18px;border-bottom:1px solid var(--line);flex:none}
.chat-header .icon-button{margin-left:auto}
.transcript{display:flex;flex-direction:column;gap:14px;overflow:auto;overscroll-behavior:contain;touch-action:pan-y;flex:1;min-height:0;padding:22px 18px;background:var(--page)}
.message{max-width:85%;padding:12px 16px;border-radius:22px;white-space:pre-line;overflow-wrap:anywhere;line-height:1.5;font-size:15px}
.sent{align-self:flex-end;background:var(--rose);color:white;border-bottom-right-radius:5px}
.received{align-self:flex-start;background:var(--track);color:var(--ink);border-bottom-left-radius:5px}
.pig-reply{display:flex;align-items:flex-end;gap:6px}
.reply-pig{width:34px;height:34px;object-fit:contain;flex:none}
.message nav{display:flex;gap:10px;flex-wrap:wrap;font-size:12px;margin-top:10px}
.pig-chat footer{position:relative;z-index:1;background:var(--paper);padding:12px 18px max(12px,env(safe-area-inset-bottom));border-top:1px solid var(--line);flex:none}
footer form{margin:0}
@media(max-width:760px){.message{max-width:90%}}
.transcript > *{flex-shrink:0}
@media(prefers-reduced-motion:no-preference){
  .received.message,.pig-reply,.sent{animation:bubble-in 310ms cubic-bezier(.18,.75,.25,1) backwards}
  .pig-reply .received{animation:none}
  .sent{transform-origin:bottom right}
  .pig-reply,.received{transform-origin:bottom left}
  .transcript > :nth-child(2){animation-delay:45ms}
  .transcript > :nth-child(n+3){animation-delay:85ms}
}
@keyframes bubble-in{from{opacity:0;transform:translateY(9px) scale(.96)}to{opacity:1;transform:none}}
</style>
