import {test,expect} from '@playwright/test'
import {seed,command} from './helpers'
import type {User,Wish,Snapshot} from '../../src/api/models'
test('any profile reorders other owners and mixed lists; another device sees the shared order',async({page,request,browser})=>{
 const actor=await seed(page,request,'Shared order actor')
 const other=await command(request,'user.create',{name:'Shared order other'}) as User
 const wishes:Wish[]=[]
 for(const [name,owner] of [['Other first',other.id],['Actor middle',actor.id],['Other last',other.id]])wishes.push(await command(request,'wishlist.create',{name:name!,price_minor:100},owner!) as Wish)
 await page.goto('/wish-lists')
 for(const wish of wishes)await expect(page.getByRole('button',{name:'Reorder '+wish.name,exact:true})).toBeVisible()
 const device=await browser.newContext({baseURL:'http://127.0.0.1:5173'}),second=await device.newPage()
 try{
  await second.goto('/profiles');await second.getByRole('button',{name:new RegExp(other.name)}).click();await expect(second.getByTestId('selected-profile')).toHaveText(other.name)
  // Move the actor's own wish across an item belonging to someone else.
  const handle=page.getByRole('button',{name:'Reorder Actor middle',exact:true})
  await handle.focus();await page.keyboard.press('ArrowUp');await expect(handle).toBeEnabled()
  async function stored(){return (await(await request.get('/api/v1/sync/snapshot')).json() as Snapshot).records.household[0]!.wishlist_order!.filter(id=>wishes.some(w=>w.id===id))}
  await expect.poll(stored).toEqual([wishes[1]!.id,wishes[0]!.id,wishes[2]!.id])
  await second.goto('/wish-lists');await second.getByLabel('Wish-list owner').selectOption(actor.id)
  await expect(second.getByRole('button',{name:'Reorder Actor middle',exact:true})).toBeVisible()
  // Actor changes another owner's order through the owner filter.
  await page.getByLabel('Wish-list owner').selectOption(other.id)
  const otherHandle=page.getByRole('button',{name:'Reorder Other last',exact:true})
  await otherHandle.focus();await page.keyboard.press('ArrowUp');await expect(otherHandle).toBeEnabled()
  await expect.poll(stored).toEqual([wishes[1]!.id,wishes[2]!.id,wishes[0]!.id])
  await second.reload();await second.getByLabel('Wish-list owner').selectOption(other.id)
  await expect(second.locator('.wish-card h2')).toHaveText(['Other last','Other first'])
  // The second profile can change the same shared list back.
  const secondHandle=second.getByRole('button',{name:'Reorder Other first',exact:true})
  await secondHandle.focus();await second.keyboard.press('ArrowUp');await expect(secondHandle).toBeEnabled()
  await expect.poll(stored).toEqual([wishes[1]!.id,wishes[0]!.id,wishes[2]!.id])
  await page.reload();await page.getByLabel('Wish-list owner').selectOption(other.id)
  await expect(page.locator('.wish-card h2')).toHaveText(['Other first','Other last'])
 }finally{await device.close()}
})
