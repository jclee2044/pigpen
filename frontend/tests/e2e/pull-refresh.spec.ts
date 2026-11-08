import { test,expect,type Page } from '@playwright/test'
import { seed,command } from './helpers'
async function touch(page:Page,type:string,x:number,y:number,target='main'){
 await page.evaluate(({type,x,y,target})=>{
  const element=document.querySelector(target)!
  const finger=new Touch({identifier:1,target:element,clientX:x,clientY:y})
  element.dispatchEvent(new TouchEvent(type,{bubbles:true,cancelable:true,touches:type==='touchend'||type==='touchcancel'?[]:[finger],changedTouches:[finger]}))
 },{type,x,y,target})
}
test('pull refresh syncs new records once, keeps pink above logo and anchors compact navigation',async({page,request},info)=>{
 await page.setViewportSize({width:390,height:844})
 await seed(page,request,'Pull refresh actor')
 const firstPull=page.waitForResponse(r=>r.url().includes('/sync/pull'))
 await page.goto('/profiles');await firstPull
 await expect(page.getByTestId('selected-profile')).toHaveText('Pull refresh actor')
 await command(request,'user.create',{name:'Arrived through pull'})
 let pulls=0
 let release!:()=>void
 const gate=new Promise<void>(resolve=>{release=resolve})
 await page.route('**/api/v1/sync/pull?**',async route=>{pulls++;await gate;await route.continue()})
 await touch(page,'touchstart',180,220)
 await touch(page,'touchmove',180,380)
 await expect(page.getByRole('status').filter({hasText:'Release to sync'})).toBeVisible()
 expect(await page.locator('.pull-refresh').evaluate(el=>getComputedStyle(el).backgroundColor)).toBe('rgb(242, 221, 228)')
 await touch(page,'touchend',180,380)
 await expect(page.locator('.pull-refresh')).toHaveClass(/refreshing/)
 await expect.poll(()=>pulls).toBe(1)
 // A second gesture during the request must not enqueue another sync.
 await touch(page,'touchstart',180,220);await touch(page,'touchmove',180,400);await touch(page,'touchend',180,400)
 expect(pulls).toBe(1)
 await page.screenshot({path:info.outputPath('pull-spinner.png')})
 release()
 await expect(page.getByRole('button',{name:'Arrived through pull',exact:false})).toBeVisible()
 await expect(page.locator('.pull-refresh')).not.toHaveClass(/refreshing/)
 await expect(page.locator('.refresh-host')).toHaveCSS('--pull-distance','0px')
 const nav=await page.getByRole('navigation',{name:'Mobile navigation'}).boundingBox()
 expect(nav!.y+nav!.height).toBe(844);expect(nav!.height).toBeLessThanOrEqual(82)
 // Chromium has no OS notch; inject the same inset values supplied by iOS.
 await page.addStyleTag({content:':root{--safe-area-top:47px;--safe-area-bottom:34px}'})
 await expect(page.locator('.app-header')).toHaveCSS('height','117px')
 await expect(page.locator('.mobile-nav')).toHaveCSS('padding-bottom','22px')
 await touch(page,'touchstart',180,220);await touch(page,'touchmove',180,380)
 await expect(page.locator('.pull-refresh')).toHaveClass(/active/)
 const wheel=await page.locator('.refresh-wheel').boundingBox()
 expect(wheel!.y).toBeGreaterThanOrEqual(47)
 await page.screenshot({path:info.outputPath('safe-area-pull.png')})
 await touch(page,'touchcancel',180,380)
 await page.screenshot({path:info.outputPath('compact-bottom-nav.png')})
})
test('short, horizontal, cancelled and scrolled gestures do not trigger refresh',async({page,request})=>{
 await page.setViewportSize({width:390,height:600})
 await seed(page,request,'Gesture actor')
 const firstPull=page.waitForResponse(r=>r.url().includes('/sync/pull'))
 await page.goto('/profiles');await firstPull
 let pulls=0
 page.on('request',r=>{if(r.url().includes('/sync/pull'))pulls++})
 for(const [x,y,finish] of [[180,260,'touchend'],[320,240,'touchend'],[180,400,'touchcancel']] as const){
  await touch(page,'touchstart',180,220);await touch(page,'touchmove',x,y);await touch(page,finish,x,y)
  await expect(page.locator('.refresh-host')).toHaveCSS('--pull-distance','0px')
 }
 await page.evaluate(()=>window.scrollTo(0,100))
 expect(await page.evaluate(()=>scrollY)).toBeGreaterThan(0)
 await touch(page,'touchstart',180,220);await touch(page,'touchmove',180,400);await touch(page,'touchend',180,400)
 await expect(page.locator('.refresh-host')).toHaveCSS('--pull-distance','0px')
 expect(pulls).toBe(0)
})

