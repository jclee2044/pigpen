import { test,expect } from '@playwright/test'
import { seed } from './helpers'

test.beforeEach(async({page})=>{
 await page.addInitScript(()=>{
  const mock={calls:0,permission:'default' as NotificationPermission}
  Object.assign(window,{pushPromptTest:mock})
  Object.defineProperty(Notification,'permission',{get:()=>mock.permission})
  Object.defineProperty(Notification,'requestPermission',{value:async()=>{mock.calls++;mock.permission='denied';return 'denied'}})
 })
 await page.route('**/api/v1/push-config',route=>route.fulfill({json:{enabled:true,public_key:'BA'+'A'.repeat(85)}}))
})

test('first entry asks once, supports dismissal, and explains privacy in settings',async({page,request},info)=>{
 await seed(page,request,'Prompt dismissal')
 const prompt=page.getByRole('dialog',{name:'Enable notifications?'})
 await expect(prompt).toBeVisible()
 expect(await page.evaluate(()=>Reflect.get(window,'pushPromptTest').calls)).toBe(0)
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:844})
  const box=await prompt.boundingBox();expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(width)
  expect(Math.abs(box!.x+box!.width/2-width/2)).toBeLessThanOrEqual(1)
  expect(Math.abs(box!.y+box!.height/2-844/2)).toBeLessThanOrEqual(1)
 }
 await page.setViewportSize({width:390,height:844})
 await page.screenshot({path:info.outputPath('prompt-phone.png')})
 await page.getByRole('button',{name:'Not now',exact:true}).click()
 await page.reload();await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible()
 await expect(prompt).not.toBeVisible()
 await page.goto('/settings')
 const toggle=page.getByRole('switch',{name:'Push notifications',exact:true})
 await expect(toggle).toHaveAttribute('aria-describedby','push-privacy')
 await expect(page.locator('#push-privacy')).toContainText('Amounts, prices, balances, and other financial numbers are not included')
 await page.screenshot({path:info.outputPath('settings-phone.png')})
})

test('permission is requested only on Enable, denial remains dismissible',async({page,request})=>{
 await seed(page,request,'Prompt permission')
 await expect(page.getByRole('dialog',{name:'Enable notifications?'})).toBeVisible()
 await page.getByRole('button',{name:'Enable notifications',exact:true}).click()
 await expect(page.getByRole('alert')).toContainText('Notifications were not allowed')
 expect(await page.evaluate(()=>Reflect.get(window,'pushPromptTest').calls)).toBe(1)
 await page.keyboard.press('Escape')
 await expect(page.getByRole('dialog')).not.toBeVisible()
 await page.reload();await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible()
 await expect(page.getByRole('dialog')).not.toBeVisible()
})

test('existing permission is respected',async({page,request})=>{
 await page.addInitScript(()=>{Reflect.get(window,'pushPromptTest').permission='granted'})
 await seed(page,request,'Already allowed')
 await page.evaluate(async()=>{await navigator.serviceWorker.ready})
 await expect(page.getByRole('dialog')).not.toBeVisible()
 expect(await page.evaluate(()=>Reflect.get(window,'pushPromptTest').calls)).toBe(0)
})

test('iPhone installation guidance does not suppress the installed-app prompt',async({page,request})=>{
 await page.addInitScript(()=>{
  Object.defineProperty(navigator,'userAgent',{get:()=> 'iPhone'})
  Object.defineProperty(navigator,'standalone',{get:()=>sessionStorage.getItem('installed')==='yes'})
 })
 await seed(page,request,'iPhone entry')
 await expect(page.getByRole('dialog')).toContainText('Add to Home Screen')
 await expect(page.getByRole('button',{name:'Enable notifications',exact:true})).toHaveCount(0)
 await page.getByRole('button',{name:'Got it',exact:true}).click()
 await page.evaluate(()=>sessionStorage.setItem('installed','yes'))
 await page.reload()
 await expect(page.getByRole('dialog',{name:'Enable notifications?'})).toBeVisible()
 await expect(page.getByRole('button',{name:'Enable notifications',exact:true})).toBeEnabled()
})
