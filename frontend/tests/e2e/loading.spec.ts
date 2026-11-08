import {test,expect} from '@playwright/test'
import {seed} from './helpers'
test('centered thinking pig and pull refresh wheel respect reduced motion',async({page,request},info)=>{
 await page.setViewportSize({width:390,height:844})
 let release!:()=>void
 let gate=new Promise<void>(resolve=>{release=resolve})
 await page.route('**/api/v1/sync/snapshot',async route=>{await gate;await route.continue()})
 await page.goto('/')
 const startup=page.getByRole('status').filter({hasText:'Loading PigPen…'})
 await expect(startup).toBeVisible()
 await expect(startup.locator('img')).toHaveJSProperty('complete',true)
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:844})
  const box=await startup.boundingBox()
  expect(Math.abs(box!.x+box!.width/2-width/2)).toBeLessThan(2)
  expect(Math.abs(box!.y+box!.height/2-422)).toBeLessThan(2)
 }
 await page.setViewportSize({width:390,height:844})
 await page.screenshot({path:info.outputPath('startup.png')})
 await page.emulateMedia({reducedMotion:'reduce'})
 await expect(startup.locator('img')).toHaveCSS('animation-name','none')
 release();await expect(startup).toHaveCount(0);await page.unroute('**/api/v1/sync/snapshot')
 await seed(page,request,'Thinking pig actor')
 await page.goto('/wish-lists');await page.getByRole('button',{name:'Add wish'}).click()
 await page.getByLabel('Wish name').fill('Loading test wish')
 await page.getByLabel('Price ($)',{exact:true}).fill('12')
 gate=new Promise<void>(resolve=>{release=resolve})
 await page.route('**/api/v1/operations',async route=>{await gate;await route.continue()})
 await page.getByRole('button',{name:'Save wish',exact:true}).click()
 await expect(page.getByRole('dialog').getByRole('status')).toHaveText('Saving…')
 await expect(page.getByRole('dialog').locator('.app-loading')).toHaveCSS('align-items','center')
 await page.screenshot({path:info.outputPath('saving.png')})
 release();await expect(page.getByRole('dialog')).toHaveCount(0)
 await page.unroute('**/api/v1/operations')
 gate=new Promise<void>(resolve=>{release=resolve})
 await page.route('**/api/v1/sync/pull?**',async route=>{await gate;await route.continue()})
 await page.evaluate(()=>{
  const el=document.querySelector('main')!
  for(const [type,y] of [['touchstart',220],['touchmove',400],['touchend',400]] as const){
   const t=new Touch({identifier:1,target:el,clientX:180,clientY:y})
   el.dispatchEvent(new TouchEvent(type,{bubbles:true,cancelable:true,touches:type==='touchend'?[]:[t],changedTouches:[t]}))
  }
 })
 const pull=page.locator('.pull-refresh')
 await expect(pull).toHaveText('Syncing…')
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:844})
  for(const theme of ['light','dark']){
   await page.evaluate(t=>document.documentElement.dataset.theme=t,theme)
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
   await expect(pull.locator('.refresh-wheel')).toBeVisible()
   await expect(pull.locator('img')).toHaveCount(0)
  }
 }
 await page.setViewportSize({width:390,height:844})
 await page.screenshot({path:info.outputPath('refresh-dark.png')})
 release();await expect(page.locator('.pull-refresh')).not.toHaveClass(/refreshing/)
})
