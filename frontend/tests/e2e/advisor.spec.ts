import { expect, test } from '@playwright/test'
import { seed } from './helpers'

test.use({ hasTouch: true })

test('ask from the dashboard, follow up, and start a fresh session', async ({ page, request, context }) => {
  await page.setViewportSize({ width: 320, height: 800 })
  await page.route('**/api/v1/advisor/insights?*', route => route.fulfill({ json: {
    enabled: true, month: '2026-11', as_of: '2026-11-12', insights: ['Food is over its allocation.'],
  } }))
  const requests: { history: { content: string }[] }[] = []
  let releaseFirstReply!: () => void
  const firstReply = new Promise<void>(resolve => { releaseFirstReply = resolve })
  await page.route('**/api/v1/advisor/ask', async route => {
    requests.push(route.request().postDataJSON())
    if (requests.length === 1) await firstReply
    return route.fulfill({ json: { month: '2026-11', as_of: '2026-11-12', answer: 'Check food spending.',
      sources: [{ label: 'View budget', path: '/budget' }] } })
  })
  await seed(page, request, 'Advisor test')
  await page.goto('/')
  await page.getByRole('button', { name: 'Where could we reallocate money?' }).click()
  const outgoing = await page.locator('.sent').elementHandle()
  releaseFirstReply()
  await expect(page.locator('.pig-reply')).toContainText('Check food spending.')
  expect(await outgoing!.evaluate(el => el === document.querySelector('.sent'))).toBe(true)
  await page.getByLabel('Message Sir Pennington', { exact: true }).fill('How much?')
  await page.getByLabel('Message Sir Pennington', { exact: true }).press('Enter')
  await expect(page.locator('.pig-reply')).toHaveCount(2)
  expect(requests[1]?.history.map(t => t.content)).toEqual(['Where could we reallocate money?', 'Check food spending.'])
  expect(await page.locator('.advisor').evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true)
  await expect(page.getByRole('region', { name: 'Chat with Sir Pennington' })).toBeVisible()
  await expect(page.locator('.sent')).toHaveCount(2)
  await page.locator('.pig-chat').evaluate(el => Promise.all(el.getAnimations().map(a => a.finished)))
  const headerGeometry = () => page.evaluate(() => ['.app-header', '.chat-header'].map(selector => {
    const el = document.querySelector(selector)!
    const { y, height } = el.getBoundingClientRect()
    return [y, height]
  }))
  const headerAtRest = await headerGeometry()
  const newestIsVisible = () => page.locator('.pig-reply').last().evaluate(el => {
    const row = el.getBoundingClientRect()
    const log = el.parentElement!.getBoundingClientRect()
    return row.bottom <= log.bottom + 1 && row.bottom > log.top && row.top < log.bottom
  })
  const composerIsTouchable = () => page.locator('#advisor-question').evaluate(el => {
    const r = el.getBoundingClientRect()
    return document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2) === el
  })
  const layout = await page.locator('.pig-chat').evaluate(el => ({
    top: el.getBoundingClientRect().top,
    bottom: el.getBoundingClientRect().bottom,
    header: document.querySelector('.app-header')!.getBoundingClientRect().bottom,
    nav: document.querySelector('.mobile-nav')!.getBoundingClientRect().top,
  }))
  await expect(page.locator('.app-header')).toHaveCSS('position', 'fixed')
  await expect(page.locator('.mobile-nav')).toHaveCSS('bottom', '0px')
  expect(await page.locator('.mobile-nav').evaluate(el =>
    el.getBoundingClientRect().bottom === window.innerHeight && el.contains(document.elementFromPoint(10, window.innerHeight - 1)))).toBe(true)
  expect(layout.top - layout.header).toBeCloseTo(4, 0)
  expect(layout.nav - layout.bottom).toBeCloseTo(4, 0)
  await expect(page.getByRole('heading', { name: 'Sir Pennington', exact: true })).toBeVisible()
  // Sample the entire resize, including the first small change while the keyboard
  // is still below the navigation. A settled screenshot misses these jumps.
  await page.locator('#advisor-question').tap()
  const frames = await page.evaluate(async () => {
    const viewport = window.visualViewport!
    const rect = (s: string) => document.querySelector(s)!.getBoundingClientRect()
    const samples: { bottom: number, header: number, title: number, nav: number }[] = []
    async function sample(height: number, pan: number, count: number) {
      Object.defineProperty(viewport, 'height', { configurable: true, value: height })
      Object.defineProperty(viewport, 'offsetTop', { configurable: true, value: pan })
      viewport.dispatchEvent(new Event('resize'))
      for (let i = 0; i < count; i++) {
        await new Promise(requestAnimationFrame)
        samples.push({ bottom: rect('.pig-chat').bottom - pan, header: rect('.app-header').top - pan,
          title: rect('.chat-header').top - pan, nav: rect('.mobile-nav').top })
      }
    }
    await sample(770, 8, 2)
    await sample(480, 8, 24)
    await sample(800, 0, 24)
    Reflect.deleteProperty(viewport, 'height')
    Reflect.deleteProperty(viewport, 'offsetTop')
    viewport.dispatchEvent(new Event('resize'))
    return samples
  })
  for (const f of frames) {
    expect(f.header).toBe(headerAtRest[0]![0])
    expect(f.title).toBe(headerAtRest[1]![0])
    expect(f.nav).toBe(layout.nav)
  }
  expect(frames[25]!.bottom).toBe(480)
  expect(frames.slice(2, 25).some(f => f.bottom > 485 && f.bottom < layout.bottom - 10)).toBe(true)
  expect(frames.at(-1)!.bottom).toBeCloseTo(layout.bottom, 0)
  await expect(page.getByRole('button', { name: 'Clear conversation' })).toHaveCount(0)
  await page.screenshot({ path: '/tmp/pig-chat-mobile.png' })
  await page.getByLabel('Message Sir Pennington', { exact: true }).focus()
  await page.getByRole('button', { name: 'Close chat' }).tap()
  await expect(page.getByRole('heading', { name: 'Ask Sir Pennington' })).toBeFocused()
  const composer = page.getByRole('textbox', { name: 'Message Sir Pennington' })
  await page.locator('.advisor').evaluate(el => Promise.all(el.getAnimations().map(a => a.finished)))
  await page.evaluate(() => window.scrollTo(0, 90))
  const beforeTap = await page.evaluate(() => ({
    scroll: window.scrollY, input: document.querySelector('#advisor-question')!.getBoundingClientRect().top,
  }))
  await composer.tap()
  expect(await page.evaluate(() => window.scrollY)).toBe(beforeTap.scroll)
  expect(await composer.evaluate(el => el.getBoundingClientRect().top)).toBe(beforeTap.input)
  await expect(page.locator('.app-header')).toHaveCSS('position', 'fixed')
  await expect(page.locator('.mobile-nav')).toHaveCSS('bottom', '0px')
  await expect(composer).toBeFocused()
  await composer.fill('Can I stay on the dashboard?')
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible()
  await expect(page.locator('.pig-chat')).toHaveCount(0)
  expect(requests.length).toBe(2)
  // Model an overlay keyboard: layout viewport stays tall while its visible bottom moves.
  const headerTop = await page.locator('.app-header').evaluate(el => el.getBoundingClientRect().top)
  await page.evaluate(() => {
    Object.defineProperty(window.visualViewport!, 'height', { configurable: true, value: 480 })
    window.visualViewport!.dispatchEvent(new Event('resize'))
  })
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible()
  await expect(composer).toBeFocused()
  const cardBottom = () => page.locator('.advisor').evaluate(el => el.getBoundingClientRect().bottom)
  await expect.poll(cardBottom).toBeCloseTo(480, 0)
  expect(await composerIsTouchable()).toBe(true)
  await composer.blur()
  // Blur precedes the last keyboard frames. The navigation must stay covered
  // until the viewport recovers, even though the field has lost focus.
  await expect(page.locator('.mobile-nav')).toBeHidden()
  await expect(page.locator('.app-header')).toHaveCSS('position', 'fixed')
  await page.evaluate(() => {
    Reflect.deleteProperty(window.visualViewport!, 'height')
    window.visualViewport!.dispatchEvent(new Event('resize'))
  })
  await expect(page.locator('.mobile-nav')).toBeVisible()
  await composer.blur()
  await expect(page.locator('html')).not.toHaveClass(/chat-open/)
  await composer.tap()
  await expect(composer).toHaveValue('Can I stay on the dashboard?')
  // Exercise actual document scrolling alongside a large visual viewport pan.
  // WebKit can scroll the root to reveal a focused input even in a locked PWA.
  const forcedScroll = await page.addStyleTag({ content: 'html.chat-open{overflow-y:auto!important}html.chat-open body{height:1600px!important}' })
  await page.evaluate(() => {
    Object.defineProperty(window.visualViewport!, 'height', { configurable: true, value: 480 })
    window.visualViewport!.dispatchEvent(new Event('resize'))
    window.scrollTo(0, 600)
    Object.defineProperty(window.visualViewport!, 'offsetTop', { configurable: true, value: 256 })
    window.visualViewport!.dispatchEvent(new Event('scroll'))
  })
  expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(500)
  await expect.poll(cardBottom).toBeCloseTo(736, 0)
  const sharedHeaderTop = () => page.locator('.app-header').evaluate(el => el.getBoundingClientRect().top)
  expect(await sharedHeaderTop()).toBe(256)
  expect(await composerIsTouchable()).toBe(true)
  await expect(page.locator('.mobile-nav')).toBeHidden()
  await page.getByRole('button', { name: 'Ask', exact: true }).tap()
  await expect(page.locator('.pig-reply')).toHaveCount(3)
  await expect(composer).toBeFocused()
  await expect.poll(cardBottom).toBeCloseTo(736, 0)
  expect(await sharedHeaderTop()).toBe(256)
  expect(await composerIsTouchable()).toBe(true)
  await expect.poll(newestIsVisible).toBe(true)
  await page.evaluate(() => {
    window.scrollTo(0, 0)
    Reflect.deleteProperty(window.visualViewport!, 'offsetTop')
    window.visualViewport!.dispatchEvent(new Event('scroll'))
  })
  await forcedScroll.evaluate(el => el.remove())
  await expect.poll(() => composer.evaluate(el => el.getBoundingClientRect().bottom)).toBeLessThanOrEqual(480)
  expect(await composer.evaluate(el => el.getBoundingClientRect().bottom)).toBeGreaterThan(460)
  expect(await page.locator('.app-header').evaluate(el => el.getBoundingClientRect().top)).toBe(headerTop)
  expect(await headerGeometry()).toEqual(headerAtRest)
  await expect.poll(newestIsVisible).toBe(true)
  expect(await composerIsTouchable()).toBe(true)
  await expect.poll(() => page.locator('.transcript').evaluate(el => el.scrollHeight - el.scrollTop - el.clientHeight)).toBeLessThan(2)
  await expect(page.locator('.wordmark')).toBeInViewport({ ratio: 1 })
  await expect(composer).toBeInViewport({ ratio: 1 })
  await page.evaluate(() => { Reflect.deleteProperty(window.visualViewport!, 'height') })
  await page.setViewportSize({ width: 320, height: 480 })
  await expect.poll(() => composer.evaluate(el => el.getBoundingClientRect().bottom)).toBeLessThanOrEqual(480)
  expect(await composer.evaluate(el => el.getBoundingClientRect().bottom)).toBeGreaterThan(460)
  expect(await page.locator('.app-header').evaluate(el => el.getBoundingClientRect().top)).toBe(headerTop)
  expect(await headerGeometry()).toEqual(headerAtRest)
  await expect.poll(newestIsVisible).toBe(true)
  expect(await composerIsTouchable()).toBe(true)
  await composer.fill('What next?')
  await composer.press('Enter')
  await expect(page.locator('.pig-reply')).toHaveCount(4)
  const scroll = await page.locator('.transcript').evaluate(el => {
    el.scrollTo({ top: 0, behavior: 'instant' })
    el.scrollTop = 80
    window.scrollBy(0, 800)
    return { chat: el.scrollTop, page: window.scrollY }
  })
  expect(scroll.chat).toBeGreaterThan(0)
  expect(scroll.page).toBe(0)
  await expect.poll(() => headerGeometry()).toEqual(headerAtRest)
  expect(await composerIsTouchable()).toBe(true)
  await page.getByLabel('Message Sir Pennington', { exact: true }).press('Escape')
  await expect(page.getByRole('heading', { name: 'Ask Sir Pennington' })).toBeFocused()
  await page.setViewportSize({ width: 1440, height: 1000 })
  await expect.poll(() => page.locator('.advisor').evaluate(el => {
    const panel = el.getBoundingClientRect()
    const heading = document.querySelector('.page-heading')!.getBoundingClientRect()
    const metrics = document.querySelector('.metrics')!.getBoundingClientRect()
    return panel.top >= heading.bottom && panel.bottom <= metrics.top && Math.abs(panel.right - metrics.right) < 2
  })).toBe(true)
  expect(await page.locator('.advisor').evaluate(el => getComputedStyle(el).borderTopColor)).toBe(
    await page.locator('.wordmark svg').evaluate(el => getComputedStyle(el).color))
  await page.screenshot({ path: '/tmp/pig-chat-desktop.png' })
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.locator('.advisor li').first().tap()
  await expect(page.locator('.pig-reply')).toHaveCount(4)
  expect(await page.locator('.pig-chat').evaluate(el => el.getAnimations().length)).toBe(0)
  await expect.poll(newestIsVisible).toBe(true)
  await page.getByRole('link', { name: 'PigPen home' }).click()
  await expect(page.locator('.pig-chat')).toHaveCount(0)
  await page.getByRole('button', { name: 'Ask Sir Pennington', exact: true }).press('Enter')
  await page.reload()
  await expect(page.getByRole('textbox', { name: 'Message Sir Pennington' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Chat with Sir Pennington' })).toHaveCount(0)
  await page.waitForLoadState('networkidle')
  await context.setOffline(true)
  await expect(page.getByText('Reconnect to refresh insights or ask a question.')).toBeVisible()
})

test('the tapped frame grows around the mascot and only pulls outside the transcript refresh', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await seed(page, request, 'Chat gesture actor')
  await page.goto('/')
  await page.waitForLoadState('networkidle')
  const panel = page.locator('.advisor')
  const start = await panel.boundingBox()
  await panel.locator('.pig').tap()
  const motion = await panel.evaluate(async el => {
    const animation = el.getAnimations()[0]!
    animation.pause()
    const origin = el.querySelector('.pig')!
    const sample = (time: number) => {
      animation.currentTime = time
      const bounds = el.getBoundingClientRect()
      return { top: bounds.top, height: bounds.height, avatarHeight: origin.getBoundingClientRect().height }
    }
    const duration = Number(animation.effect!.getTiming().duration)
    const frames = [0, duration / 2, duration].map(sample)
    animation.finish()
    return frames
  })
  const [first, mid, end] = motion
  expect(first!.top).toBeCloseTo(start!.y, 0)
  expect(first!.height).toBeCloseTo(start!.height, 0)
  expect(mid!.height).toBeGreaterThan(first!.height + 10)
  expect(mid!.height).toBeLessThan(end!.height - 10)
  expect(mid!.avatarHeight).toBe(first!.avatarHeight)
  expect(end!.avatarHeight).toBe(first!.avatarHeight)
  const client = await page.context().newCDPSession(page)
  async function pull(selector: string) {
    const box = (await page.locator(selector).boundingBox())!
    const x = box.x + box.width / 2
    const y = box.y + 12
    await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] })
    for (const dy of [6, 20, 60, 110, 160]) {
      await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: y + dy }] })
    }
    await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  }
  let pulls = 0
  page.on('request', req => { if (req.url().includes('/sync/pull')) pulls++ })
  await pull('.transcript')
  await expect(page.locator('.pull-refresh')).not.toHaveClass(/active|refreshing/)
  expect(pulls).toBe(0)
  await pull('.chat-header')
  await expect.poll(() => pulls).toBe(1)
  await expect(page.locator('.pull-refresh')).not.toHaveClass(/refreshing/)
  await expect(page.locator('.chat-header')).toBeVisible()
  await pull('.app-header')
  await expect.poll(() => pulls).toBe(2)
  await expect(page.locator('.pig-chat')).toBeVisible()
})
