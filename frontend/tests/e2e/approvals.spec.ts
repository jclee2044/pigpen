import { test,expect } from '@playwright/test'
import { seed,command } from './helpers'
import type { User,Request } from '../../src/api/models'
test('wish comments, unanimous approval and a linked purchase',async({page,request})=>{
 const requester=await seed(page,request,'Requester');const reviewer=await command(request,'user.create',{name:'Reviewer'}) as User;await page.reload()
 await page.goto('/wish-lists');await page.getByRole('button',{name:'Add wish'}).click();await page.getByLabel('Wish name').fill('Picnic basket');await page.getByLabel('Price ($)',{exact:true}).fill('45.00');await page.getByRole('button',{name:'Save wish',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0)
 const card=page.locator('.wish-card').filter({hasText:'Picnic basket'})
 await expect(page.getByRole('button',{name:'View wish',exact:true})).toHaveCount(0)
 await expect(page.getByRole('button',{name:'Ask for approval',exact:true})).toHaveCount(0)
 for(const width of [390,1440]){
  await page.setViewportSize({width,height:900})
  await card.click({position:{x:8,y:8}})
  await expect(page.getByRole('dialog').getByRole('heading',{name:'Picnic basket',exact:true})).toBeVisible()
  await expect(page.getByRole('dialog').getByRole('button',{name:'Ask for approval',exact:true})).toBeVisible()
  await page.keyboard.press('Escape')
 }
 const openWish=page.getByRole('button',{name:'Picnic basket',exact:true})
 await openWish.focus();await page.keyboard.press('Enter')
 await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape')
 await openWish.focus();await page.keyboard.press('Space')
 await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape')
 await openWish.click();await page.getByLabel('Say something...',{exact:true}).fill('For slow weekends together.');await page.getByRole('button',{name:'Add comment',exact:true}).click();await expect(page.getByText('For slow weekends together.',{exact:true})).toBeVisible();await page.getByRole('dialog').getByRole('button',{name:'Ask for approval',exact:true}).click();await expect(page.getByLabel('Proposed purchase')).toHaveValue('Picnic basket');await page.getByRole('button',{name:'Submit request',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0)
 await page.goto('/approvals');await expect(page.getByRole('article',{name:'Picnic basket',exact:true}).getByRole('button',{name:'Approve',exact:true})).toHaveCount(0)
 await page.goto('/profiles');await page.getByRole('button',{name:/Reviewer/}).click();await expect(page.getByTestId('selected-profile')).toHaveText('Reviewer');await page.goto('/approvals');await page.getByRole('article',{name:'Picnic basket',exact:true}).getByRole('button',{name:'Approve',exact:true}).click();await expect(page.getByRole('article',{name:'Picnic basket',exact:true}).getByRole('button',{name:'Approved',exact:true})).toBeDisabled()
 const proposal=(await (await request.get('/api/v1/approval-requests')).json()).items.find((x:Request)=>x.item==='Picnic basket') as Request
 const users=(await (await request.get('/api/v1/users')).json()).items as User[]
 for(const user of users.filter(x=>x.active&&![requester.id,reviewer.id].includes(x.id)))await command(request,'vote.set',{request_id:proposal.id,request_revision:proposal.revision,approved:true},user.id)
 await page.reload();await page.getByRole('article',{name:'Picnic basket',exact:true}).getByRole('button',{name:'Record approved purchase'}).click();await page.getByRole('combobox',{name:'Category',exact:true}).selectOption({label:'Food'});await page.getByLabel('Transaction date',{exact:true}).fill('2025-02-01');await page.getByRole('button',{name:'Save purchase',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0)
 const final=await (await request.get('/api/v1/records/approval-requests/'+proposal.id)).json();expect(final.status).toBe('purchased');expect(final.approved).toBe(true)
 const purchases=(await (await request.get('/api/v1/purchases?month=2025-02')).json()).items;expect(purchases.filter((x:{request_id:string})=>x.request_id===proposal.id)).toHaveLength(1)
 await page.goto('/notifications');await page.getByRole('button',{name:'Requester submitted "Picnic basket" for approval',exact:true}).click();await expect(page.getByRole('article',{name:'Picnic basket',exact:true})).toBeVisible();await expect(page.getByRole('dialog').getByRole('heading',{name:'Picnic basket',exact:true})).toBeVisible()
 const notes=(await (await request.get('/api/v1/notifications?recipient_id='+reviewer.id)).json()).items;expect(notes.find((n:{kind:string})=>n.kind==='request.created').read_at).toBeTruthy()
})
