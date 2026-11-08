import { test,expect } from '@playwright/test'
import { createServer } from 'node:http'
import { readFileSync } from 'node:fs'
import { resolve,extname } from 'node:path'
import { seed } from './helpers'

test('opening, foregrounding and pulling sync before automatic updates; current or failed sync never reloads',async({browser,request})=>{
 let revision=0,workerChecks=0,syncFailure=false
 const dist=resolve('dist')
 // A private disposable origin serves two real worker revisions without changing dist.
 const server=createServer(async(req,res)=>{
  try{
   const path=new URL(req.url!,'http://localhost').pathname
   if(path.startsWith('/api/')){
    if(syncFailure&&path==='/api/v1/sync/pull'){res.writeHead(503,{'content-type':'application/json'});res.end(JSON.stringify({detail:'Synthetic unavailable server'}));return}
    const chunks:Buffer[]=[];for await(const chunk of req)chunks.push(Buffer.from(chunk))
    const response=await fetch('http://127.0.0.1:8879'+req.url,{method:req.method,headers:{'content-type':'application/json'},body:['GET','HEAD'].includes(req.method!)?undefined:Buffer.concat(chunks)})
    res.writeHead(response.status,{'content-type':response.headers.get('content-type')||'application/json','cache-control':'no-store'})
    res.end(Buffer.from(await response.arrayBuffer()));return
   }
   if(path==='/sw.js'){
    workerChecks++
    res.writeHead(200,{'content-type':'text/javascript','cache-control':'no-store','service-worker-allowed':'/'})
    res.end(readFileSync(resolve(dist,'sw.js'),'utf8')+`\nself.addEventListener('message',event=>{if(event.data?.type==='TEST_VERSION')event.ports[0].postMessage(${revision})})`);return
   }
   const file=path==='/'||!extname(path)?'index.html':path.slice(1)
   const mime:Record<string,string>={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.webmanifest':'application/manifest+json','.png':'image/png','.svg':'image/svg+xml'}
   res.writeHead(200,{'content-type':mime[extname(file)]||'application/octet-stream','cache-control':'no-store'})
   res.end(readFileSync(resolve(dist,file)))
  }catch{res.writeHead(500);res.end()}
 })
 await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve))
 const address=server.address() as {port:number}
 const context=await browser.newContext({baseURL:'http://127.0.0.1:'+address.port,viewport:{width:390,height:844}})
 try{
  let page=await context.newPage()
  await seed(page,request,'App update actor')
  await expect.poll(()=>page.evaluate(()=>!!navigator.serviceWorker.controller)).toBe(true)
  const workerVersion=()=>page.evaluate(()=>new Promise<number>(resolve=>{const channel=new MessageChannel();channel.port1.onmessage=event=>{channel.port1.close();resolve(event.data)};navigator.serviceWorker.controller!.postMessage({type:'TEST_VERSION'},[channel.port2])}))
  const mark=()=>page.evaluate(()=>{Reflect.set(window,'beforeAppUpdate',true)})
  const pull=()=>page.evaluate(()=>{
   scrollTo(0,0)
   const el=document.querySelector('main')!
   for(const [type,y] of [['touchstart',220],['touchmove',390],['touchend',390]] as const){
    const touch=new Touch({identifier:1,target:el,clientX:180,clientY:y})
    el.dispatchEvent(new TouchEvent(type,{bubbles:true,cancelable:true,touches:type==='touchend'?[]:[touch],changedTouches:[touch]}))
   }
  })
  await expect(page.getByRole('button',{name:'Update app',exact:true})).toHaveCount(0)
  await expect.poll(()=>workerChecks).toBeGreaterThanOrEqual(2)
  await page.waitForTimeout(650) // Let the initial automatic update check settle before changing the served revision.
  await expect(page.locator('.sync-loading')).toHaveCount(0)
  let release!:()=>void
  const gate=new Promise<void>(resolve=>{release=resolve})
  let requested=false
  await page.route('**/api/v1/sync/pull?**',async route=>{requested=true;await gate;await route.continue()})
  await mark();revision=1
  const before=workerChecks
  await pull()
  await expect.poll(()=>requested).toBe(true)
  await expect(page.locator('.pull-refresh')).toHaveClass(/refreshing/)
  expect(await workerVersion()).toBe(0) // Never activate ahead of saved-data synchronization.
  const reloaded=page.waitForEvent('domcontentloaded')
  release();await reloaded
  await expect.poll(()=>page.evaluate(()=>Reflect.get(window,'beforeAppUpdate')===undefined)).toBe(true)
  await expect(page.getByTestId('selected-profile')).toHaveText('App update actor')
  expect(workerChecks).toBeGreaterThan(before)
  await page.unroute('**/api/v1/sync/pull?**')
  // Same version: synchronize and check, without a page reload.
  await mark();await pull()
  await expect(page.locator('.pull-refresh')).toHaveClass(/refreshing/)
  await expect(page.locator('.pull-refresh')).not.toHaveClass(/refreshing/)
  expect(await page.evaluate(()=>Reflect.get(window,'beforeAppUpdate'))).toBe(true)
  // Returning to an already-open app uses the same sync-before-update path.
  revision=2
  await mark()
  await page.evaluate(()=>{const dialog=document.createElement('dialog');dialog.id='update-safety-test';document.body.append(dialog);dialog.showModal();window.dispatchEvent(new Event('focus'))})
  await expect.poll(()=>page.evaluate(async()=>!!(await navigator.serviceWorker.getRegistration())?.waiting)).toBe(true)
  expect(await workerVersion()).toBe(1)
  expect(await page.evaluate(()=>Reflect.get(window,'beforeAppUpdate'))).toBe(true)
  await page.evaluate(()=>document.querySelector('#update-safety-test')!.remove())
  const foregroundReload=page.waitForEvent('domcontentloaded')
  await page.evaluate(()=>window.dispatchEvent(new Event('focus')))
  await foregroundReload
  await expect.poll(workerVersion).toBe(2)
  await expect(page.getByRole('button',{name:'Update app',exact:true})).toHaveCount(0)
  // Opening the app again also applies a newer worker automatically.
  await page.close()
  revision=3
  page=await context.newPage()
  await page.goto('/')
  await expect.poll(()=>workerVersion().catch(()=>-1)).toBe(3)
  await expect(page.getByTestId('selected-profile')).toHaveText('App update actor')
  await expect(page.locator('.sync-loading')).toHaveCount(0)
  await mark()
  // Failed data synchronization: never activate the newer version.
  syncFailure=true
  revision=4
  await pull()
  await expect(page.locator('.pull-refresh')).toHaveClass(/refreshing/)
  await expect(page.locator('.pull-refresh')).not.toHaveClass(/refreshing/)
  await expect(page.getByRole('alert')).toBeVisible()
  expect(await workerVersion()).toBe(3) // Background browser checks may download revision 4; never activate it here.
  expect(await page.evaluate(()=>Reflect.get(window,'beforeAppUpdate'))).toBe(true)
 }finally{
  await context.close();server.closeAllConnections()
  await new Promise<void>(resolve=>server.close(()=>resolve()))
 }
})
