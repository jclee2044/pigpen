import { test, expect } from '@playwright/test'
import { seed, command } from './helpers'

for(const width of [390,1440])test(`cents preference persists and preserves exact editing at ${width}px`,async({page,request},info)=>{
 await page.setViewportSize({width,height:900})
 const month=width===390?'2035-06':'2035-07'
 const actor=await seed(page,request,`Cents ${width}`)
 await command(request,'budget.set',{month,expected_income_minor:123450,allocations:[]},actor.id)
 await page.goto('/settings')
 const toggle=page.getByRole('switch',{name:'Show cents',exact:true})
 await expect(toggle).toBeChecked()
 await toggle.uncheck()
 await page.reload()
 await expect(toggle).not.toBeChecked()
 await page.screenshot({path:info.outputPath(`settings-${width}.png`),fullPage:true})
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.goto('/budget')
 await page.getByLabel('Budget month',{exact:true}).fill(month)
 await expect(page.locator('.donut-center')).toContainText('$1,235')
 await expect(page.locator('.donut-center')).not.toContainText('.50')
 await page.getByRole('button',{name:'Edit',exact:true}).click()
 await expect(page.getByLabel('Expected income ($)',{exact:true})).toHaveValue('1,234.50')
 await page.getByRole('button',{name:'Close dialog',exact:true}).click()
 await page.goto('/settings');await toggle.check();await page.reload();await expect(toggle).toBeChecked()
 await page.goto('/budget');await expect(page.locator('.donut-center')).toContainText('$1,234.50')
})
