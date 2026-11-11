import { request } from './client'

export interface Source { label: string; path: string }
export interface Answer { answer: string; as_of: string; month: string; sources: Source[] }
export interface Turn { role: 'user' | 'assistant'; content: string }
export interface Insights { enabled: boolean; month: string; as_of: string; insights: string[] }

export function getInsights(month: string) {
  return request<Insights>('/advisor/insights?month=' + encodeURIComponent(month))
}
export function askAdvisor(actor_id: string, month: string, question: string, history: Turn[]) {
  return request<Answer>('/advisor/ask', {
    method: 'POST', body: JSON.stringify({ actor_id, month, question, history }),
  }, 75000)
}
