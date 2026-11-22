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
  await page.getByLabel('Message Sir Pennysworth', { exact: true }).fill('How much?')
  await page.getByLabel('Message Sir Pennysworth', { exact: true }).press('Enter')
  await expect(page.locator('.pig-reply')).toHaveCount(2)
  expect(requests[1]?.history.map(t => t.content)).toEqual(['Where could we reallocate money?', 'Check food spending.'])
  expect(await page.locator('.advisor').evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true)
  await expect(page.getByRole('region', { name: 'Chat with Sir Pennysworth' })).toBeVisible()
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
  await expect(page.getByRole('heading', { name: 'Sir Pennysworth', exact: true })).toBeVisible()
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
  await page.getByLabel('Message Sir Pennysworth', { exact: true }).focus()
  await page.getByRole('button', { name: 'Close chat' }).tap()
  await expect(page.getByRole('heading', { name: 'Ask Sir Pennysworth' })).toBeFocused()
  const composer = page.getByRole('textbox', { name: 'Message Sir Pennysworth' })
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
  await expect.poll(cardBottom).toBeLessThanOrEqual(480)
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
  await expect.poll(cardBottom).toBeLessThanOrEqual(736)
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
  await page.getByLabel('Message Sir Pennysworth', { exact: true }).press('Escape')
  await expect(page.getByRole('heading', { name: 'Ask Sir Pennysworth' })).toBeFocused()
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
  await page.getByRole('button', { name: 'Ask Sir Pennysworth', exact: true }).press('Enter')
  await page.reload()
  await expect(page.getByRole('textbox', { name: 'Message Sir Pennysworth' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Chat with Sir Pennysworth' })).toHaveCount(0)
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

test('closing chat releases the dashboard even before the keyboard fully recovers', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.route('**/api/v1/advisor/insights?*', route => route.fulfill({ json: {
    enabled: true, month: '2026-11', as_of: '2026-11-12', insights: ['Synthetic budget insight.'],
  } }))
  await seed(page, request, 'Chat dismissal actor')
  await page.goto('/')
  for (const keyboard of [true, false, true]) {
    await page.getByRole('button', { name: 'Ask Sir Pennysworth', exact: true }).tap()
    await page.locator('.pig-chat').evaluate(el => Promise.all(el.getAnimations().map(a => a.finished)))
    if (keyboard) {
      await page.getByRole('textbox', { name: 'Message Sir Pennysworth' }).focus()
      await page.evaluate(() => {
        Object.defineProperty(window.visualViewport!, 'height', { configurable: true, value: 500 })
        window.visualViewport!.dispatchEvent(new Event('resize'))
      })
      await expect(page.locator('.mobile-nav')).toBeHidden()
    }
    await page.getByRole('button', { name: 'Close chat' }).tap()
    if (keyboard) {
      // Safari can finish keyboard dismissal a few pixels below the original
      // visible height. Closing chat must not wait for an exact height match.
      await page.evaluate(() => {
        Object.defineProperty(window.visualViewport!, 'height', { configurable: true, value: 840 })
        window.visualViewport!.dispatchEvent(new Event('resize'))
      })
    }
    await expect(page.locator('html')).not.toHaveClass(/chat-open|advisor-keyboard|advisor-awaiting-keyboard/)
    await expect(page.locator('.mobile-nav')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible()
    await page.locator('.advisor').evaluate(el => Promise.all(el.getAnimations().map(a => a.finished)))
    await page.getByRole('heading', { name: 'Recent purchases' }).scrollIntoViewIfNeeded()
    expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(0)
    await page.evaluate(() => {
      window.scrollTo(0, 0)
      Reflect.deleteProperty(window.visualViewport!, 'height')
      window.visualViewport!.dispatchEvent(new Event('resize'))
    })
  }
  await page.locator('.mobile-nav').getByRole('link', { name: 'Budget', exact: true }).tap()
  await expect(page).toHaveURL(/\/budget$/)
  await expect(page.locator('html')).not.toHaveClass(/chat-open|advisor-keyboard/)
})

test('dashboard drafting keeps the composer clear and restores Home after blur and refresh', async ({ page, request }) => {
  await page.setViewportSize({ width: 320, height: 844 })
  await page.route('**/api/v1/advisor/insights?*', route => route.fulfill({ json: {
    enabled: true, month: '2026-11', as_of: '2026-11-12',
    insights: ['Synthetic spending across household categories is below the monthly allocation.', 'Another longer synthetic insight about this month.'],
  } }))
  await seed(page, request, 'Dashboard draft actor')
  await page.goto('/')
  await page.addStyleTag({ content: ':root{--safe-area-top:47px}' })
  const input = page.getByRole('textbox', { name: 'Message Sir Pennysworth' })
  const initialGap = await page.locator('.advisor').evaluate(el => el.getBoundingClientRect().top - document.querySelector('.page-heading')!.getBoundingClientRect().bottom)
  await input.tap()
  await input.fill('Keep this draft')
  for (const height of [500, 380, 300]) {
    await page.evaluate(height => {
      Object.defineProperty(visualViewport!, 'height', { configurable: true, value: height })
      Object.defineProperty(visualViewport!, 'offsetTop', { configurable: true, value: 120 })
      visualViewport!.dispatchEvent(new Event('resize'))
    }, height)
    await expect.poll(() => page.locator('.advisor').evaluate(el => el.getBoundingClientRect().bottom)).toBeCloseTo(height + 120, 0)
    await expect.poll(() => input.evaluate(el => {
      const r = el.getBoundingClientRect()
      const summary = document.querySelector('.advisor-summary')!.getBoundingClientRect()
      const footer = document.querySelector('.advisor footer')!.getBoundingClientRect()
      return document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2) === el && summary.bottom <= footer.top + 1
    })).toBe(true)
  }
  await page.screenshot({ path: '/tmp/pigpen-dashboard-keyboard.png' })
  // Match the app's retry and pending-action notices above the dashboard. Their
  // content must remain scrollable without pushing the field under the keyboard.
  await page.evaluate(() => {
    for (const extra of ['error', 'pending-panel']) {
      const notice = document.createElement('section')
      notice.className = 'notice ' + extra
      notice.textContent = 'Synthetic connection retry or pending action notice. '.repeat(5)
      document.querySelector('main')!.prepend(notice)
    }
    visualViewport!.dispatchEvent(new Event('resize'))
  })
  await expect.poll(() => page.locator('.advisor').evaluate(el => el.getBoundingClientRect().bottom)).toBeCloseTo(420, 0)
  expect(await input.evaluate(el => {
    const r = el.getBoundingClientRect()
    return document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2) === el && r.bottom <= 420
  })).toBe(true)
  await input.blur()
  await page.evaluate(() => {
    Object.defineProperty(visualViewport!, 'height', { configurable: true, value: 836 })
    Object.defineProperty(visualViewport!, 'offsetTop', { configurable: true, value: 4 })
    visualViewport!.dispatchEvent(new Event('resize'))
  })
  await expect(page.locator('html')).not.toHaveClass(/chat-open|advisor-keyboard|advisor-awaiting-keyboard/)
  await expect(page.locator('.mobile-nav')).toBeVisible()
  await expect(input).toHaveValue('Keep this draft')
  expect(await page.locator('.advisor').evaluate(el => el.getBoundingClientRect().top - document.querySelector('.page-heading')!.getBoundingClientRect().bottom)).toBeCloseTo(initialGap, 0)
  await page.evaluate(() => {
    Reflect.deleteProperty(visualViewport!, 'height')
    Reflect.deleteProperty(visualViewport!, 'offsetTop')
    visualViewport!.dispatchEvent(new Event('resize'))
    window.scrollTo(0, 0)
  })
  // A missing final keyboard event must also release Home. Refocusing before
  // that fallback runs must keep the new editing session intact.
  await input.focus()
  await page.evaluate(() => {
    Object.defineProperty(visualViewport!, 'height', { configurable: true, value: 500 })
    visualViewport!.dispatchEvent(new Event('resize'))
  })
  await input.blur()
  await input.focus()
  await page.waitForTimeout(600)
  await expect(input).toBeFocused()
  await expect(page.locator('html')).toHaveClass(/advisor-keyboard/)
  await input.blur()
  await expect(page.locator('html')).not.toHaveClass(/chat-open|advisor-keyboard/)
  await expect(page.locator('.mobile-nav')).toBeVisible()
  await page.evaluate(() => {
    Reflect.deleteProperty(visualViewport!, 'height')
    visualViewport!.dispatchEvent(new Event('resize'))
    window.scrollTo(0, 0)
  })
  const client = await page.context().newCDPSession(page)
  const box = (await page.locator('.app-header').boundingBox())!
  const x = box.x + box.width / 2, y = box.y + 12
  await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] })
  for (const dy of [6, 20, 60, 110, 160]) await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: y + dy }] })
  await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await expect(page.locator('.pull-refresh')).not.toHaveClass(/active|refreshing/)
  await expect.poll(() => page.locator('.app-header').evaluate(el => el.getBoundingClientRect().top)).toBe(0)
  await page.getByRole('heading', { name: 'Recent purchases' }).scrollIntoViewIfNeeded()
  expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(0)
  await page.locator('.mobile-nav').getByRole('link', { name: 'Budget', exact: true }).tap()
  await expect(page).toHaveURL(/\/budget$/)
})

