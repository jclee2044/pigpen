import { test,expect } from '@playwright/test'
import { command } from './helpers'

test('a new phone enters through profile selection and remembers its choice',async({page,request},info)=>{
 await page.setViewportSize({width:390,height:844})
 const snapshot=await (await request.get('/api/v1/sync/snapshot')).json()
 if(!snapshot.records.household.length)await command(request,'household.initialize',{name:'Synthetic household'})
 await command(request,'user.create',{name:'Phone navigation actor'})
 await page.goto('/purchases')
 await expect(page.getByRole('heading',{name:'Choose or create your profile',exact:true})).toBeVisible()
 await expect(page.getByRole('img',{name:'PigPen',exact:true})).toBeVisible()
 await expect(page.getByText(/Your choice is saved on this device/)).toBeVisible()
 const nav=page.getByRole('navigation',{name:'Mobile navigation',exact:true})
 await expect(nav).toHaveCount(0)
 await expect(page.getByRole('navigation',{name:'Main navigation',exact:true})).toHaveCount(0)
 await expect(page.getByRole('button',{name:'Our household',exact:true})).toHaveCount(0)
 await page.screenshot({path:info.outputPath('profile-entry.png'),fullPage:true})
 await page.getByRole('button',{name:/Phone navigation actor/}).click()
 await expect(page.getByRole('heading',{name:'Purchases',exact:true})).toBeVisible()
 await expect(nav.getByRole('link')).toHaveText(['Home','Budget','Purchases','Approvals','Wish Lists'])
 for(const [label,heading] of [['Budget','Budget'],['Purchases','Purchases'],['Approvals','Approvals'],['Wish Lists','Wish lists'],['Home','Dashboard']]){
  await nav.getByRole('link',{name:label,exact:true}).click()
  await expect(page.getByRole('heading',{name:heading,exact:true})).toBeVisible()
 }
 await page.reload()
 await expect(page.getByTestId('selected-profile')).toHaveText('Phone navigation actor')
 await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible()
 await expect(page.getByText(/Your choice is saved on this device/)).toHaveCount(0)
})

test('creating a profile on the entry screen enters the app without selecting again',async({page,request})=>{
 await page.setViewportSize({width:390,height:844})
 const snapshot=await (await request.get('/api/v1/sync/snapshot')).json()
 if(!snapshot.records.household.length)await command(request,'household.initialize',{name:'Synthetic household'})
 await page.goto('/')
 await page.getByRole('button',{name:'Add profile',exact:true}).click()
 await page.getByLabel('Display name').fill('New phone profile')
 await page.getByRole('button',{name:'Create profile',exact:true}).click()
 await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible()
 await expect(page.getByRole('navigation',{name:'Mobile navigation',exact:true})).toBeVisible()
 await page.reload()
 await expect(page.getByTestId('selected-profile')).toHaveText('New phone profile')
 await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible()
})

