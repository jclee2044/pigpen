import {test,expect} from '@playwright/test'
import {seed,command} from './helpers'
import type {Wish} from '../../src/api/models'
test.use({viewport:{width:390,height:900},isMobile:true,hasTouch:true})
test('card tracks the finger, neighbors slide, and drop settles into the saved slot',async({page,request})=>{
 const actor=await seed(page,request,'Wish motion')
 const wishes:Wish[]=[]
 for(const name of ['Motion one','Motion two','Motion three'])wishes.push(await command(request,'wishlist.create',{name,price_minor:100},actor.id) as Wish)
 await page.goto('/wish-lists');await page.getByLabel('Wish-list owner').selectOption(actor.id)
 const handle=page.getByRole('button',{name:'Reorder Motion one',exact:true}),box=(await handle.boundingBox())!
 const slot=page.locator(`[data-sort-wish="${wishes[0]!.id}"]`),neighbor=page.locator(`[data-sort-wish="${wishes[1]!.id}"]`)
 const initial=(await slot.boundingBox())!,target=(await neighbor.boundingBox())!
 const x=box.x+20,y=box.y+20,session=await page.context().newCDPSession(page)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+12,y:y+10}]})
 const floating=page.locator('.wish-floating')
 await expect(floating).toBeVisible()
 await expect.poll(async()=>Math.round((await floating.boundingBox())!.y-initial.y)).toBe(10)
 expect(Math.round((await floating.boundingBox())!.x-initial.x)).toBe(12)
 await expect(page.locator('.refresh-host')).not.toHaveClass(/dragging|refreshing/)
 // Observe real transition frames, not just the final reordered DOM.
 await neighbor.evaluate(element=>{
  const samples:number[]=[]
  element.addEventListener('transitionrun',event=>{
   if((event as TransitionEvent).propertyName!=='transform')return
   const sample=()=>{samples.push(element.getBoundingClientRect().top);if(samples.length<10)requestAnimationFrame(sample)}
   requestAnimationFrame(sample)
  })
  ;(element as HTMLElement&{motionSamples:number[]}).motionSamples=samples
 })
 await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y+target.y-initial.y}]})
 await expect.poll(()=>neighbor.evaluate(element=>(element as HTMLElement&{motionSamples:number[]}).motionSamples.length)).toBeGreaterThan(3)
 const samples=await neighbor.evaluate(element=>(element as HTMLElement&{motionSamples:number[]}).motionSamples)
 expect(new Set(samples.map(value=>Math.round(value))).size).toBeGreaterThan(2)
 await page.screenshot({path:'../output/wish-motion/dragging.png',fullPage:true})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await session.detach()
 await expect(page.locator('.wish-settling')).toHaveCount(1)
 await expect(handle).toBeEnabled();await expect(floating).toHaveCount(0)
 await expect(page.locator('.wish-card h2')).toHaveText(['Motion two','Motion one','Motion three'])
 await page.reload();await page.getByLabel('Wish-list owner').selectOption(actor.id)
 await expect(page.locator('.wish-card h2')).toHaveText(['Motion two','Motion one','Motion three'])
 await page.emulateMedia({reducedMotion:'reduce'})
 await page.getByRole('button',{name:'Reorder Motion three',exact:true}).focus();await page.keyboard.press('ArrowUp')
 await expect(page.locator('.wish-card h2')).toHaveText(['Motion two','Motion three','Motion one'])
 expect(await neighbor.evaluate(element=>getComputedStyle(element).transitionDuration)).toBe('0s')
})