test('prompt buttons cannot paint over the dashboard composer during keyboard motion', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.route('**/api/v1/advisor/insights?*', route => route.fulfill({ json: {
    enabled: true, month: '2026-11', as_of: '2026-11-12',
    insights: ['A longer synthetic budget insight that wraps across several lines on a phone.', 'Another synthetic insight about spending this month.'],
  } }))
  await seed(page, request, 'Prompt overlap actor')
  await page.goto('/')
  const input = page.locator('#advisor-question')
  await input.tap()
  const overlaps = await page.evaluate(async () => {
    const viewport = visualViewport!
    const summary = document.querySelector<HTMLElement>('.advisor-summary')!
    const input = document.querySelector<HTMLInputElement>('#advisor-question')!
    const footer = input.closest('footer')!
    const overlaps: string[] = []
    for (const height of [720, 480, 340, 480, 836]) {
      Object.defineProperty(viewport, 'height', { configurable: true, value: height })
      viewport.dispatchEvent(new Event('resize'))
      for (let frame = 0; frame < 14; frame++) {
        await new Promise(requestAnimationFrame)
        // Show the last prompt right at the scroll area's lower edge.
        summary.scrollTop = summary.scrollHeight
        const r = input.getBoundingClientRect()
        if (r.bottom > height || r.top < document.querySelector('.app-header')!.getBoundingClientRect().bottom) continue
        for (const x of [r.left + 8, r.left + r.width / 2, r.right - 8]) {
          for (const y of [r.top + 2, r.top + r.height / 2, r.bottom - 2]) {
            const top = document.elementFromPoint(x, y)
            if (!top || !footer.contains(top)) overlaps.push(`${height}:${frame}:${top?.tagName}`)
          }
        }
      }
    }
    return overlaps
  })
  expect(overlaps).toEqual([])
  await page.screenshot({ path: '/tmp/pigpen-prompt-overlap.png' })
  await input.blur()
  await expect(page.locator('html')).not.toHaveClass(/advisor-keyboard|chat-open/)
  await expect(page.getByRole('link', { name: 'Review past analyses' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Where could we reallocate money?' })).toBeVisible()
  await page.getByRole('button', { name: 'Where could we reallocate money?' }).click()
  await expect(page.locator('.pig-chat')).toBeVisible()
})

test('focused dashboard refresh moves the header and page together like ordinary refresh', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.route('**/api/v1/advisor/insights?*', route => route.fulfill({ json: {
    enabled: true, month: '2026-11', as_of: '2026-11-12', insights: ['Synthetic budget insight.'],
  } }))
  await seed(page, request, 'Keyboard refresh actor')
  await page.goto('/')
  await page.addStyleTag({ content: ':root{--safe-area-top:47px}' })
  await page.locator('#advisor-question').tap()
  await page.evaluate(() => {
    Object.defineProperty(visualViewport!, 'height', { configurable: true, value: 480 })
    Object.defineProperty(visualViewport!, 'offsetTop', { configurable: true, value: 100 })
    visualViewport!.dispatchEvent(new Event('resize'))
  })
  await expect(page.locator('html')).toHaveClass(/advisor-keyboard/)
  const client = await page.context().newCDPSession(page)
  const box = (await page.locator('.app-header').boundingBox())!
  const contentTop = await page.locator('.refresh-content').evaluate(el => el.getBoundingClientRect().top)
  const x = box.x + box.width / 2, y = box.y + 12
  let pulls = 0
  page.on('request', req => { if (req.url().includes('/sync/pull')) pulls++ })
  await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] })
  for (const dy of [6, 20, 60, 110, 160]) {
    await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: y + dy }] })
    await page.evaluate(() => new Promise(requestAnimationFrame))
    const geometry = await page.evaluate(() => {
      const header = document.querySelector('.app-header')!.getBoundingClientRect()
      const pull = document.querySelector('.pull-refresh')!
      return { headerTop: header.top, contentTop: document.querySelector('.refresh-content')!.getBoundingClientRect().top,
        distance: parseFloat(document.querySelector<HTMLElement>('.refresh-host')!.style.getPropertyValue('--pull-distance')),
        backdrop: getComputedStyle(document.querySelector('.refresh-host')!).backgroundColor,
        headerColor: getComputedStyle(document.querySelector('.app-header')!).backgroundColor,
        pullBottom: pull.getBoundingClientRect().bottom,
        active: pull.classList.contains('active') }
    })
    expect(geometry.headerTop - box.y).toBeCloseTo(geometry.distance, 0)
    expect(geometry.contentTop - contentTop).toBeCloseTo(geometry.distance, 0)
    expect(geometry.backdrop).toBe(geometry.headerColor)
    if (geometry.active) expect(geometry.pullBottom).toBeCloseTo(geometry.headerTop + 47, 0)
  }
  await page.screenshot({ path: '/tmp/pigpen-keyboard-refresh.png' })
  await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  const returnOffsets = await page.evaluate(async () => {
    const samples: number[] = []
    for (let frame = 0; frame < 60; frame++) {
      await new Promise(requestAnimationFrame)
      samples.push(document.querySelector('.app-header')!.getBoundingClientRect().top -
        document.querySelector('.refresh-content')!.getBoundingClientRect().top)
    }
    return samples
  })
  for (const offset of returnOffsets) expect(offset).toBeCloseTo(box.y - contentTop, 0)
  await expect.poll(() => pulls).toBe(1)
  await expect(page.locator('.pull-refresh')).not.toHaveClass(/active|refreshing/)
  await expect.poll(() => page.locator('.app-header').evaluate(el => el.getBoundingClientRect().top)).toBeCloseTo(box.y, 0)
  await expect.poll(() => page.locator('.refresh-content').evaluate(el => el.getBoundingClientRect().top)).toBeCloseTo(contentTop, 0)
  await expect(page.locator('#advisor-question')).toBeFocused()
  await page.locator('#advisor-question').blur()
  await page.evaluate(() => {
    Reflect.deleteProperty(visualViewport!, 'height')
    Reflect.deleteProperty(visualViewport!, 'offsetTop')
    visualViewport!.dispatchEvent(new Event('resize'))
  })
  await expect(page.locator('html')).not.toHaveClass(/chat-open|advisor-keyboard/)
  await expect(page.locator('.mobile-nav')).toBeVisible()
  await page.locator('.mobile-nav').getByRole('link', { name: 'Budget', exact: true }).tap()
  await expect(page).toHaveURL(/\/budget$/)
})

