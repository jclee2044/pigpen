import type { Kind, Payloads, Operation } from './generated'
export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details: unknown = null) { super(message); this.name = 'ApiError' }
}
export async function request<T>(path: string, options: RequestInit = {}, timeout = 12000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const headers = new Headers(options.headers)
    if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type','application/json')
    const response = await fetch('/api/v1' + path, { ...options, headers, signal: controller.signal, cache:'no-store' })
    const body = await response.json().catch(() => null)
    if (!response.ok) throw new ApiError(response.status, body?.error?.code ?? 'http', body?.error?.message ?? 'The request could not be completed.', body?.error?.details)
    return body as T
  } catch(error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(0, 'network', 'Could not reach PigPen. Your saved submission can be retried safely.')
  } finally { clearTimeout(timer) }
}
export function operation<K extends Kind>(kind: K, data: Payloads[K], actor: string|null, entity = crypto.randomUUID()): Operation<K> {
  return { operation_id:crypto.randomUUID(), entity_id:entity, actor_id:actor, client_time:new Date().toISOString(), kind, data } as Operation<K>
}
export function execute(op: Operation) { return request<{operation_id:string;result:unknown}>('/operations',{method:'POST',body:JSON.stringify(op)}) }
