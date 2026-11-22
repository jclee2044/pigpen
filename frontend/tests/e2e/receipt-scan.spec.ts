import { test,expect } from '@playwright/test'
import { seed,command } from './helpers'
import type { Snapshot } from '../../src/api/models'

test('real OCR review, interrupted save replay, attachment and retention',async({page,request})=>{
 await page.setViewportSize({width:390,height:844})
 const user=await seed(page,request,'Receipt tester')
 await page.goto('/purchases')
 await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await page.getByLabel('Or choose an image').setInputFiles('tests/fixtures/scan-receipt.png')
 await expect(page.getByLabel('Item or service')).toHaveValue('Purchase at PIGPEN MARKET',{timeout:20000})
 await expect(page.getByLabel('Amount ($)',{exact:true})).toHaveValue('7.95')
 await expect(page.getByLabel('Description',{exact:true})).toHaveValue(/Apples/)
 await page.getByRole('button',{name:'Enlarge receipt photo',exact:true}).click()
 await page.getByRole('button',{name:'Zoom in',exact:true}).click()
 await expect(page.getByRole('button',{name:'Reset image zoom',exact:true})).toHaveText('150%')
 await page.getByRole('button',{name:'Close image viewer',exact:true}).click()
 const retention=page.locator('.receipt-retention')
 const retentionBox=await retention.getByRole('checkbox').locator('..').boundingBox()
 const helpBox=await retention.locator('p').boundingBox()
 expect(helpBox!.y-(retentionBox!.y+retentionBox!.height)).toBeLessThanOrEqual(5)
 expect(await retention.locator('p').evaluate(el=>getComputedStyle(el).fontSize)).toBe('12px')
 await expect(page.getByText(/Review the receipt, including handwritten/)).toHaveCount(0)
 await expect(page.getByText(/Line items may be incomplete or misread/)).toHaveCount(0)
 const before=(await (await request.get('/api/v1/sync/snapshot')).json()) as Snapshot
 expect(before.records.purchases.filter(p=>p.purchaser_id===user.id)).toHaveLength(0)
 await expect(page.getByRole('button',{name:'Save',exact:true})).toBeDisabled()
 await page.getByLabel('Item or service').fill('Reviewed groceries')
 await page.getByLabel('Category',{exact:true}).last().selectOption({label:'Food'})
 if(await page.getByLabel('I verified everything above is accurate').count())await page.getByLabel('I verified everything above is accurate').check()
 const keepBox=await page.getByLabel('Keep photo indefinitely').boundingBox()
 const keepLabel=await page.getByLabel('Keep photo indefinitely').locator('..').boundingBox()
 expect(Math.abs(keepBox!.y-keepLabel!.y)).toBeLessThan(4)
 await page.getByLabel('Keep photo indefinitely').check()
 await page.screenshot({path:'../output/receipt-scan/review-mobile.png',fullPage:true})
 const ids:string[]=[]
 await page.route('**/api/v1/operations',async route=>{
  const op=route.request().postDataJSON()
  if(op.kind!=='receipt.confirm'){await route.continue();return}
  ids.push(op.operation_id)
  if(ids.length===1){await route.fetch();await route.fulfill({status:503,json:{error:{message:'Interrupted response'}}})}else await route.continue()
 })
 await page.getByRole('button',{name:'Save',exact:true}).click()
 await expect(page.getByRole('alert')).toContainText('saved on this device')
 await page.getByRole('button',{name:'Retry saved submission',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 expect(ids).toHaveLength(2);expect(ids[0]).toBe(ids[1])
 const after=await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot
 const purchases=after.records.purchases.filter(p=>p.purchaser_id===user.id)
 expect(purchases).toHaveLength(1);expect(purchases[0]!.amount_minor).toBe(795)
 const photo=after.records.attachments.find(x=>x.purchase_id===purchases[0]!.id)!
 expect(photo.keep_indefinitely).toBe(true)
 expect((await request.get('/api/v1/attachments/'+photo.id+'/content')).ok()).toBe(true)
 await page.goto('/purchases?detail='+purchases[0]!.id)
 await expect(page.getByLabel('Keep photo indefinitely')).toBeChecked()
 await page.getByLabel('Keep photo indefinitely').uncheck()
 await expect.poll(async()=>{const s=await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot;return s.records.attachments.find(x=>x.id===photo.id)?.keep_indefinitely}).toBe(false)
 await page.screenshot({path:'../output/receipt-scan/detail-mobile.png',fullPage:true})
})

test('fresh scan after closing, duplicate warning and explicit override',async({page,request})=>{
 const user=await seed(page,request,'Receipt resume')
 const snap=await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot
 await command(request,'purchase.create',{item:'Earlier receipt',amount_minor:795,category_id:snap.records.categories.find(c=>c.name==='Food')!.id,transaction_date:'2026-11-09',merchant:'PIGPEN MARKET'},user.id)
 await page.goto('/purchases');await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await page.getByLabel('Or choose an image').setInputFiles('tests/fixtures/scan-receipt.png')
 await expect(page.getByLabel('Item or service')).toBeVisible({timeout:20000})
 await page.getByLabel('Item or service').fill('Unsaved receipt edit')
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 const confirmation=page.getByRole('dialog',{name:'Continue without saving?',exact:true})
 await expect(confirmation).toBeVisible()
 await confirmation.getByRole('button',{name:'Keep editing',exact:true}).click()
 await expect(page.getByLabel('Item or service')).toHaveValue('Unsaved receipt edit')
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 await page.keyboard.press('Escape')
 await expect(confirmation).toHaveCount(0)
 await expect(page.getByLabel('Item or service')).toHaveValue('Unsaved receipt edit')
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 await confirmation.getByRole('button',{name:'Leave',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 expect(((await (await request.get('/api/v1/purchases')).json()).items as Array<{purchaser_id:string}>).filter(p=>p.purchaser_id===user.id)).toHaveLength(1)
 await page.reload()
 await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await expect(page.getByText('Resume a receipt')).toHaveCount(0)
 await page.getByLabel('Or choose an image').setInputFiles('tests/fixtures/scan-receipt.png')
 await expect(page.getByLabel('Amount ($)',{exact:true})).toHaveValue('7.95',{timeout:20000})
 await page.getByLabel('Category',{exact:true}).last().selectOption({label:'Food'})
 if(await page.getByLabel('I verified everything above is accurate').count())await page.getByLabel('I verified everything above is accurate').check()
 await page.getByRole('button',{name:'Save',exact:true}).click()
 await expect(page.getByRole('alert')).toContainText('matching receipt')
 expect(((await (await request.get('/api/v1/purchases')).json()).items as Array<{purchaser_id:string}>).filter(p=>p.purchaser_id===user.id)).toHaveLength(1)
 await page.getByLabel('I reviewed the matching purchase').check()
 await page.getByRole('button',{name:'Save',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
})

test('discard leaves no purchase and manual entry remains available offline',async({page,request})=>{
 const user=await seed(page,request,'Receipt discard')
 await page.setViewportSize({width:320,height:740})
 await page.goto('/purchases');await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await page.getByLabel('Or choose an image').setInputFiles('tests/fixtures/scan-receipt.png')
 await expect(page.getByLabel('Item or service')).toBeVisible({timeout:20000})
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.getByRole('button',{name:'Cancel',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 expect(((await (await request.get('/api/v1/purchases')).json()).items as Array<{purchaser_id:string}>).filter(p=>p.purchaser_id===user.id)).toHaveLength(0)
 await page.context().setOffline(true)
 await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Enter manually',exact:true}).click()
 await expect(page.getByLabel('Item or service')).toBeVisible()
 await page.getByLabel('Item or service').fill('Manual offline receipt')
 await page.getByLabel('Amount ($)',{exact:true}).fill('5.00')
 await page.getByLabel('Category',{exact:true}).last().selectOption({label:'Food'})
 if(await page.getByLabel('I verified everything above is accurate').count())await page.getByLabel('I verified everything above is accurate').check()
 await page.getByRole('button',{name:'Save',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await page.context().setOffline(false)
 await expect.poll(async()=>{const s=await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot;return s.records.purchases.filter(p=>p.item==='Manual offline receipt').length}).toBe(1)
})

test('public photographed receipt reaches a reviewed purchase with its image',async({page,request})=>{
 test.skip(!process.env.PIGPEN_PUBLIC_RECEIPT,'Optional locally downloaded public acceptance image')
 const user=await seed(page,request,'Public receipt tester')
 await page.goto('/purchases')
 await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await page.getByLabel('Or choose an image').setInputFiles(process.env.PIGPEN_PUBLIC_RECEIPT!)
 await expect(page.getByLabel('Amount ($)',{exact:true})).toHaveValue('56.58',{timeout:30000})
 await expect(page.getByLabel('Description',{exact:true})).toHaveValue(/Coffee.*3.00/)
 await page.getByLabel('Item or service').fill('Public receipt acceptance')
 await page.getByLabel('Category',{exact:true}).last().selectOption({label:'Food'})
 if(await page.getByLabel('I verified everything above is accurate').count())await page.getByLabel('I verified everything above is accurate').check()
 await page.getByRole('button',{name:'Save',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 const snapshot=await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot
 const purchases=snapshot.records.purchases.filter(p=>p.purchaser_id===user.id)
 expect(purchases).toHaveLength(1)
 expect(purchases[0]!.amount_minor).toBe(5658)
 const photo=snapshot.records.attachments.find(p=>p.purchase_id===purchases[0]!.id)!
 expect(photo.keep_indefinitely).toBe(false)
 expect(photo.expires_at).toBeTruthy()
 expect((await request.get('/api/v1/attachments/'+photo.id+'/content')).ok()).toBe(true)
})

test('camera opens automatically, captures a photo and releases the stream',async({page,request})=>{
 await seed(page,request,'Camera tester')
 await page.goto('/purchases')
 await page.getByRole('button',{name:'New purchase',exact:true}).click()
 await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await expect(page.getByRole('button',{name:/Device camera/i})).toHaveCount(0)
 const shutter=page.getByRole('button',{name:'Take receipt photo',exact:true})
 await expect(shutter).toBeEnabled()
 const stream=await page.locator('video').evaluateHandle(video=>(video as HTMLVideoElement).srcObject as MediaStream)
 await page.setViewportSize({width:390,height:844})
 const gallery=await page.getByRole('button',{name:'Choose existing photo',exact:true}).boundingBox()
 const capture=await shutter.boundingBox()
 expect(Math.abs(capture!.x+capture!.width/2-195)).toBeLessThan(1)
 const inner=await shutter.locator('span').boundingBox()
 expect(Math.abs(inner!.x+inner!.width/2-195)).toBeLessThan(1)
 expect(Math.abs(inner!.y+inner!.height/2-(capture!.y+capture!.height/2))).toBeLessThan(1)
 const frame=await page.locator('.camera-frame').boundingBox()
 const viewfinder=await page.locator('.camera-viewfinder').boundingBox()
 expect(frame!.width).toBeLessThanOrEqual(viewfinder!.width+1)
 expect(frame!.height).toBeLessThanOrEqual(viewfinder!.height+1)
 const sourceAspect=await page.locator('video').evaluate(el=>(el as HTMLVideoElement).videoWidth/(el as HTMLVideoElement).videoHeight)
 expect(Math.abs(frame!.width/frame!.height-sourceAspect)).toBeLessThan(.01)
 await expect(page.getByRole('slider',{name:'Camera zoom',exact:true})).toHaveValue('1')
 const pageScale=await page.evaluate(()=>visualViewport!.scale)
 const touch=await page.context().newCDPSession(page)
 await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:1,x:150,y:350},{id:2,x:230,y:350}]})
 for(let step=1;step<=5;step++)await touch.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{id:1,x:150-step*8,y:350},{id:2,x:230+step*8,y:350}]})
 await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 expect(await page.getByRole('slider',{name:'Camera zoom',exact:true}).inputValue()).not.toBe('1')
 expect(await page.evaluate(()=>visualViewport!.scale)).toBe(pageScale)
 await page.getByRole('button',{name:'Camera zoom 2x',exact:true}).tap()
 await expect(page.getByRole('slider',{name:'Camera zoom',exact:true})).toHaveValue('2')
 const dimensions=await page.locator('video').evaluate(el=>({width:(el as HTMLVideoElement).videoWidth,height:(el as HTMLVideoElement).videoHeight}))
 expect(gallery!.x).toBeLessThan(capture!.x)
 expect(gallery!.y).toBeGreaterThan(600)
 await page.screenshot({path:'../output/receipt-camera/camera-mobile.png'})
 await page.getByLabel('Or choose an image').dispatchEvent('cancel',{bubbles:true})
 await expect(page.getByRole('dialog',{name:'Scan receipt',exact:true})).toBeVisible()
 await expect(shutter).toBeEnabled()
 await page.evaluate(()=>{
  const original=HTMLCanvasElement.prototype.toBlob
  HTMLCanvasElement.prototype.toBlob=function(callback,...args){
   ;(window as unknown as {captureSize:{width:number;height:number}}).captureSize={width:this.width,height:this.height}
   return original.call(this,callback,...args)
  }
 })
 await shutter.click()
 const size=await page.evaluate(()=>(window as unknown as {captureSize:{width:number;height:number}}).captureSize)
 expect(size.width).toBe(Math.round(dimensions.width/2))
 expect(size.height).toBe(Math.round(dimensions.height/2))
 expect(await stream.evaluate(s=>s.getTracks().every(t=>t.readyState==='ended'))).toBe(true)
 await expect(page.getByRole('dialog').locator('p[role=status]')).toContainText(/Could not (?:isolate|read) (?:the|this) receipt/,{timeout:20000})
 const popup=await page.getByRole('dialog',{name:'Scan receipt',exact:true}).boundingBox()
 expect(Math.abs(popup!.y+popup!.height/2-422)).toBeLessThan(2)
 await page.getByRole('button',{name:'Retake photo',exact:true}).click()
 await expect(shutter).toBeEnabled()
 const second=await page.locator('video').evaluateHandle(video=>(video as HTMLVideoElement).srcObject as MediaStream)
 await expect(page.getByRole('slider',{name:'Camera zoom',exact:true})).toHaveValue('1')
 await page.getByLabel('Or choose an image').setInputFiles('tests/fixtures/scan-receipt.png')
 await expect(page.getByLabel('Item or service')).toHaveValue('Purchase at PIGPEN MARKET',{timeout:20000})
 await expect(page.getByLabel('Amount ($)',{exact:true})).toHaveValue('7.95')
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 await page.getByRole('button',{name:'Leave',exact:true}).click()
 expect(await second.evaluate(s=>s.getTracks().every(t=>t.readyState==='ended'))).toBe(true)
})

test('camera denial preserves the photo library fallback',async({page,request})=>{
 await page.addInitScript(()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('Denied','NotAllowedError')}})
 await seed(page,request,'Camera fallback')
 await page.goto('/purchases')
 await page.getByRole('button',{name:'New purchase',exact:true}).click()
 await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await expect(page.getByRole('alert')).toContainText('Camera unavailable')
 await expect(page.getByRole('button',{name:'Choose existing photo',exact:true})).toBeEnabled()
 await page.getByLabel('Or choose an image').setInputFiles('tests/fixtures/scan-receipt.png')
 await expect(page.getByAltText('Receipt photo')).toBeVisible({timeout:20000})
 await expect(page.getByRole('button',{name:'Scan photo',exact:true})).toHaveCount(0)
})


test.describe('desktop entry',()=>{
 test.use({isMobile:false,hasTouch:false,viewport:{width:1440,height:900}})
 test('only manual entry is available',async({page,request})=>{
  await seed(page,request,'Desktop purchase')
  await page.goto('/purchases')
  await page.getByRole('button',{name:'New purchase',exact:true}).click()
  await expect(page.getByRole('button',{name:'Scan receipt',exact:true})).toHaveCount(0)
  await page.getByRole('button',{name:'Enter manually',exact:true}).click()
  await expect(page.getByLabel('Item or service')).toBeVisible()
 })
})

for(const curved of [false,true])test(`steady ${curved?'curled and shaded':'flat'} receipt captures automatically without pressing the shutter`,async({page,request})=>{
 const fs=await import('node:fs')
 const image='data:image/png;base64,'+fs.readFileSync('tests/fixtures/scan-receipt.png').toString('base64')
 await page.addInitScript(async({source,curved})=>{
  navigator.mediaDevices.getUserMedia=async()=>{
   const canvas=document.createElement('canvas');canvas.width=640;canvas.height=960
   const ctx=canvas.getContext('2d')!,photo=new Image();photo.src=source;await photo.decode()
   function draw(shift:number){
    ctx.fillStyle='#252525';ctx.fillRect(0,0,640,960)
    if(!curved){ctx.drawImage(photo,100+shift,110,440,740);return}
    for(let y=0;y<740;y++){
     const inset=45*Math.sin(y/740*Math.PI),x=100+shift+inset,w=440-2*inset
     ctx.drawImage(photo,0,y/740*photo.height,photo.width,photo.height/740,x,110+y,w,1)
     ctx.fillStyle=`rgba(0,0,0,${.52*Math.exp(-(((y-370)/105)**2))})`
     ctx.fillRect(x,110+y,w,1)
    }
   }
   draw(0)
   const stream=canvas.captureStream(10)
   let tick=0
   const timer=setInterval(()=>{
    if(!stream.active){clearInterval(timer);return}
    tick++;draw((tick%3)*3)
   },150)
   return stream
  }
 },{source:image,curved})
 await seed(page,request,curved?'Curled capture':'Automatic capture')
 await page.goto('/purchases')
 await page.getByRole('button',{name:'New purchase',exact:true}).click()
 await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await expect(page.getByRole('button',{name:'Take receipt photo',exact:true})).toBeEnabled()
 await expect(page.getByText('Hold steady',{exact:true})).toBeVisible()
 await expect(page.getByLabel('Amount ($)',{exact:true})).toHaveValue('7.95',{timeout:30000})
 await page.getByRole('button',{name:'Retake photo',exact:true}).click()
 await expect(page.getByRole('button',{name:'Take receipt photo',exact:true})).toBeEnabled()
 if(curved){
  await page.getByRole('button',{name:'Take receipt photo',exact:true}).click()
  await expect(page.getByLabel('Amount ($)',{exact:true})).toHaveValue('7.95',{timeout:30000})
  await page.getByRole('button',{name:'Retake photo',exact:true}).click()
  await expect(page.getByRole('button',{name:'Take receipt photo',exact:true})).toBeEnabled()
 }
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
})

// Unmodified public photographs: see tools/fixtures/receipt-photos/README.md.
for(const [id,total,automatic] of [
 ['1003','5.35',true],['1013','9.58',true],['1038','17.80',true],['1050','26.96',true],
 ['1051','10.70',true],['1059','7.55',true],['1087','10.81',false],['1109','27.62',true],
] as const)test(`real receipt ${id}: ${automatic?'automatic':'manual'} capture preserves content`,async({page,request})=>{
 const fs=await import('node:fs')
 const image='data:image/jpeg;base64,'+fs.readFileSync(`../tools/fixtures/receipt-photos/${id}-receipt.jpg`).toString('base64')
 await page.addInitScript(source=>{
  navigator.mediaDevices.getUserMedia=async()=>{
   const photo=new Image();photo.src=source;await photo.decode()
   const canvas=document.createElement('canvas');canvas.width=photo.width;canvas.height=photo.height
   const ctx=canvas.getContext('2d')!;ctx.drawImage(photo,0,0)
   const stream=canvas.captureStream(10)
   const timer=setInterval(()=>{if(stream.active)ctx.drawImage(photo,0,0);else clearInterval(timer)},150)
   return stream
  }
 },image)
 await seed(page,request,`Real receipt ${id}`)
 await page.goto('/purchases')
 await page.getByRole('button',{name:'New purchase',exact:true}).click()
 await page.getByRole('button',{name:'Scan receipt',exact:true}).click()
 await expect(page.getByRole('button',{name:'Take receipt photo',exact:true})).toBeEnabled()
 if(!automatic){
  // The image has clipped text at its bottom edge. Manual capture still works.
  await page.waitForTimeout(1500)
  await expect(page.getByRole('button',{name:'Take receipt photo',exact:true})).toBeEnabled()
  await page.getByRole('button',{name:'Take receipt photo',exact:true}).click()
 }
 await expect(page.getByLabel('Amount ($)',{exact:true})).toHaveValue(total,{timeout:30000})
 if(id==='1109')await expect(page.getByLabel('Merchant',{exact:true})).toHaveValue('BreadFish Cafe')
 await page.screenshot({path:`../output/receipt-reliable/review-${id}.png`})
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 await page.getByRole('button',{name:'Leave',exact:true}).click()
})
