import { test, expect } from '@playwright/test'
import { seed } from './helpers'

for (const width of [390, 1440]) {
 test(`dark appearance stays readable and persists at ${width}px`, async ({page,request}, info) => {
  await page.setViewportSize({width,height:900})
  await seed(page,request,`Appearance ${width}`)
  await page.getByRole('button',{name:'Our household',exact:true}).click()
  const settings=page.getByRole('link',{name:'Settings',exact:true})
  await expect(settings.locator('svg path')).toHaveAttribute('d',/^m9\.5 3/)
  await settings.click()
  const toggle=page.getByRole('switch',{name:'Dark mode',exact:true})
  await expect(toggle).not.toBeChecked()
  const headerBefore=await page.locator('.app-header').evaluate(el=>({background:getComputedStyle(el).backgroundColor,color:getComputedStyle(el).color,logo:el.querySelector('.brand-logo')?.outerHTML}))
  await toggle.check()
  await expect(page.locator('html')).toHaveAttribute('data-theme','dark')
  await page.reload()
  await expect(toggle).toBeChecked()
  const headerAfter=await page.locator('.app-header').evaluate(el=>({background:getComputedStyle(el).backgroundColor,color:getComputedStyle(el).color,logo:el.querySelector('.brand-logo')?.outerHTML}))
  expect(headerAfter).toEqual(headerBefore)
  await page.screenshot({path:info.outputPath(`settings-${width}.png`),fullPage:true})
  for(const route of ['/','/budget','/purchases','/approvals','/wish-lists','/notifications','/profiles','/settings']) {
   await page.goto(route)
   await expect(page.locator('main h1').first()).toBeVisible()
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
   // Check the actual rendered foreground/background for each visible text node.
   const failures=await page.locator('main').evaluate(main=>{
    const rgb=(value:string)=>value.match(/[\d.]+/g)!.map(Number)
    const luminance=(value:string)=>rgb(value).slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i]!,0)
    const failures:string[]=[]
    for(const el of main.querySelectorAll<HTMLElement>('*')) {
     if(!el.getClientRects().length||!Array.from(el.childNodes).some(n=>n.nodeType===Node.TEXT_NODE&&n.textContent?.trim()))continue
     const style=getComputedStyle(el)
     if(style.visibility==='hidden')continue
     let ancestor:Element|null=el,background=''
     while(ancestor){const color=getComputedStyle(ancestor).backgroundColor;if(rgb(color)[3]!==0){background=color;break}ancestor=ancestor.parentElement}
     if(!background)continue
     const a=luminance(style.color),b=luminance(background),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05)
     const large=parseFloat(style.fontSize)>=24||(parseFloat(style.fontSize)>=18.66&&parseInt(style.fontWeight)>=700)
     if(ratio<(large?3:4.5))failures.push(`${el.textContent?.trim().slice(0,50)}: ${ratio.toFixed(2)} (${style.color} on ${background})`)
    }
    return failures
   })
   expect(failures,route).toEqual([])
   if(route==='/'||route==='/budget')await page.screenshot({path:info.outputPath(`${route==='/'?'dashboard':'budget'}-${width}.png`),fullPage:true})
   if(route==='/purchases'){
    await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Enter manually',exact:true}).click()
    await expect(page.locator('dialog')).toHaveCSS('background-color','rgb(25, 23, 27)')
    await expect(page.getByLabel('Item or service')).toHaveCSS('background-color','rgb(37, 34, 40)')
    await page.screenshot({path:info.outputPath(`form-${width}.png`),fullPage:true})
    await page.getByRole('button',{name:'Close dialog',exact:true}).click()
   }
  }
  await toggle.uncheck()
  await page.reload()
  await expect(toggle).not.toBeChecked()
  await expect(page.locator('.refresh-content')).toHaveCSS('background-color','rgb(255, 248, 247)')
 })
}
