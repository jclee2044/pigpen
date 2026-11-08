import {test,expect} from '@playwright/test'
import {seed,command} from './helpers'
import type {Wish} from '../../src/api/models'
test.use({viewport:{width:390,height:900},isMobile:true,hasTouch:true})
test('first overlap selects the slot and release clicks never open details',async({page,request})=>{
 const actor=await seed(page,request,'Overlap wishes')
 const wishes:Wish[]=[]
 for(const name of ['Overlap first','Overlap second','Overlap third'])wishes.push(await command(request,'wishlist.create',{name,price_minor:100},actor.id) as Wish)
 await page.goto('/wish-lists');await page.getByLabel('Wish-list owner').selectOption(actor.id)
 const handle=page.getByRole('button',{name:'Reorder Overlap first',exact:true}),press=(await handle.boundingBox())!
 const source=page.locator(`[data-sort-wish="${wishes[0]!.id}"]`),neighbor=page.locator(`[data-sort-wish="${wishes[1]!.id}"]`)
 const box=(await source.boundingBox())!,target=(await neighbor.boundingBox())!
 const x=press.x+20,y=press.y+20,delta=target.y-(box.y+box.height)+2
 const session=await page.context().newCDPSession(page)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y+delta}]})
 // Only two pixels of card overlap; the finger has not reached the other card.
 expect(y+delta).toBeLessThan(target.y)
 await expect.poll(()=>page.locator('[data-sort-wish]').evaluateAll(rows=>rows.map(row=>row.getAttribute('data-sort-wish')))).toEqual([wishes[1]!.id,wishes[0]!.id,wishes[2]!.id])
 // Keep moving in the same direction while the neighbor slides past: no swap-back.
 await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y+delta+3}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await session.detach()
 // Safari can retarget the compatibility click to a newly exposed title.
 await page.getByRole('button',{name:'Overlap second',exact:true}).dispatchEvent('click',{detail:1,clientX:x,clientY:y+delta})
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await expect(handle).toBeEnabled()
 await expect(page.locator('.wish-card h2')).toHaveText(['Overlap second','Overlap first','Overlap third'])
 await page.reload();await page.getByLabel('Wish-list owner').selectOption(actor.id)
 await expect(page.locator('.wish-card h2')).toHaveText(['Overlap second','Overlap first','Overlap third'])
 // A new, deliberate gesture still opens details immediately.
 await page.getByRole('button',{name:'Overlap first',exact:true}).tap();await expect(page.getByRole('dialog')).toBeVisible()
})
test('horizontal overlap reorders before the mouse reaches the target',async({page,request})=>{
 await page.setViewportSize({width:1280,height:900})
 const actor=await seed(page,request,'Overlap mouse')
 for(const name of ['Mouse first','Mouse second','Mouse third'])await command(request,'wishlist.create',{name,price_minor:100},actor.id)
 await page.goto('/wish-lists');await page.getByLabel('Wish-list owner').selectOption(actor.id)
 await expect(page.locator('.wish-card h2')).toHaveText(['Mouse first','Mouse second','Mouse third'])
 const source=page.locator('[data-sort-wish]').nth(0),neighbor=page.locator('[data-sort-wish]').nth(1)
 const box=(await source.boundingBox())!,target=(await neighbor.boundingBox())!,handle=page.getByRole('button',{name:'Reorder Mouse first',exact:true}),press=(await handle.boundingBox())!
 // Press on the left edge of the grip, then move only enough for card-edge contact.
 const x=press.x+2,y=press.y+20,delta=target.x-(box.x+box.width)+2
 expect(x+delta).toBeLessThan(target.x)
 await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+delta,y,{steps:4})
 await page.mouse.up()
 await page.getByRole('button',{name:'Mouse second',exact:true}).dispatchEvent('click',{detail:1,clientX:x+delta,clientY:y})
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await expect(handle).toBeEnabled()
 await expect(page.locator('.wish-card h2')).toHaveText(['Mouse second','Mouse first','Mouse third'])
 await page.getByRole('button',{name:'Mouse second',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible()
})
