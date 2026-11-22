import {test,expect,type Page} from '@playwright/test'
import {seed,command} from './helpers'
import type {Snapshot} from '../../src/api/models'
test.use({viewport:{width:390,height:844},isMobile:true,hasTouch:true})
async function swipe(page:Page,name:string,dx:number,dy=0){
 const row=page.locator('.category-row').filter({hasText:name})
 await row.scrollIntoViewIfNeeded()
 const box=(await row.boundingBox())!,x=box.x+box.width*.65,y=box.y+box.height/2
 const session=await page.context().newCDPSession(page)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
 for(let i=1;i<=8;i++)await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+dx*i/8,y:y+dy*i/8}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await session.detach()
}
test('category swipe confirms, cancels and retries safely; edit offers confirmed deletion',async({page,request},info)=>{
 const actor=await seed(page,request,'Category deletion owner')
 const category=await command(request,'category.create',{name:'Manager swipe groceries',kind:'expense'},actor.id)
 await page.goto('/budget');await page.getByRole('button',{name:'Manage categories',exact:true}).tap()
 const remove=page.getByRole('button',{name:'Remove Manager swipe groceries category',exact:true})
 const row=page.locator('.category-row').filter({hasText:'Manager swipe groceries'})
 await swipe(page,'Manager swipe groceries',-20);await expect(remove).toBeHidden()
 await swipe(page,'Manager swipe groceries',-100);await expect(remove).toBeVisible()
 await swipe(page,'Manager swipe groceries',100);await expect(remove).toBeHidden()
 await swipe(page,'Manager swipe groceries',0,-30);await expect(remove).toBeHidden()
 await swipe(page,'Manager swipe groceries',-100);await remove.tap()
 await expect(page.getByRole('dialog')).toContainText('Remove “Manager swipe groceries”?')
 await expect(page.getByRole('dialog')).toContainText('Existing allocations and spending stay in the budget history.')
 await page.getByRole('button',{name:'Cancel',exact:true}).tap();await expect(row).not.toContainText('Archived')
 await swipe(page,'Manager swipe groceries',-100);await remove.tap()
 await page.screenshot({path:info.outputPath('category-confirmation.png'),animations:'disabled'})
 const ids:string[]=[]
 await page.route('**/api/v1/operations',async route=>{
  const op=route.request().postDataJSON()
  if(op.kind!=='category.include'||op.entity_id!==category.id||op.data.included){await route.continue();return}
  ids.push(op.operation_id)
  if(ids.length===1){await route.fetch();await route.fulfill({status:503,json:{error:{message:'Response interrupted'}}})}
  else await route.continue()
 })
 await page.getByRole('button',{name:'Remove',exact:true}).tap()
 await expect(page.getByRole('alert')).toContainText('saved on this device')
 await expect(page.getByRole('button',{name:'Cancel',exact:true})).toBeDisabled()
 await page.getByRole('button',{name:'Retry removal',exact:true}).tap()
 await expect(page.getByRole('dialog')).toHaveAccessibleName('Manage categories');await expect(row).toHaveCount(0);await expect.poll(()=>ids.length).toBe(2);expect(ids[0]).toBe(ids[1])
 await expect(remove).toHaveCount(0)
 await page.getByRole('button',{name:'Add category',exact:true}).tap();await page.getByLabel('Category name',{exact:true}).fill('Manager swipe groceries');await page.getByRole('button',{name:'Add Manager swipe groceries',exact:true}).tap();await expect(row).toHaveCount(1)
 await page.getByRole('button',{name:'Edit name of Manager swipe groceries',exact:true}).tap()
 await page.getByLabel('Category name',{exact:true}).fill('Unsaved name')
 await page.getByRole('button',{name:'Remove',exact:true}).tap()
 await expect(page.getByRole('dialog')).toContainText('Remove “Manager swipe groceries”')
 await page.keyboard.press('Escape');await expect(page.getByLabel('Category name',{exact:true})).toHaveValue('Unsaved name')
 await page.getByRole('button',{name:'Remove',exact:true}).tap()
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:844})
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 }
 await page.getByRole('button',{name:'Remove',exact:true}).tap()
 await expect(row).toHaveCount(0)
 await page.reload();await page.getByRole('button',{name:'Manage categories',exact:true}).click();await expect(row).toHaveCount(0)
 const snapshot=await(await request.get('/api/v1/sync/snapshot')).json() as Snapshot
 expect(snapshot.records.categories.find(c=>c.id===category.id)?.name).toBe('Manager swipe groceries')
 const personal=snapshot.records.categories.find(c=>c.owner_id===actor.id&&!c.parent_id)!
 await expect(page.getByRole('button',{name:`Remove ${personal.name} category`,exact:true})).toHaveCount(0)
 await page.getByRole('button',{name:`Edit name of ${personal.name}`,exact:true}).click()
 await expect(page.getByRole('button',{name:'Remove',exact:true})).toHaveCount(0)
})
