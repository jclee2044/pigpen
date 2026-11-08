import {writeFileSync} from 'node:fs'
import {test,expect} from '@playwright/test'
import {seed,command} from './helpers'
import type {Wish} from '../../src/api/models'
declare global {interface Window {wishDropFrames:{y:number;height:number;anchor:number;panel:boolean}[]}}
for(const mobile of [true,false])test.describe(mobile?'touch scroll stability':'desktop scroll stability',()=>{
 test.use({viewport:{width:mobile?390:1280,height:900},isMobile:mobile,hasTouch:mobile})
 test('scrolled list stays in place through drop settlement and slow save',async({page,request})=>{
  const actor=await seed(page,request,mobile?'Scroll touch':'Scroll mouse')
  const wishes:Wish[]=[]
  for(let i=0;i<14;i++)wishes.push(await command(request,'wishlist.create',{name:`Scroll wish ${i}`,price_minor:100},actor.id) as Wish)
  await page.goto('/wish-lists');await page.getByLabel('Wish-list owner').selectOption(actor.id)
  await expect(page.locator('.wish-card')).toHaveCount(14);await expect(page.locator('.pending-panel')).toHaveCount(0)
  const source=page.locator(`[data-sort-wish="${wishes[4]!.id}"]`),target=page.locator(`[data-sort-wish="${wishes[5]!.id}"]`)
  await source.evaluate(element=>window.scrollTo(0,window.scrollY+element.getBoundingClientRect().top-350))
  const box=(await source.boundingBox())!,destination=(await target.boundingBox())!,handle=page.getByRole('button',{name:'Reorder Scroll wish 4',exact:true}),press=(await handle.boundingBox())!
  const x=press.x+10,y=press.y+20,endX=x+destination.x-box.x,endY=y+destination.y-box.y
  await page.route('**/api/v1/operations',async route=>{
   if(route.request().postDataJSON().kind==='wishlist.reorder')await new Promise(resolve=>setTimeout(resolve,600))
   await route.continue()
  })
  if(mobile){
   const session=await page.context().newCDPSession(page)
   await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
   await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:endX,y:endY}]})
   await page.evaluate(id=>{
    window.wishDropFrames=[];const start=performance.now()
    const sample=()=>{window.wishDropFrames.push({y:scrollY,height:document.documentElement.scrollHeight,anchor:document.querySelector(`[data-sort-wish="${id}"]`)!.getBoundingClientRect().top,panel:!!document.querySelector('.pending-panel')});if(performance.now()-start<1300)requestAnimationFrame(sample)}
    requestAnimationFrame(sample)
   },wishes[10]!.id)
   await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await session.detach()
  }else{
   await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(endX,endY,{steps:12})
   await page.evaluate(id=>{
    window.wishDropFrames=[];const start=performance.now()
    const sample=()=>{window.wishDropFrames.push({y:scrollY,height:document.documentElement.scrollHeight,anchor:document.querySelector(`[data-sort-wish="${id}"]`)!.getBoundingClientRect().top,panel:!!document.querySelector('.pending-panel')});if(performance.now()-start<1300)requestAnimationFrame(sample)}
    requestAnimationFrame(sample)
   },wishes[10]!.id)
   await page.mouse.up()
  }
  await expect(handle).toBeEnabled();await page.waitForTimeout(350)
  const frames=await page.evaluate(()=>window.wishDropFrames)
  expect(frames.length).toBeGreaterThan(10)
  const range=(key:'y'|'height'|'anchor')=>Math.max(...frames.map(frame=>frame[key]))-Math.min(...frames.map(frame=>frame[key]))
  const metrics={frames,scrollRange:range('y'),heightRange:range('height'),anchorRange:range('anchor')}
  writeFileSync(`../output/wish-scroll/${mobile?'touch':'desktop'}-metrics.json`,JSON.stringify(metrics,null,2))
  await test.info().attach('scroll-frames',{body:JSON.stringify(metrics),contentType:'application/json'})
  expect(range('y'),'scroll offset must not jump during save').toBeLessThan(2)
  expect(range('height'),'document height must stay stable').toBeLessThan(2)
  expect(range('anchor'),'unmoved card must stay at the same viewport position').toBeLessThan(2)
  expect(frames.some(frame=>frame.panel),'ordinary in-flight save must not insert a pending notice').toBe(false)
  await expect(page.getByRole('dialog')).toHaveCount(0)
 })
})

test('an uncertain reorder still shows its durable pending action and can retry',async({page,request})=>{
 const actor=await seed(page,request,'Scroll failure')
 for(const name of ['Failure one','Failure two'])await command(request,'wishlist.create',{name,price_minor:100},actor.id)
 await page.goto('/wish-lists');await page.getByLabel('Wish-list owner').selectOption(actor.id)
 let interrupted=false
 await page.route('**/api/v1/operations',async route=>{
  if(route.request().postDataJSON().kind==='wishlist.reorder'&&!interrupted){interrupted=true;await route.fetch();return route.fulfill({status:503,json:{error:{message:'Response interrupted'}}})}
  return route.continue()
 })
 await page.getByRole('button',{name:'Reorder Failure one',exact:true}).focus();await page.keyboard.press('ArrowDown')
 await expect(page.locator('.pending-panel')).toBeVisible()
 await page.locator('.pending-panel summary').click()
 await page.locator('.pending-panel').getByRole('button',{name:'Retry saved action',exact:true}).click()
 await expect(page.locator('.pending-panel')).toHaveCount(0)
 await expect(page.locator('.wish-card h2')).toHaveText(['Failure two','Failure one'])
})
