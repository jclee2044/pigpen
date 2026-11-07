import { test,expect } from '@playwright/test'
test('onboarding, profiles and responsive routes persist after reload',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Welcome to PigPen'})).toBeVisible()
 await page.getByLabel('Household name').fill('Synthetic household');await page.getByRole('button',{name:'Create household',exact:true}).click()
 await page.getByLabel('Display name').fill('Alex');await page.getByRole('combobox',{name:'Hat',exact:true}).selectOption('beanie');await page.getByRole('button',{name:'Create profile',exact:true}).click()
 await expect(page.getByRole('heading',{name:'Dashboard',exact:true})).toBeVisible()
 await page.reload();await expect(page.locator('.profile-link strong')).toHaveText('Alex')
 await page.getByRole('navigation',{name:'Main navigation',exact:true}).getByRole('link',{name:'Purchases'}).click()
 await expect(page.getByRole('heading',{name:'Purchases',exact:true})).toBeVisible()
 await page.setViewportSize({width:390,height:844});await page.goto('/budget')
 await expect(page.getByRole('navigation',{name:'Mobile navigation'})).toBeVisible()
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.goto('/profiles');await page.getByRole('button',{name:'Edit name & avatar'}).click();await expect(page.getByRole('combobox',{name:'Hat',exact:true})).toHaveValue('beanie')
})
