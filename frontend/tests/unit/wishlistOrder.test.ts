import {describe,it,expect} from 'vitest'
import {orderWishes,mergeWishOrder} from '../../src/lib/wishlistOrder'
import type {Wish} from '../../src/api/models'
const wish=(id:string,owner='owner',date='2026-11-08T12:00:00Z')=>({id,owner_id:owner,created_at:date}) as Wish
describe('wish order',()=>{
 it('keeps hidden wishes in place when a filtered subset moves',()=>{
  const items=['a','hidden','b','c'].map(id=>wish(id))
  expect(mergeWishOrder(items,['c','a','b'])).toEqual(['c','hidden','a','b'])
 })
 it('shares one order across owners and appends new wishes',()=>{
  const items=[wish('a'),wish('b'),wish('c'),wish('x','other'),wish('y','other')]
  expect(orderWishes(items,['b','y','a','x']).map(w=>w.id)).toEqual(['b','y','a','x','c'])
 })
})
