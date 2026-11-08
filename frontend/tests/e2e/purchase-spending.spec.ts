import { test, expect } from '@playwright/test'
import { seed, command } from './helpers'
import type { Snapshot } from '../../src/api/models'

test.use({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
test('monthly chart totals, weekly categories, filters and swipe navigation', async ({ page, request }) => {
  const total = page.locator('.month-page:not([inert]) [data-testid=month-spending-total]')
  const ready = () => expect(page.getByRole('button', { name: 'Next month', exact: true })).toBeEnabled()
  const user = await seed(page, request, 'Spending chart')
  const snapshot = await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot
  const food = snapshot.records.categories.find(c => c.name === 'Food')!
  const other = snapshot.records.categories.find(c => c.kind === 'expense' && c.id !== food.id)!
  for (const [item, amount, category, date] of [
    ['First Sunday', 1000, food.id, '2024-12-01'], ['Monday food', 2000, food.id, '2024-12-02'],
    ['Monday other', 500, other.id, '2024-12-02'], ['Last day', 700, food.id, '2024-12-31'],
  ] as const) await command(request, 'purchase.create', { item, amount_minor: amount, category_id: category, transaction_date: date }, user.id)
  await page.evaluate(() => localStorage.setItem('pigpen-month', '2024-12'))
  await page.goto('/purchases')
  await expect(total).toHaveText('$42.00')
  const chart = page.getByRole('region', { name: 'Monthly spending', exact: true })
  const week = chart.getByRole('button', { name: 'December 2024 2–8: $25.00', exact: true })
  await week.tap()
  await expect(week).toHaveAttribute('aria-pressed', 'true')
  await expect(chart.locator('.week-summary')).toContainText('$25.00')
  await expect(chart.locator('.category-breakdown')).toContainText(other.name)
  await expect(page.getByRole('button', { name: 'First Sunday', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Monday food', exact: true })).toBeVisible()
  await page.getByRole('combobox', { name: 'Category', exact: true }).selectOption(food.id)
  await expect(total).toHaveText('$37.00')
  await expect(chart.locator('.week-summary')).toContainText('$20.00')
  await chart.getByRole('button', { name: 'Show full month' }).tap()
  await expect(page.getByRole('button', { name: 'First Sunday', exact: true })).toBeVisible()
  await page.getByRole('combobox', { name: 'Category', exact: true }).selectOption('')
  await page.evaluate(() => { (document.activeElement as HTMLElement)?.blur(); window.scrollTo(0, 0) })
  await page.screenshot({ path: '../output/purchase-spending/month-mobile.png', fullPage: true })
  await chart.getByRole('button', { name: 'Previous month' }).tap()
  await expect(chart.getByRole('heading', { name: 'November 2024' })).toBeVisible()
  await chart.getByRole('button', { name: 'Next month' }).tap()
  await expect(total).toHaveText('$42.00')
  await ready()
  // A real horizontal touch gesture navigates across the year boundary.
  await chart.locator('.month-total').scrollIntoViewIfNeeded()
  const box = (await chart.locator('.month-total').boundingBox())!
  const x = box.x + box.width * .8, y = box.y + 20
  const session = await page.context().newCDPSession(page)
  await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] })
  for (let i = 1; i <= 8; i++) await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x - i * 18, y }] })
  await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await session.detach()
  await expect(chart.getByRole('heading', { name: 'January 2025' })).toBeVisible()
  await expect(total).toHaveText('$0.00')
  await expect(chart).toContainText('No spending this month.')
  await ready()
  await chart.getByRole('button', { name: 'Previous month' }).focus()
  await page.keyboard.press('Enter')
  await expect(total).toHaveText('$42.00')
  for (const width of [320, 390, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  }
  await week.focus(); await page.keyboard.press('Enter')
  await expect(week).toHaveAttribute('aria-pressed', 'true')
  await page.screenshot({ path: '../output/purchase-spending/week-desktop.png', fullPage: true })
})


