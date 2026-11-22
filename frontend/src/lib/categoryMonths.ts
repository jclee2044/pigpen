import type { Records } from '../api/models'
import { orderCategories } from './categoryOrder'
export const OTHER_CATEGORY_ID='00000000-0000-5000-8000-000000000001'
export function monthRevision(records:Records,month:string){return records['category-months']?.find(x=>!x.deleted&&x.month===month)?.revision??0}
export function monthPlan(records:Records,month:string){
 const months=records['category-months']??[]
 const exact=months.find(x=>!x.deleted&&x.month===month)
 const source=exact??months.filter(x=>!x.deleted&&x.month<month).sort((a,b)=>b.month.localeCompare(a.month))[0]
 const ids=new Set(source?.category_ids??records.categories.filter(x=>x.active&&!x.deleted).map(x=>x.id))
 if(records.categories.some(x=>x.id===OTHER_CATEGORY_ID))ids.add(OTHER_CATEGORY_ID)
 const budget=records['budget-months'].find(x=>!x.deleted&&x.month===(source?.month??month))
 let allocations=budget?records.allocations.filter(x=>!x.deleted&&x.budget_month_id===budget.id):source?.inherited_allocations??[]
 if(!exact)allocations=allocations.filter(x=>ids.has(x.category_id))
 return {ids,allocations,expected:budget?.expected_income_minor??source?.inherited_income_minor??0,established:!!exact}
}
export function monthCategories(records:Records,month:string){
 const ids=monthPlan(records,month).ids
 return orderCategories(records.categories.filter(x=>!x.deleted&&(!x.owner_id||records.users.some(u=>u.id===x.owner_id&&u.active&&!u.deleted))&&ids.has(x.id)&&(!x.parent_id||ids.has(x.parent_id))),records.household[0]?.category_order)
}