test('real touch pulls from the logo repeat reliably without changing document height',async({page,request})=>{
 await page.setViewportSize({width:390,height:844})
 await seed(page,request,'Real touch actor')
 const firstPull=page.waitForResponse(r=>r.url().includes('/sync/pull'))
 await page.goto('/profiles');await firstPull
 const cdp=await page.context().newCDPSession(page)
 await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1})
 let pulls=0
 page.on('request',r=>{if(r.url().includes('/sync/pull'))pulls++})
 for(let attempt=1;attempt<=3;attempt++){
  await page.evaluate(()=>scrollTo(0,0))
  const height=await page.evaluate(()=>document.documentElement.scrollHeight)
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:80,y:35}]})
  for(const y of [37,42,52,72,102,132,162,192]){
   await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:80,y}]})
  }
  await expect(page.locator('.pull-refresh')).toHaveClass(/active/)
  expect(await page.evaluate(()=>document.documentElement.scrollHeight)).toBe(height)
  expect(await page.evaluate(()=>scrollY)).toBe(0)
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
  await expect(page.locator('.pull-refresh')).toHaveClass(/refreshing/)
  await expect.poll(()=>pulls).toBe(attempt)
  await expect(page.locator('.pull-refresh')).not.toHaveClass(/refreshing/)
  await expect(page.locator('.refresh-host')).toHaveCSS('--pull-distance','0px')
  await expect(page).toHaveURL(/\/profiles$/)
 }
 // An ordinary tap still follows the home link.
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:80,y:35}]})
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await expect(page).toHaveURL(/\/$/)
})

test('initial select or create profile page never captures a refresh pull',async({page,request})=>{
 await page.setViewportSize({width:390,height:844})
 // Seed a household independently so this page still has no selected local profile.
 const snapshot=await (await request.get('/api/v1/sync/snapshot')).json()
 if(!snapshot.records.household.length)await command(request,'household.initialize',{name:'Entry household'})
 await command(request,'user.create',{name:'Entry pull actor'})
 const firstPull=page.waitForResponse(r=>r.url().includes('/sync/pull'))
 await page.goto('/');await firstPull
 await expect(page.getByRole('heading',{name:'Choose or create your profile'})).toBeVisible()
 let pulls=0
 page.on('request',r=>{if(r.url().includes('/sync/pull'))pulls++})
 await touch(page,'touchstart',180,220);await touch(page,'touchmove',180,430);await touch(page,'touchend',180,430)
 await expect(page.locator('.pull-refresh')).not.toHaveClass(/active|refreshing/)
 await expect(page.locator('.refresh-host')).toHaveCSS('--pull-distance','0px')
 expect(pulls).toBe(0)
})

test('header stays anchored while bottom navigation resets a scrolled page',async({page,request},info)=>{
 await page.setViewportSize({width:390,height:600})
 await seed(page,request,'Header navigation actor')
 await page.goto('/profiles')
 await expect(page.getByTestId('selected-profile')).toHaveText('Header navigation actor')
 // Make the source taller than every destination to exercise route-height shrinkage.
 await page.addStyleTag({content:'main:has(.profile-grid){min-height:1800px}'})
 const header=page.locator('.app-header')
 await expect(header).toHaveCSS('position','fixed')
 expect(await header.evaluate(el=>el.closest('.refresh-content'))).toBeNull()
 for(const inset of [0,47]){
  for(const destination of ['Budget','Purchases','Approvals','Wish Lists','Home']){
   await page.goto('/profiles')
   await page.addStyleTag({content:`:root{--safe-area-top:${inset}px}main:has(.profile-grid){min-height:1800px}`})
   await expect(header).toBeVisible()
   await page.evaluate(()=>scrollTo(0,500))
   await expect.poll(()=>page.evaluate(()=>scrollY)).toBe(500)
   await page.evaluate(()=>{
    const samples:{top:number;color:string;covered:boolean}[]=[]
    Object.assign(window,{headerSamples:samples,stopHeaderSampling:false})
    const sample=()=>{
     const header=document.querySelector('.app-header')!
     samples.push({top:header.getBoundingClientRect().top,color:getComputedStyle(header).backgroundColor,covered:header.contains(document.elementFromPoint(200,10))})
     if(!(window as unknown as {stopHeaderSampling:boolean}).stopHeaderSampling)requestAnimationFrame(sample)
    }
    sample()
   })
   await page.getByRole('navigation',{name:'Mobile navigation',exact:true}).getByRole('link',{name:destination,exact:true}).click()
   await expect.poll(()=>page.evaluate(()=>scrollY)).toBe(0)
   await expect.poll(()=>page.evaluate(()=>(window as unknown as {headerSamples:unknown[]}).headerSamples.length)).toBeGreaterThan(20)
   const samples=await page.evaluate(()=>{
    const state=window as unknown as {stopHeaderSampling:boolean;headerSamples:{top:number;color:string;covered:boolean}[]}
    state.stopHeaderSampling=true
    return state.headerSamples
   })
   expect(samples.every(s=>s.top===0&&s.color==='rgb(242, 221, 228)'&&s.covered)).toBe(true)
   await expect(header).toHaveCSS('height',`${70+inset}px`)
  }
 }
 await page.screenshot({path:info.outputPath('header-after-scrolled-navigation.png')})
 await page.setViewportSize({width:1440,height:900})
 await expect(header).toHaveCSS('height','127px')
 const contentTop=await page.locator('main').evaluate(el=>el.getBoundingClientRect().top)
 expect(contentTop).toBe(127)
})
