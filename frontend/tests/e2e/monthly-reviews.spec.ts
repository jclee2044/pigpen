import { expect, test } from '@playwright/test'
import { seed } from './helpers'
import type { Review } from '../../src/api/reviews'
const report:Review={id:'00000000-0000-4000-a000-000000000011',month:'2026-10',created_at:'2026-11-01T13:00:00Z',summary:'Dining increased.',data_changed:false,chat_enabled:true,
 totals:{budgeted_minor:320000,spent_minor:286000,remaining_minor:34000,savings_allocated_minor:0,savings_actual_minor:0,income_minor:320000},coverage:{comparison_months:['2026-08','2026-09'],purchase_count:1,included_purchase_count:1},findings:[{id:'finding-1',kind:'trend',title:'Dining rose 50%',explanation:'$540 spent, up $180 from the prior average.',category_id:null,suggested_category:null,chart:[{label:'2026-08',amount_minor:36000},{label:'2026-09',amount_minor:36000},{label:'2026-10',amount_minor:54000}],purchases:[{id:'00000000-0000-4000-a000-000000000012',item:'Weekend meal',merchant:null,transaction_date:'2026-10-03',amount_minor:8500,category_id:'food',category_explanation:''}]}]}
const summary={id:report.id,month:report.month,created_at:report.created_at,finding_count:1,remaining_minor:34000}

test('requested preview appears above the advisor outside days one to five and expires at month end',async({page,request})=>{
 await page.clock.install({time:new Date('2026-11-22T15:00:00Z')})
 const preview={...summary,month:'2026-11',is_preview:true}
 await page.route('**/api/v1/advisor/reviews',route=>route.fulfill({json:{items:[preview],next_before:null,latest:preview,current_month:'2026-11',show_home:true,enabled:true}}))
 await page.route('**/api/v1/advisor/reviews/2026-11',route=>route.fulfill({json:{...report,month:'2026-11',summary:'Month-to-date preview.'}}))
 await seed(page,request,'Preview card test')
 await page.goto('/')
 const card=page.locator('.monthly-review-card')
 await expect(card).toBeVisible()
 await expect(card).toContainText('November 2026 preview')
 expect(await page.evaluate(()=>document.querySelector('.monthly-review-card')!.getBoundingClientRect().top<document.querySelector('.advisor')!.getBoundingClientRect().top)).toBe(true)
 await card.getByRole('link',{name:'Review analysis'}).click()
 await expect(page.getByText('Month-to-date preview.',{exact:true})).toBeVisible()
 await page.getByRole('link',{name:'‹ Home',exact:true}).click()
 await expect(card).toBeVisible()
 await page.clock.setSystemTime(new Date('2026-12-01T15:00:00Z'))
 await page.clock.runFor(61000)
 await expect(card).toHaveCount(0)
})

test('monthly card survives a visit, disappears after day five, and history remains',async({page,request})=>{
 await page.setViewportSize({width:390,height:844})
 await page.clock.install({time:new Date('2026-11-05T15:00:00Z')})
 await page.route('**/api/v1/advisor/reviews',route=>route.fulfill({json:{items:[summary],next_before:null,latest:summary,current_month:'2026-11',show_home:true,enabled:true}}))
 await page.route('**/api/v1/advisor/reviews/2026-10',route=>route.fulfill({json:report}))
 await seed(page,request,'Monthly review test')
 await page.goto('/')
 const card=page.locator('.monthly-review-card')
 await expect(card).toBeVisible()
 const position=await page.evaluate(()=>({card:document.querySelector('.monthly-review-card')!.getBoundingClientRect().top,advisor:document.querySelector('.advisor')!.getBoundingClientRect().top}))
 expect(position.card).toBeLessThan(position.advisor)
 await page.getByRole('link',{name:'Review analysis',exact:true}).click()
 await expect(page.getByRole('heading',{name:'October 2026 analysis',exact:true})).toBeVisible()
 await page.getByRole('link',{name:'‹ Home',exact:true}).click()
 await expect(card).toBeVisible()
 await page.clock.setSystemTime(new Date('2026-11-06T15:00:00Z'))
 await page.clock.runFor(61000)
 await expect(card).toHaveCount(0)
 await page.getByRole('link',{name:'Review past analyses',exact:true}).click()
 await page.getByRole('link',{name:'October 2026 1 finding →',exact:true}).click()
 await expect(page.getByText('Dining rose 50%',{exact:true})).toBeVisible()
})

