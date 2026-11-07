import 'fake-indexeddb/auto'
import { it,expect } from 'vitest'
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
