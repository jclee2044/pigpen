import {test,expect} from '@playwright/test'
import {seed,command} from './helpers'
test.use({viewport:{width:390,height:900},isMobile:true,hasTouch:true})
test('reorder grip follows the card through partial swipe, reveal and close',async({page,request})=>{
 const actor=await seed(page,request,'Swipe grip')
 await command(request,'wishlist.create',{name:'Swipe with grip',price_minor:100},actor.id)
 await page.goto('/wish-lists');await page.getByLabel('Wish-list owner').selectOption(actor.id)
 await expect(page.locator('.wish-card')).toHaveCount(1)
 const card=page.locator('.wish-card'),handle=page.getByRole('button',{name:'Reorder Swipe with grip',exact:true})
 const start=(await card.boundingBox())!,grip=(await handle.boundingBox())!,x=start.x+start.width*.6,y=start.y+start.height*.65
 const session=await page.context().newCDPSession(page)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
 for(const dx of [-15,-35,-60,-85]){
  await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+dx,y}]})
  await expect.poll(async()=>Math.round((await card.boundingBox())!.x-start.x)).toBe(dx)
  expect(Math.round((await handle.boundingBox())!.x-grip.x)).toBe(dx)
 }
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await session.detach()
 await expect(page.getByRole('button',{name:'Delete Swipe with grip',exact:true})).toBeVisible()
 await expect.poll(async()=>Math.round((await handle.boundingBox())!.x-grip.x)).toBe(-88)
 await page.getByRole('button',{name:'Swipe with grip',exact:true}).tap()
 await expect.poll(async()=>Math.round((await handle.boundingBox())!.x-grip.x)).toBe(0)
 await expect(page.getByRole('dialog')).toHaveCount(0)
 // Left Arrow on the grip is reordering, not a request to reveal Delete.
 await handle.focus();await page.keyboard.press('ArrowLeft')
 await expect(page.getByRole('button',{name:'Delete Swipe with grip',exact:true})).toBeHidden()
})