test('mobile selection slides without changing size',async({page,request})=>{
 await page.setViewportSize({width:390,height:844})
 await page.emulateMedia({reducedMotion:'no-preference'})
 const snapshot=await (await request.get('/api/v1/sync/snapshot')).json()
 if(!snapshot.records.household.length)await command(request,'household.initialize',{name:'Synthetic household'})
 await command(request,'user.create',{name:'Navigation motion actor'})
 await page.goto('/')
 await page.getByRole('button',{name:/Navigation motion actor/}).click()
 const nav=page.getByRole('navigation',{name:'Mobile navigation',exact:true})
 const pill=nav.locator('.mobile-nav-highlight')
 await expect(pill).toBeVisible()
 const start=await pill.boundingBox()
 await nav.getByRole('link',{name:'Wish Lists',exact:true}).click()
 const frames=await pill.evaluate(el=>{
  const animation=el.getAnimations()[0]!
  animation.pause()
  if((animation.effect as KeyframeEffect).getKeyframes().some(frame=>'left' in frame))throw new Error('Pill must slide on its own compositing layer')
  const sample=(time:number)=>{
   animation.currentTime=time
   const rect=el.getBoundingClientRect()
   return {x:rect.x,width:rect.width,height:rect.height,transform:getComputedStyle(el).transform}
  }
  // Sample keyframes independent of the animation's easing.
  animation.effect!.updateTiming({easing:'linear'})
  return [sample(0),sample(210),sample(420)]
 })
 expect(await pill.evaluate(el=>getComputedStyle(el).willChange)).toBe('transform')
 for(const link of await nav.getByRole('link').all()){
  expect(await link.evaluate(el=>getComputedStyle(el).transform)).not.toBe('none')
  expect(await link.evaluate(el=>getComputedStyle(el).willChange)).toBe('transform')
 }
 expect(frames[0]!.x).toBeCloseTo(start!.x,0)
 expect(frames[1]!.width).toBeCloseTo(start!.width,0)
 expect(frames[1]!.height).toBeCloseTo(start!.height,0)
 const target=await nav.getByRole('link',{name:'Wish Lists',exact:true}).boundingBox()
 expect(frames[2]!.x).toBeCloseTo(target!.x,0)
 expect(frames[2]!.width).toBeCloseTo(target!.width,0)
 await nav.getByRole('link',{name:'Budget',exact:true}).click()
 await nav.getByRole('link',{name:'Home',exact:true}).click()
 await expect.poll(async()=>pill.evaluate(el=>el.getAnimations().filter(a=>a.playState==='running').length)).toBe(0)
 await page.setViewportSize({width:430,height:844})
 await expect.poll(async()=>Math.round((await pill.boundingBox())!.width)).toBe(Math.round((await nav.getByRole('link',{name:'Home',exact:true}).boundingBox())!.width))
 await page.emulateMedia({reducedMotion:'reduce'})
 await nav.getByRole('link',{name:'Purchases',exact:true}).click()
 expect(await pill.evaluate(el=>el.getAnimations().length)).toBe(0)
 await expect(nav.getByRole('link',{name:'Purchases',exact:true})).toHaveAttribute('aria-current','page')
})


test('mobile row stays fixed when the bottom safe-area inset fluctuates during routing',async({page,request})=>{
 test.setTimeout(60000)
 await page.setViewportSize({width:390,height:844})
 const snapshot=await (await request.get('/api/v1/sync/snapshot')).json()
 if(!snapshot.records.household.length)await command(request,'household.initialize',{name:'Synthetic household'})
 await command(request,'user.create',{name:'Safe area navigation actor'})
 await page.goto('/')
 await page.getByRole('button',{name:/Safe area navigation actor/}).click()
 const nav=page.getByRole('navigation',{name:'Mobile navigation',exact:true})
 await expect(nav).toBeVisible()
 for(const width of [320,390,430,760]){
  await page.setViewportSize({width,height:844})
  const drift=await nav.evaluate(async el=>{
   function measure(){return [el,...el.querySelectorAll('a, a svg, a span')].flatMap(node=>{const r=node.getBoundingClientRect();return [r.x,r.y,r.width,r.height]})}
   const root=document.documentElement
   root.style.setProperty('--safe-area-bottom','34px')
   const initial=measure();let drift=0
   for(const link of el.querySelectorAll('a')){
    window.scrollTo(0,document.documentElement.scrollHeight)
    link.click()
    const started=performance.now()
    do{
     const elapsed=performance.now()-started
     root.style.setProperty('--safe-area-bottom',elapsed<150?'0px':elapsed<300?'34px':elapsed<450?'10px':'34px')
     await new Promise(requestAnimationFrame)
     measure().forEach((value,i)=>{drift=Math.max(drift,Math.abs(value-initial[i]!))})
    }while(performance.now()-started<600)
   }
   return drift
  })
  expect(drift).toBeLessThan(.02)
  expect(await nav.evaluate(el=>getComputedStyle(el).paddingBottom)).toBe('22px')
  expect(await nav.locator('a.active').evaluate(el=>getComputedStyle(el).fontWeight)).toBe('700')
 }
})
