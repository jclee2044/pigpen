import { test,expect } from '@playwright/test'
import { seed,command } from './helpers'

test('recurring budgets, shared empty states and every page at iPhone widths',async({page,request},info)=>{
 test.setTimeout(60000)
 const actor=await seed(page,request,'Mobile review')
 const categories=(await (await request.get('/api/v1/categories')).json()).items
 const food=categories.find((x:{name:string})=>x.name==='Food')
 await command(request,'budget.set',{month:'2031-01',expected_income_minor:100000,allocations:[{category_id:food.id,amount_minor:20000}]},actor.id)
 await page.goto('/budget');await page.getByLabel('Budget month',{exact:true}).fill('2031-04')
 await expect(page.getByRole('button',{name:/Copy previous/})).toHaveCount(0)
 await page.getByRole('button',{name:'Edit',exact:true}).click()
 await expect(page.getByLabel('Food',{exact:true})).toHaveValue('200.00')
 await expect(page.getByLabel('Expected income ($)',{exact:true})).toHaveValue('1000.00')
 await page.getByLabel('Food',{exact:true}).fill('250.00')
 await page.getByRole('button',{name:'Save budget',exact:true}).click()
 await expect(page.getByRole('dialog')).toHaveCount(0)
 await page.getByLabel('Budget month',{exact:true}).fill('2031-07')
 await page.goto('/');await expect(page.getByTestId('allocated')).toHaveText('$250.00')
 expect((await (await request.get('/api/v1/budget-months/2031-07')).json()).allocated_minor).toBe(25000)
 for(const width of [320,375,390,430]){
  await page.setViewportSize({width,height:844})
  for(const route of ['/','/purchases','/budget','/wish-lists','/approvals','/notifications','/profiles','/settings']){
   await page.goto(route);await expect(page.locator('main h1')).toBeVisible()
   if(route==='/wish-lists')await page.getByRole('combobox',{name:'Wish-list owner'}).selectOption(actor.id)
   if(route==='/approvals')await page.getByRole('combobox',{name:'Show requests'}).selectOption('mine')
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${route} at ${width}`).toBe(true)
   const filters=await page.locator('.toolbar input,.toolbar select').evaluateAll(elements=>elements.map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}}))
   for(let i=0;i<filters.length;i++){
    expect(filters[i]!.left).toBeGreaterThanOrEqual(0);expect(filters[i]!.right).toBeLessThanOrEqual(width)
    for(let j=i+1;j<filters.length;j++)expect(filters[i]!.bottom<=filters[j]!.top||filters[j]!.bottom<=filters[i]!.top||filters[i]!.right<=filters[j]!.left||filters[j]!.right<=filters[i]!.left).toBe(true)
   }
   if(['/purchases','/wish-lists','/approvals','/notifications'].includes(route))await expect(page.getByText('Nothing here yet',{exact:true})).toBeVisible()
   if(width===375)await page.screenshot({path:info.outputPath(route.replaceAll('/','')||'dashboard')+'.png',fullPage:true})
  }
  await page.goto('/purchases');await page.getByRole('button',{name:'New purchase',exact:true}).click()
  const dialog=page.getByRole('dialog');await expect(dialog).toBeVisible()
  expect(await dialog.evaluate(e=>e.scrollWidth<=e.clientWidth)).toBe(true)
  await page.getByRole('button',{name:'Close dialog'}).click()
 }
})
