import { test,expect,type Page } from '@playwright/test'
import { seed,command } from './helpers'
import type { Wish } from '../../src/api/models'
test.use({viewport:{width:390,height:844},isMobile:true,hasTouch:true})
async function swipe(page:Page,item:string,dx:number,dy=0){
 const card=page.getByRole('button',{name:item,exact:true})
 await card.scrollIntoViewIfNeeded()
 const box=(await card.locator('xpath=ancestor::*[contains(@class,"wish-surface")]').boundingBox())!
 const x=box.x+box.width*.75,y=box.y+box.height/2
 const session=await page.context().newCDPSession(page)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
 for(let step=1;step<=8;step++)await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+dx*step/8,y:y+dy*step/8}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await session.detach()
}

test('wish swipe asks before deleting, cancels, and retries an interrupted response safely',async({page,request})=>{
 const owner=await seed(page,request,'Wish swipe owner')
 const wish=await command(request,'wishlist.create',{name:'Swipe wish',price_minor:1234,description:'A special wish'},owner.id) as Wish
 await page.goto('/wish-lists')
 const remove=page.getByRole('button',{name:'Delete Swipe wish',exact:true})
 await swipe(page,'Swipe wish',-20)
 await expect(remove).toBeHidden()
 await swipe(page,'Swipe wish',-100)
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await expect(remove).toBeVisible()
 await swipe(page,'Swipe wish',100)
 await expect(remove).toBeHidden()
 await swipe(page,'Swipe wish',-100)
 await remove.tap()
 await expect(page.getByRole('dialog')).toContainText('Delete “Swipe wish” from the wish list?')
 await page.getByRole('button',{name:'Cancel',exact:true}).tap()
 expect((await (await request.get('/api/v1/wishlist-items')).json()).items.some((x:Wish)=>x.id===wish.id)).toBe(true)
 await swipe(page,'Swipe wish',0,-60)
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await swipe(page,'Swipe wish',-100)
 await remove.tap()
 await page.screenshot({path:'../output/wishlist-delete/confirmation.png'})
 const ids:string[]=[]
 await page.route('**/api/v1/operations',async route=>{
  const op=route.request().postDataJSON()
  if(op.kind!=='wishlist.delete'){await route.continue();return}
  ids.push(op.operation_id)
  if(ids.length===1){await route.fetch();await route.fulfill({status:503,json:{error:{message:'Response interrupted'}}})}
  else await route.continue()
 })
 await page.getByRole('button',{name:'Delete wish',exact:true}).tap()
 await expect(page.getByRole('alert')).toContainText('saved on this device')
 await page.getByRole('button',{name:'Retry saved submission',exact:true}).tap()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await expect(page.getByRole('button',{name:'Swipe wish',exact:true})).toHaveCount(0)
 expect(ids).toHaveLength(2);expect(ids[0]).toBe(ids[1])
 expect((await (await request.get('/api/v1/wishlist-items')).json()).items.some((x:Wish)=>x.id===wish.id)).toBe(false)
})

test('detail offers keyboard deletion and other profiles cannot reveal delete',async({page,request})=>{
 const owner=await seed(page,request,'Wish access owner')
 await command(request,'wishlist.create',{name:'Keyboard wish',price_minor:500},owner.id)
 await page.goto('/wish-lists')
 const card=page.getByRole('button',{name:'Keyboard wish',exact:true})
 await card.focus();await page.keyboard.press('Enter')
 await page.getByRole('button',{name:'Delete wish',exact:true}).tap()
 await expect(page.getByRole('dialog')).toContainText('Delete “Keyboard wish”')
 await page.keyboard.press('Escape')
 await seed(page,request,'Other wish viewer')
 await page.goto('/wish-lists')
 await swipe(page,'Keyboard wish',-100)
 await expect(page.getByRole('button',{name:'Delete Keyboard wish',exact:true})).toHaveCount(0)
 await card.tap()
 await expect(page.getByRole('dialog')).toBeVisible()
 await expect(page.getByRole('button',{name:'Delete wish',exact:true})).toHaveCount(0)
})
