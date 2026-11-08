import { test,expect,type Page } from '@playwright/test'
import { seed,command } from './helpers'
import type { Snapshot,Purchase } from '../../src/api/models'

test.use({viewport:{width:390,height:844},isMobile:true,hasTouch:true})
async function swipe(page:Page,item:string,dx:number,dy=0){
 const card=page.getByRole('button',{name:item,exact:true})
 await card.scrollIntoViewIfNeeded()
 const box=(await card.boundingBox())!
 const x=box.x+box.width*.75,y=box.y+box.height/2
 const session=await page.context().newCDPSession(page)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
 for(let step=1;step<=8;step++)await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x+dx*step/8,y:y+dy*step/8}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await session.detach()
}
async function setup(page:Page,request:Parameters<typeof seed>[1],name:string){
 const user=await seed(page,request,name)
 const snapshot=await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot
 const category=snapshot.records.categories.find(c=>c.name==='Food')!
 const purchase=await command(request,'purchase.create',{item:name,amount_minor:1234,category_id:category.id,transaction_date:'2025-09-10'},user.id) as Purchase
 await page.evaluate(()=>localStorage.setItem('pigpen-month','2025-09'));await page.goto('/purchases')
 return purchase
}

test('purchase details omit empty artwork and open a compact image in a zoomable fullscreen viewer',async({page,request})=>{
 await setup(page,request,'Receipt card')
 const card=page.getByRole('button',{name:'Receipt card',exact:true})
 await card.getByText('$12.34',{exact:true}).tap()
 const dialog=page.getByRole('dialog')
 await expect(dialog).toBeVisible()
 await expect(dialog.getByText(/JPEG, PNG or WebP/)).toHaveCount(0)
 await expect(dialog.locator('img')).toHaveCount(0)
 const popup=await dialog.boundingBox()
 expect(Math.abs(popup!.y+popup!.height/2-844/2)).toBeLessThan(2)
 await expect(dialog.getByRole('button',{name:'Upload image',exact:true})).toHaveCount(0)
 await page.getByLabel('Attach receipt or bank screenshot').setInputFiles('tests/fixtures/receipt.png')
 await expect(dialog.getByRole('button',{name:'Upload image',exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Upload image',exact:true}).click()
 const image=dialog.getByRole('img',{name:'receipt.png',exact:true})
 await expect(image).toBeVisible()
 await expect.poll(()=>image.evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true)
 expect((await image.boundingBox())!.height).toBeLessThanOrEqual(120)
 await expect(dialog.getByRole('button',{name:'Upload image',exact:true})).toHaveCount(0)
 const preview=await image.boundingBox(),withImage=await dialog.boundingBox()
 expect(Math.abs(preview!.x+preview!.width/2-(withImage!.x+withImage!.width/2))).toBeLessThan(2)
 expect(Math.abs(withImage!.y+withImage!.height/2-844/2)).toBeLessThan(2)
 await dialog.getByRole('button',{name:'View image: receipt.png',exact:true}).tap()
 const viewer=page.getByRole('dialog',{name:'Purchase image viewer',exact:true})
 await expect(viewer).toBeVisible()
 expect((await viewer.boundingBox())!.height).toBe(844)
 const photo=viewer.getByRole('img',{name:'receipt.png',exact:true})
 await expect.poll(()=>photo.evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true)
 const stage=viewer.locator('.photo-stage'), box=(await stage.boundingBox())!
 const session=await page.context().newCDPSession(page)
 const cx=box.x+box.width/2,cy=box.y+box.height/2
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:1,x:cx-35,y:cy},{id:2,x:cx+35,y:cy}]})
 for(let step=1;step<=6;step++)await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{id:1,x:cx-35-step*12,y:cy},{id:2,x:cx+35+step*12,y:cy}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await expect(viewer.getByRole('button',{name:'Reset image zoom'})).not.toHaveText('100%')
 const before=await photo.evaluate(img=>getComputedStyle(img).transform)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:1,x:cx,y:cy}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{id:1,x:cx+65,y:cy+20}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 expect(await photo.evaluate(img=>getComputedStyle(img).transform)).not.toBe(before)
 await viewer.getByRole('button',{name:'Reset image zoom'}).tap()
 await expect(viewer.getByRole('button',{name:'Reset image zoom'})).toHaveText('100%')
 await stage.tap();await stage.tap()
 await expect(viewer.getByRole('button',{name:'Reset image zoom'})).toHaveText('250%')
 await page.screenshot({path:'../output/purchase-images/mobile-viewer.png'})
 await viewer.getByRole('button',{name:'Zoom out',exact:true}).tap()
 await expect(viewer.getByRole('button',{name:'Reset image zoom'})).toHaveText('167%')
 await viewer.getByRole('button',{name:'Close image viewer'}).tap()
 await expect(viewer).toHaveCount(0)
 await expect(dialog).toBeVisible()
 await expect(dialog.getByRole('button',{name:'View image: receipt.png',exact:true})).toBeFocused()
 await dialog.getByRole('button',{name:'View image: receipt.png',exact:true}).tap()
 await page.keyboard.press('Escape')
 await expect(viewer).toHaveCount(0)
 await expect(dialog).toBeVisible()
 await dialog.getByRole('button',{name:'View image: receipt.png',exact:true}).tap()
 await expect(viewer).toBeVisible()
 const dragBox=(await viewer.locator('.photo-stage').boundingBox())!
 const dragX=dragBox.x+dragBox.width/2,dragY=dragBox.y+dragBox.height/2
 async function pull(distance:number,cancel=false){
  await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:dragX,y:dragY}]})
  for(let step=1;step<=8;step++)await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:dragX+step,y:dragY+distance*step/8}]})
  await expect.poll(async()=>Math.abs(await photo.evaluate(img=>new DOMMatrixReadOnly(getComputedStyle(img).transform).m42)-distance)).toBeLessThan(2)
  await session.send('Input.dispatchTouchEvent',{type:cancel?'touchCancel':'touchEnd',touchPoints:[]})
 }
 await pull(60)
 await expect(viewer).toBeVisible()
 await expect.poll(()=>photo.evaluate(img=>new DOMMatrixReadOnly(getComputedStyle(img).transform).m42)).toBe(0)
 await pull(150,true)
 await expect(viewer).toBeVisible()
 await expect.poll(()=>photo.evaluate(img=>new DOMMatrixReadOnly(getComputedStyle(img).transform).m42)).toBe(0)
 await pull(160)
 await expect(viewer).toHaveCount(0)
 await expect(dialog).toBeVisible()
 await expect(dialog.getByRole('button',{name:'View image: receipt.png',exact:true})).toBeFocused()
 await page.screenshot({path:'../output/purchase-images/mobile-detail.png'})
 await session.detach()
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 await card.getByRole('img').tap()
 await expect(dialog.getByRole('img',{name:'receipt.png',exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 await card.focus();await page.keyboard.press('Enter');await expect(dialog).toBeVisible()
})

test('swipe reveals delete, confirmation can cancel, and failed deletion retries safely',async({page,request})=>{
 const purchase=await setup(page,request,'Swipe card')
 await swipe(page,'Swipe card',-20)
 await expect(page.getByRole('button',{name:'Delete Swipe card',exact:true})).toBeHidden()
 await swipe(page,'Swipe card',-100)
 await expect(page.getByRole('dialog')).toHaveCount(0)
 const remove=page.getByRole('button',{name:'Delete Swipe card',exact:true})
 await expect(remove).toBeVisible();await remove.tap()
 await expect(page.getByRole('dialog')).toContainText('It will be removed from spending totals.')
 await page.getByRole('button',{name:'Cancel',exact:true}).tap()
 expect((await (await request.get('/api/v1/purchases?month=2025-09')).json()).items.some((p:Purchase)=>p.id===purchase.id)).toBe(true)
 await swipe(page,'Swipe card',0,-60)
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await swipe(page,'Swipe card',-100)
 await remove.tap()
 const operationIds:string[]=[]
 await page.route('**/api/v1/operations',async route=>{
  const op=route.request().postDataJSON()
  if(op.kind!=='purchase.delete'){await route.continue();return}
  operationIds.push(op.operation_id)
  if(operationIds.length===1){await route.fetch();await route.fulfill({status:503,json:{error:{message:'Response interrupted'}}})}
  else await route.continue()
 })
 await page.getByRole('button',{name:'Delete purchase',exact:true}).tap()
 await expect(page.getByRole('alert')).toContainText('saved on this device')
 await page.getByRole('button',{name:'Retry saved submission',exact:true}).tap()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 expect(operationIds).toHaveLength(2);expect(operationIds[0]).toBe(operationIds[1])
 await expect(page.getByRole('button',{name:'Swipe card',exact:true})).toHaveCount(0)
 expect((await (await request.get('/api/v1/purchases?month=2025-09')).json()).items.some((p:Purchase)=>p.id===purchase.id)).toBe(false)
})
