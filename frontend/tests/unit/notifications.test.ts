import { expect,test } from 'vitest'
import { noteLabel,noteLink } from '../../src/lib/notifications'
import type { Note } from '../../src/api/models'

test('inbox and banner use the persisted preview with compatible legacy labels',()=>{
 const note={kind:'wishlist.created',message:'Alex just added "Switch 2" to the wish list',target_resource:'wishlist-items',target_id:'wish'} as Note
 expect(noteLabel(note)).toBe('Alex just added "Switch 2" to the wish list')
 expect(noteLabel({...note,message:''})).toBe('Wish added')
 expect(noteLabel({...note,message:undefined})).toBe('Wish added')
 expect(noteLink({...note,kind:'purchase.created',target_resource:'purchases',target_id:'purchase'})).toBe('/purchases?detail=purchase')
})
