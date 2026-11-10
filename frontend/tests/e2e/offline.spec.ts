import { test,expect } from '@playwright/test'
import { seed,command } from './helpers'
import type { User,Snapshot } from '../../src/api/models'
test('offline entry retains its original profile and syncs once after reconnect',async({page,context,request})=>{
 const actor=await seed(page,request,'Offline actor');const other=await command(request,'user.create',{name:'Offline switch'}) as User;await page.reload();await page.goto('/profiles');await expect(page.getByRole('button',{name:/Offline switch/})).toBeVisible();await page.goto('/purchases')
 await context.setOffline(true);await expect(page.getByText('Offline · saved on this device',{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'New purchase',exact:true}).click();await page.getByRole('button',{name:'Enter manually',exact:true}).click();await page.getByLabel('Item or service').fill('Offline notebook');await page.getByLabel('Amount ($)',{exact:true}).fill('9.99');await page.getByLabel('Transaction date',{exact:true}).fill('2025-03-01');await page.getByRole('dialog').getByRole('combobox',{name:'Category',exact:true}).selectOption({label:'Food'});await page.getByRole('button',{name:'Save',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0);await page.getByRole('link',{name:'PigPen home',exact:true}).click();await expect(page.getByText('1 purchase waiting to sync.',{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Our household',exact:true}).click();await page.getByRole('link',{name:'Profiles',exact:true}).click();await page.getByRole('button',{name:/Offline switch/}).click();await expect(page.getByTestId('selected-profile')).toHaveText('Offline switch')
 await context.setOffline(false);await page.evaluate(()=>window.dispatchEvent(new Event('focus')));await expect(page.getByText('1 purchase waiting to sync.',{exact:true})).toHaveCount(0)
 await expect.poll(async()=>{const snapshot=await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot;return snapshot.records.purchases.filter(p=>p.item==='Offline notebook').length}).toBe(1)
 const purchases=(await (await request.get('/api/v1/purchases?month=2025-03')).json()).items;expect(purchases.find((x:{item:string})=>x.item==='Offline notebook').purchaser_id).toBe(actor.id)
 const binding=await page.evaluate(async()=>{const req=indexedDB.open('pigpen-v1',1);return await new Promise<string>(resolve=>{req.onsuccess=()=>{const get=req.result.transaction('meta').objectStore('meta').get('device');get.onsuccess=()=>resolve(get.result)}})})
 await expect.poll(async()=>{const response=await request.get('/api/v1/installations/'+binding);return (await response.json()).installation.user_id}).toBe(other.id)
})