test('month slides in the navigation direction and respects reduced motion', async ({ page, request }) => {
  await seed(page, request, 'Month motion')
  await page.evaluate(() => localStorage.setItem('pigpen-month', '2024-12'))
  await page.goto('/purchases')
  const chart = page.getByRole('region', { name: 'Monthly spending', exact: true })
  for (const [button, direction] of [['Next month', 1], ['Previous month', -1]] as const) {
    await chart.getByRole('button', { name: button, exact: true }).click()
    await expect(chart.locator('.month-slide-leave-to')).toHaveCount(1)
    const positions = await chart.evaluate(element => {
      const pages = [...element.querySelectorAll<HTMLElement>('.month-page')]
      for (const node of pages) for (const animation of node.getAnimations()) { animation.pause(); animation.currentTime = 120 }
      return pages.map(node => ({ leaving: node.hasAttribute('inert'), x: new DOMMatrixReadOnly(getComputedStyle(node).transform).m41 }))
    })
    expect(positions).toHaveLength(2)
    expect(positions.find(p => !p.leaving)!.x * direction).toBeGreaterThan(0)
    expect(positions.find(p => p.leaving)!.x * direction).toBeLessThan(0)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.screenshot({ path: `../output/purchase-slide/slide-${direction}.png` })
    await chart.evaluate(element => { for (const animation of element.getAnimations({ subtree: true })) animation.play() })
    await expect(chart.locator('.month-page')).toHaveCount(1)
    await expect(chart.getByRole('button', { name: 'Next month', exact: true })).toBeEnabled()
  }
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await chart.getByRole('button', { name: 'Next month', exact: true }).click()
  await expect(chart.locator('.month-page')).toHaveCount(1)
  expect(await chart.locator('.month-page').evaluate(node => getComputedStyle(node).transform)).toBe('none')
})

test('current week boundary and swipe starts before lifting the finger', async ({ page, request }) => {
  await page.clock.setFixedTime(new Date('2026-11-08T17:00:00Z'))
  await seed(page, request, 'Current week boundary')
  await page.evaluate(() => localStorage.setItem('pigpen-month', '2027-01'))
  await page.goto('/purchases')
  const chart = page.getByRole('region', { name: 'Monthly spending', exact: true })
  await expect(chart.getByRole('heading', { name: 'November 2026' })).toBeVisible()
  await expect(chart.getByRole('button', { name: 'Next month', exact: true })).toBeDisabled()
  await expect(page.getByRole('combobox', { name: 'Purchased by', exact: true })).toHaveCount(0)
  await expect(chart.getByRole('button', { name: /November 2026 9–15:/ })).toBeDisabled()
  await expect(chart.getByRole('button', { name: /November 2026 2–8:/ })).toBeEnabled()
  const session = await page.context().newCDPSession(page)
  async function beginSwipe(dx: number) {
    await expect(chart.locator('.month-page')).toHaveCount(1)
    await chart.locator('.month-total').scrollIntoViewIfNeeded()
    const box = (await chart.locator('.month-total').boundingBox())!
    const x = box.x + box.width / 2, y = box.y + 20
    await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] })
    for (let i = 1; i <= 3; i++) await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + dx * i / 3, y }] })
  }
  // Forward swiping at today's boundary cannot navigate into a future month.
  await beginSwipe(-90)
  const edge = chart.locator('.month-edge-surface')
  const offset = await edge.evaluate(node => new DOMMatrixReadOnly(getComputedStyle(node).transform).m41)
  expect(offset).toBeLessThan(-10)
  expect(offset).toBeGreaterThan(-52)
  expect(await chart.locator('.month-window').evaluate(node => {
    const box = node.getBoundingClientRect()
    return document.elementFromPoint(box.right - 8, box.top + 40) === node
  })).toBe(true)
  await page.screenshot({ path: '../output/purchase-edge/drag.png' })
  await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await expect(chart.getByRole('heading', { name: 'November 2026' })).toBeVisible()
  await expect(chart.locator('.month-page')).toHaveCount(1)
  await expect.poll(() => edge.evaluate(node => new DOMMatrixReadOnly(getComputedStyle(node).transform).m41)).toBe(0)
  await beginSwipe(-90)
  await session.send('Input.dispatchTouchEvent', { type: 'touchCancel', touchPoints: [] })
  await expect.poll(() => edge.evaluate(node => new DOMMatrixReadOnly(getComputedStyle(node).transform).m41)).toBe(0)
  await expect(chart.getByRole('heading', { name: 'November 2026' })).toBeVisible()
  await beginSwipe(30)
  // The month changes while the finger is still down, after only 18px of travel.
  await expect(chart.getByRole('heading', { name: 'October 2026' })).toBeVisible()
  await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await session.detach()
  await expect(chart.getByRole('button', { name: 'Next month', exact: true })).toBeEnabled()
  await chart.getByRole('button', { name: 'Next month', exact: true }).click()
  await expect(chart.getByRole('heading', { name: 'November 2026' })).toBeVisible()
  await expect(chart.locator('.month-page')).toHaveCount(1)
  await expect(chart.getByRole('button', { name: 'Next month', exact: true })).toBeDisabled()
  await page.evaluate(() => { (document.activeElement as HTMLElement)?.blur(); scrollTo(0, 0) })
  await page.screenshot({ path: '../output/purchase-swipe-boundary/mobile.png', fullPage: true })
})
