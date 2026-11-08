import type { Wish } from '../api/models'
export function orderWishes(items:Wish[],order:string[]=[]){
 const rank=(id:string)=>{const index=order.indexOf(id);return index<0?Infinity:index}
 return [...items].sort((a,b)=>rank(a.id)-rank(b.id)||a.created_at.localeCompare(b.created_at)||a.id.localeCompare(b.id))
}
/** Replace only visible slots, preserving the positions of filtered-out wishes. */
export function mergeWishOrder(all:Wish[],visible:string[]){
 const included=new Set(visible);let index=0
 return all.map(wish=>included.has(wish.id)?visible[index++]!:wish.id)
}
