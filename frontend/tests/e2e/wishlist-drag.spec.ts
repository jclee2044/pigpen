import {test,expect,type Page} from '@playwright/test'
import {seed,command} from './helpers'
async function setup(page:Page,request:Parameters<typeof seed>[1],label:string){
 const actor=await seed(page,request,label)
 for(const name of ['One','Two','Three'])await command(request,'wishlist.create',{name,price_minor:100},actor.id)
 await page.goto('/wish-lists');await page.getByLabel('Wish-list owner').selectOption(actor.id);await expect(page.locator('.sortable-wish:has(.wish-drag-handle) .wish-card h2')).toHaveText(['One','Two','Three'])
 return actor
}
const titles=(page:Page)=>page.locator('.sortable-wish:has(.wish-drag-handle) .wish-card h2')
test.describe('touch wish dragging',()=>{
 test.use({viewport:{width:390,height:844},isMobile:true,hasTouch:true})
 test('continuous dragging keeps capture, skips refresh, saves and cancels',async({page,request})=>{
  const actor=await setup(page,request,'Continuous wish touch')
  async function drag(name:string,targetIndex:number){
   const handle=page.getByRole('button',{name:'Reorder '+name,exact:true})
   await handle.scrollIntoViewIfNeeded()
   const start=(await handle.boundingBox())!,target=(await page.locator('[data-sort-wish]:has(.wish-drag-handle)').nth(targetIndex).boundingBox())!
   const slot=(await handle.locator('xpath=ancestor::*[@data-sort-wish]').boundingBox())!
   const x=start.x+start.width/2,y=start.y+start.height/2,end=y+target.y-slot.y
   const session=await page.context().newCDPSession(page)
   await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
   for(let step=1;step<=16;step++){
    await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y+(end-y)*step/16}]})
    await page.waitForTimeout(25)
    await expect(page.locator('.sortable-wish.dragging')).toHaveCount(1)
    await expect(page.locator('.refresh-host')).not.toHaveClass(/dragging|refreshing/)
   }
   await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await session.detach()
   await expect(handle).toBeEnabled()
  }
  await drag('One',1);await expect(titles(page)).toHaveText(['Two','One','Three'])
  await page.reload();await page.getByLabel('Wish-list owner').selectOption(actor.id);await expect(titles(page)).toHaveText(['Two','One','Three'])
  await drag('One',0);await expect(titles(page)).toHaveText(['One','Two','Three'])
  await page.reload();await page.getByLabel('Wish-list owner').selectOption(actor.id);await expect(titles(page)).toHaveText(['One','Two','Three'])
  await expect(page.locator('.wish-card .pill')).toHaveCount(0)
  const box=(await page.getByRole('button',{name:'Reorder One',exact:true}).boundingBox())!
  const session=await page.context().newCDPSession(page)
  await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:box.x+20,y:box.y+20}]})
  await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:box.x+20,y:box.y+240}]})
  await session.send('Input.dispatchTouchEvent',{type:'touchCancel',touchPoints:[]});await session.detach()
  await expect(titles(page)).toHaveText(['One','Two','Three'])
 })
})
test('desktop continuous drag saves and details still open',async({page,request})=>{
 await page.setViewportSize({width:1280,height:900});const actor=await setup(page,request,'Continuous wish mouse')
 const handle=page.getByRole('button',{name:'Reorder One',exact:true}),start=(await handle.boundingBox())!,target=(await page.locator('[data-sort-wish]:has(.wish-drag-handle)').nth(1).boundingBox())!
 const slot=(await handle.locator('xpath=ancestor::*[@data-sort-wish]').boundingBox())!
 await page.mouse.move(start.x+20,start.y+20);await page.mouse.down()
 await page.mouse.move(start.x+20+target.x-slot.x,start.y+20+target.y-slot.y,{steps:24})
 await expect(page.locator('.sortable-wish.dragging')).toHaveCount(1)
 await page.mouse.up();await expect(handle).toBeEnabled()
 await expect(titles(page)).toHaveText(['Two','One','Three'])
 await page.reload();await page.getByLabel('Wish-list owner').selectOption(actor.id);await expect(titles(page)).toHaveText(['Two','One','Three'])
 await expect(page.locator('.wish-card .pill')).toHaveCount(0)
 await page.locator('.sortable-wish:has(.wish-drag-handle)').getByRole('button',{name:'One',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible()
})
