import { describe,it,expect } from 'vitest'
import 'fake-indexeddb/auto'
import { applyPage } from '../../src/lib/sync'
import { emptyRecords,type Row } from '../../src/api/models'
import { commitCache,readMeta } from '../../src/lib/storage'
const record=(id:string,revision:number,deleted=false)=>({id,revision,deleted,created_at:'now',updated_at:'now',household_id:'h'}) as Row
describe('sync read model',()=>{
 it('applies revision snapshots and tombstones',()=>{const base={cursor:0,records:emptyRecords()};const next=applyPage(base,{changes:[{cursor:1,resource:'purchases',record:record('p',1)},{cursor:2,resource:'purchases',record:record('p',2,true)}],next_cursor:2,has_more:false});expect(next.records.purchases).toHaveLength(1);expect(next.records.purchases[0]?.deleted).toBe(true);expect(base.records.purchases).toHaveLength(0)})
 it('does not advance a cursor past an invalid page',()=>{const base={cursor:0,records:emptyRecords()};expect(()=>applyPage(base,{changes:[],next_cursor:1,has_more:false})).toThrow();expect(base.cursor).toBe(0)})
 it('keeps a newer committed cache when another tab finishes an older request',async()=>{const base={records:emptyRecords(),lastSync:'now'};await commitCache({...base,cursor:20});await commitCache({...base,cursor:10});expect((await readMeta<{cursor:number}>('cache'))?.cursor).toBe(20)})
})

it('authoritative recovery replaces an invalid cursor without erasing pending actions',async()=>{
 const {savePending,pending}=await import('../../src/lib/storage')
 const {operation}=await import('../../src/api/client')
 const op=operation('purchase.delete',{expected_revision:1},crypto.randomUUID())
 await savePending({operation:op,state:'uncertain'})
 await commitCache({cursor:1,records:emptyRecords(),lastSync:'recovered'},true)
 expect((await readMeta<{cursor:number}>('cache'))?.cursor).toBe(1)
 expect((await pending()).some(x=>x.operation.operation_id===op.operation_id)).toBe(true)
})
