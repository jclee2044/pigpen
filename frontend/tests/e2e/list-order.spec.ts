import {test,expect} from '@playwright/test'
import {seed,command} from './helpers'
import type {Snapshot} from '../../src/api/models'
test.use({viewport:{width:390,height:844},isMobile:true,hasTouch:true})
test('newest purchases and approvals first; touch and keyboard wish order persists',async({page,request})=>{
 const actor=await seed(page,request,'List ordering')
 const snapshot=await(await request.get('/api/v1/sync/snapshot')).json() as Snapshot
 const category=snapshot.records.categories.find(c=>c.name==='Food')!
 for(const [item,date] of [['Old purchase','2024-02-02'],['Newest purchase','2024-02-20'],['Backdated purchase','2024-02-01'],['Newest same day','2024-02-20']]){
  await command(request,'purchase.create',{item:item!,transaction_date:date!,amount_minor:100,category_id:category.id},actor.id)
 }
 await page.evaluate(()=>localStorage.setItem('pigpen-month','2024-02'));await page.goto('/purchases')
 await expect(page.locator('.purchase-title')).toHaveText(['Newest same day','Newest purchase','Old purchase','Backdated purchase'])
 for(const item of ['Old request','New request'])await command(request,'request.create',{item,amount_minor:100},actor.id)
 await page.goto('/approvals')
 await expect(page.locator('.request-card h2')).toHaveText(['New request','Old request'])
 for(const name of ['First wish','Second wish','Third wish'])await command(request,'wishlist.create',{name,price_minor:100},actor.id)
 await page.goto('/wish-lists')
 const titles=page.locator('.wish-card h2')
 await expect(titles).toHaveText(['First wish','Second wish','Third wish'])
 const handle=page.getByRole('button',{name:'Reorder First wish',exact:true})
 const box=(await handle.boundingBox())!,target=(await page.locator('[data-sort-wish]').nth(1).boundingBox())!
 const x=box.x+box.width/2,y=box.y+box.height/2
 const session=await page.context().newCDPSession(page)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
 // Move into the lower half of the second item and drop.
 await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:target.y+target.height*.8}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await session.detach()
 await expect(titles).toHaveText(['Second wish','First wish','Third wish'])
 await expect(page.getByRole('button',{name:'Reorder First wish',exact:true})).toBeEnabled()
 await page.reload();await expect(titles).toHaveText(['Second wish','First wish','Third wish'])
 await page.getByRole('button',{name:'Reorder Third wish',exact:true}).focus();await page.keyboard.press('ArrowUp')
 await expect(titles).toHaveText(['Second wish','Third wish','First wish'])
 await expect(page.getByRole('button',{name:'Reorder First wish',exact:true})).toBeEnabled()
 await page.reload();await expect(titles).toHaveText(['Second wish','Third wish','First wish'])
 await page.screenshot({path:'../output/list-order/mobile.png',fullPage:true})
})
