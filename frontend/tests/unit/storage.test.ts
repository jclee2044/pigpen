import 'fake-indexeddb/auto'
import { it,expect,vi } from 'vitest'
import { savePending,pending,removePending,writeMeta,readMeta } from '../../src/lib/storage'
import { operation } from '../../src/api/client'
it('durably stores the original actor/payload and independent actions',async()=>{
 const op=operation('purchase.delete',{expected_revision:1},crypto.randomUUID())
 await savePending({operation:op,state:'uncertain'})
 expect((await pending()).find(x=>x.operation.operation_id===op.operation_id)?.operation).toEqual(op)
 await writeMeta('selected-profile',crypto.randomUUID())
 expect((await pending())[0]?.operation.actor_id).toBe(op.actor_id)
 await removePending(op.operation_id);expect(await pending()).toEqual([])
 await writeMeta('cache',{cursor:1});expect(await readMeta('cache')).toEqual({cursor:1})
})

it('does not report a saved action when its storage transaction aborts',async()=>{
 const original=IDBObjectStore.prototype.put
 const mock=vi.spyOn(IDBObjectStore.prototype,'put').mockImplementation(function(this:IDBObjectStore,value:unknown,key?:IDBValidKey){const result=Reflect.apply(original,this,key===undefined?[value]:[value,key]) as IDBRequest;if(this.name==='pending')this.transaction.abort();return result})
 const op=operation('purchase.delete',{expected_revision:1},crypto.randomUUID())
 await expect(savePending({operation:op,state:'queued'})).rejects.toThrow()
 mock.mockRestore()
 expect((await pending()).some(x=>x.operation.operation_id===op.operation_id)).toBe(false)
})
