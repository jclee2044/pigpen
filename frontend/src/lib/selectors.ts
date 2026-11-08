import type { Records,Request,Purchase } from '../api/models'
export function summary(records:Records,month:string){
 const budget=records['budget-months'].find(x=>x.month===month&&!x.deleted)
 const plan=budget??records['budget-months'].filter(x=>!x.deleted&&x.month<month).sort((a,b)=>b.month.localeCompare(a.month))[0]
 const allocations=records.allocations.filter(x=>!x.deleted&&x.budget_month_id===plan?.id&&(!!budget||records.categories.some(c=>c.id===x.category_id&&c.active&&!c.deleted)))
 const purchases=records.purchases.filter(x=>!x.deleted&&x.transaction_date.slice(0,7)===month)
 const categories=records.categories.filter(x=>!x.deleted)
 const savings=records.savings.filter(x=>!x.deleted&&x.transaction_date.slice(0,7)===month&&x.kind!=='opening')
 const netSavings=savings.reduce((n,x)=>n+(x.kind==='withdrawal'?-x.amount_minor:x.amount_minor),0)
 const rows=categories.filter(x=>!x.parent_id).map(category=>{
  const allocated=allocations.find(x=>x.category_id===category.id)?.amount_minor??0
  const actual=category.kind==='savings'?netSavings:purchases.filter(x=>x.category_id===category.id||categories.find(c=>c.id===x.category_id)?.parent_id===category.id).reduce((n,x)=>n+x.amount_minor,0)
  return {...category,allocated,actual,remaining:allocated-actual}
 })
 const allocated=rows.reduce((n,x)=>n+x.allocated,0),spent=purchases.reduce((n,x)=>n+x.amount_minor,0)
 return {budget,rows,allocated,spent,remaining:rows.reduce((n,x)=>n+x.remaining,0),expected:plan?.expected_income_minor??0,
  actualIncome:records.income.filter(x=>!x.deleted&&x.transaction_date.slice(0,7)===month).reduce((n,x)=>n+x.amount_minor,0),
  savingsBalance:records.savings.filter(x=>!x.deleted&&x.transaction_date.slice(0,7)<=month).reduce((n,x)=>n+(x.kind==='withdrawal'?-x.amount_minor:x.amount_minor),0),netSavings}
}
export function approved(request:Request,records:Records){
 if(request.status==='purchased')return true
 if(request.status!=='open'||!records.users.some(x=>x.id===request.requester_id&&x.active))return false
 const reviewers=records.users.filter(x=>x.active&&!x.deleted&&x.id!==request.requester_id)
 return reviewers.length>0&&reviewers.every(user=>records['approval-votes'].some(v=>!v.deleted&&v.request_id===request.id&&v.reviewer_id===user.id&&v.approved&&v.request_revision===request.revision))
}
export const recent=(purchases:Purchase[])=>[...purchases].sort((a,b)=>b.transaction_date.localeCompare(a.transaction_date)||b.created_at.localeCompare(a.created_at))
export function occurrences(records:Records,month:string){
 const year=Number(month.slice(0,4)),number=Number(month.slice(5,7)),lastDay=new Date(Date.UTC(year,number,0)).getUTCDate()
 return records['recurring-bills'].filter(b=>!b.deleted).flatMap(b=>{
  const existing=records['bill-occurrences'].find(x=>!x.deleted&&'bill_id' in x&&(x as unknown as {bill_id:string}).bill_id===b.id&&'due_date' in x&&String((x as unknown as {due_date:string}).due_date).startsWith(month)) as unknown as {due_date:string;expected_minor:number;purchase_id:string}|undefined
  const due=existing?.due_date??`${month}-${String(Math.min(lastDay,b.due_day)).padStart(2,'0')}`
  return !existing&&(!b.active||due<b.start_date)?[]:[{id:b.id+'/'+due,bill_id:b.id,name:b.name,due_date:due,expected_minor:existing?.expected_minor??b.amount_minor,purchase_id:existing?.purchase_id??null}]
 }).sort((a,b)=>a.due_date.localeCompare(b.due_date))
}
