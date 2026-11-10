import { test,expect,type Page } from '@playwright/test'
import { seed,command } from './helpers'

async function addProfile(page:Page,name:string){
 await page.goto('/profiles')
 await expect(page.locator('main h1')).toBeVisible()
 if(await page.getByRole('heading',{name:'Create household',exact:true}).isVisible()){
  await page.getByLabel('Household name').fill('Synthetic live-data household')
  await page.getByRole('button',{name:'Create household',exact:true}).click()
 }else await page.getByRole('button',{name:'Add profile',exact:true}).click()
 await page.getByLabel('Display name').fill(name)
 await page.getByRole('button',{name:'Create profile',exact:true}).click()
 await expect(page.getByTestId('selected-profile')).toHaveText(name)
 await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible()
}

async function addPurchase(page:Page,item:string,amount:string,date:string){
 await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Enter manually',exact:true}).click()
 await page.getByLabel('Item or service').fill(item)
 await page.getByLabel('Amount ($)',{exact:true}).fill(amount)
 await page.getByLabel('Transaction date',{exact:true}).fill(date)
 await page.getByRole('combobox',{name:'Category',exact:true}).selectOption({label:'Food'})
 await page.getByRole('button',{name:'Save',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
}

test('two independent clients share budgets, corrections and exactly one offline purchase',async({page:writer,browser,request,baseURL})=>{
 const readerContext=await browser.newContext({baseURL,viewport:{width:390,height:844}})
 try{
  await addProfile(writer,'Live writer')
  await expect(writer.locator('.status-strip')).toHaveCount(0)
  await addProfile(writer,'Live reader')
  await writer.goto('/profiles')
  await writer.locator('.profile-card').filter({hasText:'Live writer'}).click()
  await expect(writer.getByTestId('selected-profile')).toHaveText('Live writer')
  let reader=await readerContext.newPage()
  await reader.clock.install({time:new Date('2026-11-07T12:00:00Z')})
  await reader.clock.pauseAt(new Date('2026-11-07T12:00:01Z'))
  await reader.goto('/profiles')
  await reader.locator('.profile-card').filter({hasText:'Live reader'}).click()
  await expect(reader.getByTestId('selected-profile')).toHaveText('Live reader')

  await writer.goto('/budget')
  await writer.getByLabel('Budget month',{exact:true}).fill('2025-10')
  await writer.getByRole('button',{name:'Edit',exact:true}).click()
  await writer.getByLabel('Expected income ($)',{exact:true}).fill('1000.00')
  await writer.getByLabel('Food',{exact:true}).fill('200.00')
  await writer.getByRole('button',{name:'Save budget',exact:true}).click()
  await expect(writer.getByRole('dialog')).toHaveCount(0)
  await writer.goto('/')
  await addPurchase(writer,'Cross-device groceries','12.34','2025-10-07')
  // Advance browser time to prove periodic sync without a click or focus event.
  let polls=0
  reader.on('request',request=>{if(request.url().includes('/sync/pull?'))polls++})
  await reader.getByLabel('Selected month',{exact:true}).fill('2025-10')
  await reader.clock.runFor(59000)
  expect(polls).toBe(0)
  await reader.clock.runFor(1000)

  await expect(reader.getByTestId('allocated')).toHaveText('$200.00')
  await expect(reader.getByTestId('spent')).toHaveText('$12.34')
  await reader.reload()
  await expect(reader.getByTestId('spent')).toHaveText('$12.34')
  await expect(reader.getByTestId('selected-profile')).toHaveText('Live reader')

  await writer.getByRole('button',{name:'Cross-device groceries',exact:true}).click()
  await writer.getByRole('button',{name:'Edit purchase',exact:true}).click()
  await writer.getByLabel('Amount ($)',{exact:true}).fill('14.50')
  await writer.getByRole('button',{name:'Save changes',exact:true}).click()
  await expect(writer.getByRole('dialog')).toHaveCount(0)
  await writer.goto('/')
  await reader.evaluate(()=>window.dispatchEvent(new Event('focus')))
  await expect(reader.getByTestId('spent')).toHaveText('$14.50')

  await reader.evaluate(async()=>{await navigator.serviceWorker.ready})
  await expect.poll(()=>reader.evaluate(()=>!!navigator.serviceWorker.controller)).toBe(true)
  await readerContext.setOffline(true)
  await expect(reader.getByText('Offline · saved on this device',{exact:true})).toBeVisible()
  await addPurchase(reader,'Cross-device offline purchase','2.25','2025-10-08')
  await expect(reader.getByText('1 purchase waiting to sync.',{exact:true})).toBeVisible()
  await expect(reader.getByTestId('spent')).toHaveText('$14.50')
  await writer.evaluate(()=>window.dispatchEvent(new Event('focus')))
  await expect(writer.getByTestId('spent')).toHaveText('$14.50')
  await reader.close()
  reader=await readerContext.newPage()
  await reader.goto('/')
  await expect(reader.getByText('1 purchase waiting to sync.',{exact:true})).toBeVisible()
  await expect(reader.getByTestId('selected-profile')).toHaveText('Live reader')
  await readerContext.setOffline(false)
  await reader.evaluate(()=>window.dispatchEvent(new Event('focus')))
  await expect(reader.locator('.pending-panel')).toHaveCount(0)
  await expect(reader.getByTestId('spent')).toHaveText('$16.75')
  await expect(reader.getByText('Offline · saved on this device',{exact:true})).toHaveCount(0)
  for(let retry=0;retry<2;retry++){
   await writer.evaluate(()=>window.dispatchEvent(new Event('focus')))
   await expect(writer.getByTestId('spent')).toHaveText('$16.75')
  }
  await writer.reload()
  await expect(writer.getByTestId('spent')).toHaveText('$16.75')
  const users=(await (await request.get('/api/v1/users')).json()).items
  const purchases=(await (await request.get('/api/v1/purchases?month=2025-10')).json()).items
  const offline=purchases.filter((purchase:{item:string})=>purchase.item==='Cross-device offline purchase')
  expect(offline).toHaveLength(1)
  expect(offline[0].purchaser_id).toBe(users.find((user:{name:string})=>user.name==='Live reader').id)
  expect((await (await request.get('/api/v1/budget-months/2025-10')).json()).spent_minor).toBe(1675)
  expect(await writer.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  expect(await reader.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 }finally{await readerContext.close()}
})

test('missing optional runtime metadata leaves server records usable',async({page,request})=>{
 await page.route('**/api/v1/runtime',route=>route.fulfill({status:503,json:{error:{code:'unavailable',message:'Metadata unavailable'}}}))
 const actor=await seed(page,request,'Metadata reader')
 const categories=(await (await request.get('/api/v1/categories')).json()).items
 await command(request,'purchase.create',{item:'Metadata-independent purchase',amount_minor:123,category_id:categories.find((category:{name:string})=>category.name==='Food').id,transaction_date:'2024-12-01'},actor.id)
 await page.getByLabel('Selected month',{exact:true}).fill('2024-12')
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')))
 await expect(page.getByTestId('spent')).toHaveText('$1.23')
 await expect(page.locator('.data-source')).toHaveCount(0)
})
