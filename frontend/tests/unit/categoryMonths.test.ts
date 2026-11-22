import {describe,it,expect} from 'vitest'
import {emptyRecords,type Category,type CategoryMonth,type Budget,type Allocation,type Purchase} from '../../src/api/models'
import {monthCategories,OTHER_CATEGORY_ID} from '../../src/lib/categoryMonths'
import {summary} from '../../src/lib/selectors'
const row={household_id:'h',revision:1,deleted:false,created_at:'now',updated_at:'now'}
const category=(id:string)=>({...row,id,name:id,kind:'expense',owner_id:null,parent_id:null,active:true}) as Category
const month=(value:string,ids:string[],amount=5000)=>({...row,id:value,month:value,category_ids:ids,inherited_allocations:[{category_id:'food',amount_minor:amount}],inherited_income_minor:10000}) as CategoryMonth
function fixture(){const r=emptyRecords();r.categories=[category('food'),category('project'),category(OTHER_CATEGORY_ID)];r['category-months']=[month('2040-01',['food','project']),month('2040-02',['project']),month('2040-03',['food','project'])];return r}
describe('monthly categories',()=>{
 it('keeps removed allocations visible without offering removed categories',()=>{const r=fixture();expect(monthCategories(r,'2040-02').map(x=>x.id)).toEqual(['project',OTHER_CATEGORY_ID]);const result=summary(r,'2040-02');expect(result.allocated).toBe(5000);expect(result.rows.find(x=>x.id==='food')?.active).toBe(false);expect(summary(r,'2040-01').rows.find(x=>x.id==='food')?.active).toBe(true)})
 it('excludes removed money only when inheriting into a new month',()=>{const r=fixture();r['category-months'].pop();expect(summary(r,'2040-03').allocated).toBe(0);expect(summary(r,'2040-03').expected).toBe(10000);expect(summary(r,'2040-02').allocated).toBe(5000)})
 it('preserves an established later month after editing an earlier plan',()=>{const r=fixture();r['budget-months']=[{...row,id:'budget',month:'2040-01',expected_income_minor:20000} as Budget];r.allocations=[{...row,id:'allocation',budget_month_id:'budget',category_id:'food',amount_minor:9000} as Allocation];expect(summary(r,'2040-01').allocated).toBe(9000);expect(summary(r,'2040-03').allocated).toBe(5000)})
 it('retains removed parent spending and Other in historical totals',()=>{const r=fixture();r.categories.push({...category('child'),parent_id:'food'});r.purchases=[{...row,id:'p',category_id:'child',amount_minor:250,transaction_date:'2040-02-02'} as Purchase,{...row,id:'other',category_id:OTHER_CATEGORY_ID,category_explanation:'Permit',amount_minor:150,transaction_date:'2040-02-02'} as Purchase];const result=summary(r,'2040-02');expect(result.spent).toBe(400);expect(result.rows.find(x=>x.id==='food')?.actual).toBe(250);expect(result.rows.find(x=>x.id===OTHER_CATEGORY_ID)?.actual).toBe(150)})
 it('does not interpret an explicitly empty membership as inheritance',()=>{const r=fixture();r['category-months']=[month('2040-01',[])];expect(monthCategories(r,'2040-02').map(x=>x.id)).toEqual([OTHER_CATEGORY_ID])})
})
