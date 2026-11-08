import { test,expect } from '@playwright/test'
import { seed,command } from './helpers'

test('phone comments remain editable after scrolling and keyboard-sized viewport changes',async({page,request},info)=>{
 await page.setViewportSize({width:390,height:844})
 const actor=await seed(page,request,'Mobile comment actor')
 await command(request,'wishlist.create',{name:'Phone comment wish',price_minor:4500,description:'A weekend plan.\n'.repeat(24)},actor.id)
 await command(request,'request.create',{item:'Phone comment request',amount_minor:4500,description:'A weekend plan.\n'.repeat(24)},actor.id)
 for(const [route,name] of [['/wish-lists','Phone comment wish'],['/approvals','Phone comment request']]){
  await page.goto(route!)
  await page.getByRole('button',{name,exact:true}).click()
  const dialog=page.getByRole('dialog'),field=page.getByLabel('Comment',{exact:true})
  await field.scrollIntoViewIfNeeded()
  await field.click()
  await field.pressSequentially('First line')
  const top=await dialog.evaluate(el=>el.getBoundingClientRect().top)
  // Approximate the available space with a software keyboard visible.
  await page.setViewportSize({width:390,height:420})
  await field.scrollIntoViewIfNeeded()
  expect(await dialog.evaluate(el=>el.getBoundingClientRect().top)).toBe(top)
  await expect(field).toBeFocused()
  await field.press('Enter')
  await field.pressSequentially('Third line')
  await field.press('Home')
  await field.pressSequentially('Second then ')
  await expect(field).toHaveValue('First line\nSecond then Third line')
  await page.getByRole('button',{name:'Add comment',exact:true}).click()
  await expect(dialog.locator('.comment p').last()).toHaveText('First line\nSecond then Third line')
  await expect(field).toHaveValue('')
  await field.click()
  await field.pressSequentially('Still editable')
  await expect(field).toHaveValue('Still editable')
  await page.screenshot({path:info.outputPath(route!.slice(1)+'.png')})
  await page.setViewportSize({width:390,height:844})
  await page.getByRole('button',{name:'Close dialog'}).click()
 }
})
