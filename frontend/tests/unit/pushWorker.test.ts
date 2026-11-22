import { readFileSync } from 'node:fs'
import { runInNewContext } from 'node:vm'
import { expect, test, vi } from 'vitest'

const worker = readFileSync(new URL('../../public/sw.js', import.meta.url), 'utf8')

test.each([
  { title: 'New approval request', expected: 'New approval request' },
  { title: undefined, expected: 'PigPen' },
  { title: '  ', expected: 'PigPen' },
])('push displays $expected when the payload title is $title', async ({ title, expected }) => {
  const showNotification = vi.fn()
  const postMessage = vi.fn()
  const listeners = new Map()
  runInNewContext(worker, { self: {
    addEventListener: listeners.set.bind(listeners),
    clients: { matchAll: async () => [{ postMessage }] },
    registration: { showNotification },
  } })

  const id = '00000000-0000-4000-a000-000000000001'
  const body = 'Alex submitted "Lawn chair" for approval'
  const waitUntil = vi.fn()
  listeners.get('push')({ data: { json: () => ({ title, notification_id: id, body }) }, waitUntil })
  await waitUntil.mock.calls[0]![0]

  expect(showNotification).toHaveBeenCalledWith(expected, expect.objectContaining({
    body, tag: id, data: { url: '/notifications?notification=' + id },
  }))
  expect(postMessage).toHaveBeenCalledWith({ type: 'PIGPEN_NOTIFICATION' })
})
