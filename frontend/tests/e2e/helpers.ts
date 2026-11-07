import { expect,type Page,type APIRequestContext } from '@playwright/test'
import type { Kind,Payloads } from '../../src/api/generated'
import type { User,Snapshot } from '../../src/api/models'
export async function command<K extends Kind>(request:APIRequestContext,kind:K,data:Payloads[K],actor:string|null=null,entity=crypto.randomUUID()){
 const response=await request.post('/api/v1/operations',{data:{operation_id:crypto.randomUUID(),entity_id:entity,actor_id:actor,client_time:new Date().toISOString(),kind,data}})
 expect(response.ok(),await response.text()).toBeTruthy();return (await response.json()).result
}
export async function seed(page:Page,request:APIRequestContext,label:string){
 const snapshot=await (await request.get('/api/v1/sync/snapshot')).json() as Snapshot
 if(!snapshot.records.household.length)await command(request,'household.initialize',{name:'Synthetic household'})
 const user=await command(request,'user.create',{name:label}) as User
 await page.goto('/profiles');await page.getByRole('button',{name:new RegExp(label)}).click()
 await expect(page.locator('.profile-link strong')).toHaveText(label)
 return user
}
