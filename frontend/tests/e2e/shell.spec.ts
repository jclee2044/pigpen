import { test,expect } from '@playwright/test'
test('responsive shell and direct routes',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible()
 await page.getByRole('navigation',{name:'Main navigation',exact:true}).getByRole('link',{name:'Purchases'}).click()
 await expect(page.getByRole('heading',{name:'Purchases',exact:true})).toBeVisible()
 await page.setViewportSize({width:390,height:844});await page.goto('/budget')
 await expect(page.getByRole('navigation',{name:'Mobile navigation'})).toBeVisible()
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
})
