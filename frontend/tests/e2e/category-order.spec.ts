import {test,expect,type Locator} from '@playwright/test'
import {seed,command} from './helpers'
import type {Category,Snapshot} from '../../src/api/models'

test('every category dropdown follows Manage categories after reordering and reload',async({page,request})=>{
 const actor=await seed(page,request,'Dropdown order')
 const parent=await command(request,'category.create',{name:'Ordered shared parent',kind:'expense',allows_subcategories:true},actor.id) as Category
 await command(request,'category.create',{name:'Ordered shared child',kind:'expense',parent_id:parent.id},actor.id)
 const archived=await command(request,'category.create',{name:'Ordered archived expense',kind:'expense'},actor.id) as Category
 await command(request,'category.update',{name:archived.name,active:false,expected_revision:archived.revision},actor.id,archived.id)
 const initial=await(await request.get('/api/v1/sync/snapshot')).json() as Snapshot
 const personal=initial.records.categories.find(c=>c.kind==='personal'&&c.owner_id===actor.id&&!c.parent_id)!
 await command(request,'category.create',{name:'Ordered personal child',kind:'personal',owner_id:actor.id,parent_id:personal.id},actor.id)
 for(const category_ids of [[personal.id,parent.id],[parent.id,personal.id,archived.id]]){
  const snapshot=await(await request.get('/api/v1/sync/snapshot')).json() as Snapshot
  const household=snapshot.records.household[0]!
  await command(request,'category.reorder',{expected_revision:household.revision,category_ids},actor.id,household.id)
  await page.goto('/budget');await page.reload()
  await page.getByRole('button',{name:'Manage categories',exact:true}).click()
  await expect(page.locator('.category-row')).toHaveCount(snapshot.records.categories.filter(c=>!c.deleted).length)
  const names=await page.locator('.category-row .row-main strong').allTextContents()
  const managed=names.map(name=>snapshot.records.categories.find(c=>c.name===name)!)
  async function matches(select:Locator,eligible:(c:Category)=>boolean){
   await expect(select).toBeVisible()
   const expected=managed.filter(eligible).map(c=>c.id)
   await expect.poll(()=>select.locator('option').evaluateAll(options=>options.map(o=>(o as HTMLOptionElement).value).filter(Boolean))).toEqual(expected)
  }
  await page.getByRole('button',{name:'Add category',exact:true}).click()
  await page.getByRole('combobox',{name:'Category type',exact:true}).selectOption('subcategory')
  await matches(page.getByRole('combobox',{name:'Parent category',exact:true}),c=>c.active&&!c.parent_id&&(c.kind==='expense'&&!!c.allows_subcategories||c.kind==='personal'&&c.owner_id===actor.id))
  await page.goto('/budget')
  await page.getByText('Monthly bills',{exact:true}).click()
  await page.getByRole('button',{name:'+ Add monthly bill',exact:true}).click()
  await matches(page.getByRole('dialog').getByRole('combobox',{name:'Category',exact:true}),c=>c.active&&c.kind!=='savings')
  await page.goto('/purchases')
  await matches(page.getByRole('combobox',{name:'Category',exact:true}),c=>c.kind!=='savings')
  await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Enter manually',exact:true}).click()
  await matches(page.getByRole('dialog').getByRole('combobox',{name:'Category',exact:true}),c=>c.active&&c.kind!=='savings'&&!c.parent_id)
  await page.goto('/approvals')
  await page.getByRole('button',{name:'Request approval',exact:true}).click()
  await matches(page.getByRole('dialog').getByRole('combobox',{name:'Proposed category',exact:true}),c=>c.active&&c.kind!=='savings')
 }
})