test('evidence and report-aware chat work at narrow widths and retain follow-ups',async({page,request})=>{
 await page.setViewportSize({width:320,height:800})
 await page.route('**/api/v1/advisor/reviews/2026-10',route=>route.fulfill({json:{...report,data_changed:true}}))
 const questions:{month:string;review_month:string;finding_id:string;history:{content:string}[]}[]=[]
 await page.route('**/api/v1/advisor/ask',route=>{questions.push(route.request().postDataJSON());return route.fulfill({json:{month:'2026-10',as_of:'2026-11-01',answer:'The saved report includes a weekend meal.',sources:[{label:'View purchase',path:'/purchases?detail='+report.findings[0]!.purchases[0]!.id}]}})})
 await seed(page,request,'Review chat test')
 await page.goto('/analyses/2026-10')
 await expect(page.getByText('Records have changed since this analysis was prepared.',{exact:false})).toBeVisible()
 await page.getByText('View purchases (1)',{exact:true}).click()
 await expect(page.getByRole('link',{name:/Weekend meal/})).toHaveAttribute('href',/\/purchases\?detail=/)
 await page.getByRole('button',{name:'Ask about this',exact:true}).click()
 await page.getByRole('button',{name:'What drove this?',exact:true}).click()
 await expect(page.locator('.review-chat .received')).toContainText('saved report')
 await page.getByLabel('Message Sir Pennysworth about this analysis').fill('What about next month?')
 await page.getByRole('button',{name:'Send analysis question',exact:true}).click()
 await expect(page.locator('.review-chat .received')).toHaveCount(2)
 expect(questions[0]).toMatchObject({month:'2026-10',review_month:'2026-10',finding_id:'finding-1'})
 expect(questions[1]!.history[0]!.content).toContain('Dining rose 50%')
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.getByRole('button',{name:'Close analysis chat',exact:true}).click()
 await expect(page.locator('.review-totals')).toBeVisible()
 await page.evaluate(()=>{(document.activeElement as HTMLElement)?.blur();window.scrollTo(0,0)})
 await expect.poll(()=>page.locator('.app-header').evaluate(el=>el.getBoundingClientRect().top)).toBe(0)
 for(const amount of await page.locator('.review-totals .fit-money').all()){
  expect(await amount.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true)
 }
 await page.screenshot({path:'../output/monthly-analysis/implemented-mobile.png',fullPage:true})
})

test('empty history, unavailable report and quiet report have usable states',async({page,request})=>{
 await page.route('**/api/v1/advisor/reviews',route=>route.fulfill({json:{items:[],next_before:null,latest:null,current_month:'2026-11',show_home:false,enabled:false}}))
 await seed(page,request,'Review empty test')
 await page.goto('/analyses')
 await expect(page.getByText('No analyses yet.',{exact:false})).toBeVisible()
 await page.goto('/analyses/2026-10')
 await expect(page.getByRole('alert')).toContainText('not available yet')
 await page.route('**/api/v1/advisor/reviews/2026-10',route=>route.fulfill({json:{...report,findings:[],summary:'No significant changes stand out.',chat_enabled:false}}))
 await page.getByRole('button',{name:'Retry',exact:true}).click()
 await expect(page.getByText('No significant changes stand out.',{exact:true})).toBeVisible()
 await expect(page.getByText('Chat is currently unavailable.',{exact:true})).toBeVisible()
})
