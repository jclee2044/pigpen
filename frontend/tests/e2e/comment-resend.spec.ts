import { test,expect } from '@playwright/test'
import { seed,command } from './helpers'

test('own comments confirm resend; cancel, touch, retries and author restrictions',async({page,request},info)=>{
 await page.setViewportSize({width:390,height:844})
 const actor=await seed(page,request,'Resend author')
 const other=await command(request,'user.create',{name:'Resend other'})
 for(const [resource,kind,route] of [['wishlist-items','wishlist.create','/wish-lists'],['approval-requests','request.create','/approvals']] as const){
  const target=kind==='wishlist.create'?await command(request,kind,{name:'Resend wish',price_minor:100},actor.id):await command(request,kind,{item:'Resend request',amount_minor:100},actor.id)
  await command(request,'comment.create',{target_resource:resource,target_id:target.id,text:'My resend comment'},actor.id)
  await command(request,'comment.create',{target_resource:resource,target_id:target.id,text:'Other comment'},other.id)
  await page.goto(route)
  await page.getByRole('button',{name:kind==='wishlist.create'?'Resend wish':'2 comments on Resend request',exact:true}).click()
  const own=page.locator('.comment').filter({hasText:'My resend comment'}),foreign=page.locator('.comment').filter({hasText:'Other comment'})
  let attempts=0
  await page.route('**/api/v1/operations',async r=>{
   const op=r.request().postDataJSON()
   if(op.kind!=='comment.resend')return r.continue()
   attempts++
   const response=await r.fetch()
   if(attempts===1)return r.fulfill({status:503,json:{error:{message:'Response lost'}}})
   return r.fulfill({response})
  })
  const popup=page.getByRole('dialog',{name:'Resend notification?',exact:true})
  await foreign.dblclick();await expect(popup).toHaveCount(0)
  await own.click();await expect(popup).toHaveCount(0)
  await own.dblclick();await expect(popup).toBeVisible();expect(attempts).toBe(0)
  await popup.getByRole('button',{name:'No',exact:true}).click();expect(attempts).toBe(0)
  // Scrolling/cancelled gestures must not count as double taps.
  await own.dispatchEvent('pointerdown',{pointerType:'touch',clientX:30,clientY:30})
  await own.dispatchEvent('pointerup',{pointerType:'touch',clientX:30,clientY:90})
  await expect(popup).toHaveCount(0)
  await own.scrollIntoViewIfNeeded()
  const bounds=await own.boundingBox()
  expect(bounds).toBeTruthy()
  for(let tap=0;tap<2;tap++)await page.touchscreen.tap(bounds!.x+20,bounds!.y+20)
  await expect(popup).toBeVisible()
  await page.screenshot({path:info.outputPath(`${resource}-confirmation.png`)})
  const before=(await (await request.get('/api/v1/notifications')).json()).items.length
  await popup.getByRole('button',{name:'Yes',exact:true}).click()
  await expect(popup.getByRole('button',{name:'Retry saved submission'})).toBeVisible()
  await popup.getByRole('button',{name:'Retry saved submission'}).click()
  await expect(popup).toHaveCount(0);expect(attempts).toBe(2)
  const after=(await (await request.get('/api/v1/notifications')).json()).items.length
  expect(after-before).toBeGreaterThan(0)
  const notes=(await (await request.get('/api/v1/notifications')).json()).items
  const resent=notes.filter((n:{event_key:string})=>n.event_key===notes.at(-1).event_key)
  expect(after-before).toBe(resent.length)
  await expect(page.locator('.comment')).toHaveCount(2)
  await page.unroute('**/api/v1/operations')
  await page.keyboard.press('Escape')
 }
})