test('dashboard focus preserves the card and starts keyboard scrolling at the previous position', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.route('**/api/v1/advisor/insights?*', route => route.fulfill({ json: {
    enabled: true, month: '2026-11', as_of: '2026-11-12',
    insights: ['Synthetic budget insight. '.repeat(5), 'Another monthly insight. '.repeat(3)],
  } }))
  await seed(page, request, 'Scroll origin actor')
  await page.goto('/')
  const input = page.locator('#advisor-question')
  await input.waitFor({ state: 'visible' })
  for (const originalScroll of [0, 100]) {
    await page.evaluate(top => window.scrollTo(0, top), originalScroll)
    const before = await page.locator('.advisor').boundingBox()
    await input.tap()
    expect(await page.locator('.advisor').boundingBox()).toEqual(before)
    const start = await page.evaluate(() => {
      Object.defineProperty(visualViewport!, 'height', { configurable: true, value: 480 })
      visualViewport!.dispatchEvent(new Event('resize'))
      const card = document.querySelector('.advisor')!.getBoundingClientRect()
      return { top: card.top, height: card.height, width: card.width }
    })
    expect(start.top).toBeCloseTo(before!.y, 0)
    expect(start.height).toBeCloseTo(before!.height, 0)
    expect(start.width).toBeCloseTo(before!.width, 0)
    const animation = await page.evaluate(async () => {
      const samples: { top: number, height: number }[] = []
      for (let frame = 0; frame < 20; frame++) {
        await new Promise(requestAnimationFrame)
        const card = document.querySelector('.advisor')!.getBoundingClientRect()
        samples.push({ top: card.top, height: card.height })
      }
      return samples
    })
    for (const sample of animation) expect(sample.height).toBeCloseTo(before!.height, 0)
    await expect.poll(() => page.locator('.advisor').evaluate(el => el.getBoundingClientRect().top - document.querySelector('.app-header')!.getBoundingClientRect().bottom)).toBeCloseTo(16, 0)
    const finalTop = (await page.locator('.advisor').boundingBox())!.y
    expect(animation.some(sample => sample.top > Math.min(start.top, finalTop) + 1 && sample.top < Math.max(start.top, finalTop) - 1)).toBe(true)
    expect((await page.locator('.advisor').boundingBox())!.height).toBeCloseTo(before!.height, 0)
    await page.screenshot({ path: '/tmp/pigpen-natural-draft-card.png' })
    await input.blur()
    await page.evaluate(() => {
      Reflect.deleteProperty(visualViewport!, 'height')
      visualViewport!.dispatchEvent(new Event('resize'))
    })
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(originalScroll)
    await expect(page.locator('.mobile-nav')).toBeVisible()
  }
})
