import type { Category } from '../api/models'

/** Shared categories first, Personal last; children follow their parent. */
export function orderCategories<T extends Pick<Category,'id'|'kind'|'parent_id'>>(categories: readonly T[], order: readonly string[] = []): T[] {
 const positions=new Map(categories.map((category,index)=>[category.id,index]))
 const ranks=new Map(order.map((id,index)=>[id,index]))
 const root=(category:T)=>category.parent_id??category.id
 const rank=(category:T)=>ranks.get(root(category))??order.length+(positions.get(root(category))??positions.get(category.id)??0)
 return [...categories].sort((a,b)=>Number(a.kind==='personal')-Number(b.kind==='personal')||rank(a)-rank(b)||Number(!!a.parent_id)-Number(!!b.parent_id))
}
