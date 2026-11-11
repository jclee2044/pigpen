import { ref, watch } from 'vue'
import { askAdvisor, type Answer, type Turn } from '../api/advisor'
import { state } from './household'
import { shell } from './shell'

interface Exchange extends Answer { question: string }
export const exchanges = ref<Exchange[]>([])
export const thinking = ref(false)
export const questionError = ref('')
let generation = 0

export function clearConversation() {
  generation++
  exchanges.value = []
  questionError.value = ''
  thinking.value = false
}

watch([() => state.selectedId, () => shell.month], clearConversation, { flush: 'sync' })

export async function ask(question: string) {
  if (!question || thinking.value || !state.online) return false
  const current = generation
  thinking.value = true
  questionError.value = ''
  const history: Turn[] = exchanges.value.slice(-3).flatMap(e => [
    { role: 'user', content: e.question }, { role: 'assistant', content: e.answer.slice(0, 6000) },
  ])
  try {
    const answer = await askAdvisor(state.selectedId, shell.month, question, history)
    if (current !== generation) return false
    exchanges.value.push({ question, ...answer })
    return true
  } catch (error) {
    if (current === generation) questionError.value = error instanceof Error ? error.message : 'Could not get an answer.'
    return false
  } finally {
    if (current === generation) thinking.value = false
  }
}
