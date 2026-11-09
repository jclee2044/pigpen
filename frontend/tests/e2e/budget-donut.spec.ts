import {test,expect} from '@playwright/test'
import {seed,command} from './helpers'

test('budget wheel selects by tap, drag, touch and keyboard with income percentages',async({page,request},info)=>{
 const actor=await seed(page,request,'Donut explorer')
 const first=await command(request,'category.create',{name:'Wheel food',kind:'expense'},actor.id)
 const second=await command(request,'category.create',{name:'Wheel housing',kind:'expense'},actor.id)
 const budgetId=crypto.randomUUID()
 let revision:number|undefined
 const setBudget=async(income:number)=>{const result=await command(request,'budget.set',{month:'2035-04',expected_revision:revision,expected_income_minor:income,allocations:[{category_id:first.id,amount_minor:25000},{category_id:second.id,amount_minor:50000}]},actor.id,budgetId);revision=result.revision}
 await setBudget(100000)
 await page.goto('/budget');await page.getByLabel('Budget month',{exact:true}).fill('2035-04')
 const wheel=page.getByRole('listbox',{name:/Budget categories/})
 const callout=page.locator('.donut-callout')
 const key=page.locator('.budget-legend')
 const keyFood=key.getByRole('button',{name:'Wheel food',exact:true})
 const food=wheel.getByRole('option',{name:/Wheel food,/})
 const housing=wheel.getByRole('option',{name:/Wheel housing,/})
 async function point(option:typeof food){
  const box=(await wheel.boundingBox())!
  const offset=-Number(await option.getAttribute('stroke-dashoffset'))
  const share=Number((await option.getAttribute('stroke-dasharray'))!.split(' ')[0])
  const angle=(offset+share/2)/100*Math.PI*2-Math.PI/2
  return {x:box.x+box.width/2+Math.cos(angle)*box.width*46/120,y:box.y+box.height/2+Math.sin(angle)*box.height*46/120}
 }
 await expect(food).toBeAttached()
 await expect(key).not.toContainText('%')
 await expect(page.locator('.donut-feedback')).toHaveCount(0)
 await expect(page.locator('.donut-center')).toContainText('Expected income')
 await keyFood.click()
 await expect(callout).toHaveAccessibleName(/Wheel food, \$250\.00, 25\.0% of expected income/)
 await expect(food).toHaveAttribute('aria-selected','true')
 await expect(keyFood).toHaveAttribute('aria-pressed','true')
 await keyFood.hover()
 await key.getByRole('button',{name:'Wheel housing',exact:true}).focus()
 await page.keyboard.press('Enter')
 await expect(keyFood).toHaveCSS('background-color','rgba(0, 0, 0, 0)')
 await expect(food).toHaveAttribute('stroke-width','17')
 await expect(housing).toHaveAttribute('stroke-width','20')
 await keyFood.click()
 await expect(page.locator('.donut-center .donut-callout')).toBeVisible()
 await expect(page.locator('.donut-center')).not.toContainText('Expected income')
 await key.getByRole('button',{name:'Housing',exact:true}).click()
 await expect(callout).toHaveAccessibleName(/\$0\.00, 0\.0% of expected income/)
 await expect(wheel.locator('.segment-muted')).toHaveCount(0)
 await keyFood.focus();await page.keyboard.press('Enter')
 await expect(food).toHaveAttribute('aria-selected','true')
 await page.keyboard.press('Escape');await expect(callout).toHaveCount(0)
 await wheel.evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}))
 const start=await point(food)
 await page.mouse.click(start.x,start.y)
 await expect(callout).toContainText('Wheel food');await expect(callout).toHaveAccessibleName(/Wheel food, \$250\.00, 25\.0% of expected income/)
 const center=(await wheel.boundingBox())!
 await page.mouse.click(center.x+center.width/2,center.y+center.height/2)
 await expect(callout).toHaveCount(0)
 await expect(page.locator('.donut-center')).toContainText('Expected income')
 await page.mouse.click(start.x,start.y)
 await page.getByRole('heading',{name:'Budget',exact:true}).click()
 await expect(callout).toHaveCount(0)
 await wheel.evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}))
 const dragStart=await point(food),dragEnd=await point(housing)
 await page.mouse.move(dragStart.x,dragStart.y);await page.mouse.down();await page.mouse.move(dragEnd.x,dragEnd.y,{steps:15})
 await expect(callout).toContainText('Wheel housing');await page.mouse.up()
 await expect(housing).toHaveAttribute('aria-selected','true')
 expect(await wheel.evaluate(el=>getComputedStyle(el).outlineStyle)).toBe('none')
 expect(await wheel.evaluate(el=>getComputedStyle(el).webkitTapHighlightColor)).toBe('rgba(0, 0, 0, 0)')
 await wheel.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab')
 await expect(wheel).toBeFocused()
 expect(await wheel.evaluate(el=>getComputedStyle(el).outlineStyle)).toBe('solid')
 await page.keyboard.press('Home');await expect(food).toHaveAttribute('aria-selected','true')
 await page.keyboard.press('ArrowRight');await expect(housing).toHaveAttribute('aria-selected','true')
 await page.keyboard.press('Escape');await expect(callout).toHaveCount(0)
 const afterKeyboard=await point(food);await page.mouse.click(afterKeyboard.x,afterKeyboard.y)
 expect(await wheel.evaluate(el=>getComputedStyle(el).outlineStyle)).toBe('none')
 await page.keyboard.press('Escape')
 for(const width of [320,390,768,1024,1440]){
  await page.setViewportSize({width,height:900});await wheel.evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}))
  const size=(await wheel.boundingBox())!.width
  expect(size).toBeCloseTo(width===320?187.5:width===390?240:300,0)
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  const gutters=await key.evaluate(el=>{const key=el.getBoundingClientRect(),card=el.closest('.budget-chart')!.getBoundingClientRect();return {left:key.left-card.left,right:card.right-key.right}})
  expect(gutters.left).toBeGreaterThanOrEqual(40)
  const wheelBox=(await wheel.boundingBox())!,keyBounds=(await key.boundingBox())!
  if(width>=1024){
   expect(keyBounds.x).toBeGreaterThanOrEqual(wheelBox.x+wheelBox.width)
   expect(Math.abs(keyBounds.y+keyBounds.height/2-wheelBox.y-wheelBox.height/2)).toBeLessThan(2)
   await keyFood.hover()
   await expect(food).toHaveAttribute('aria-selected','true')
   await expect(keyFood).toHaveAttribute('aria-pressed','true')
   await key.getByRole('button',{name:'Wheel housing',exact:true}).hover()
   await expect(housing).toHaveAttribute('stroke-width','20')
   await expect(food).toHaveClass(/segment-muted/)
   await expect(keyFood).toHaveAttribute('aria-pressed','false')
   await expect(callout).toContainText('Wheel housing')
  }else{
   expect(gutters.right).toBeCloseTo(gutters.left,0)
   expect(keyBounds.y).toBeGreaterThan(wheelBox.y+wheelBox.height)
   await page.getByRole('heading',{name:'Budget',exact:true}).click()
   await keyFood.hover()
   await expect(callout).toHaveCount(0)
  }
  const boxes=await page.locator('.budget-legend li').evaluateAll(elements=>elements.map(el=>{const box=el.getBoundingClientRect();return {x:Math.round(box.left),y:Math.round(box.top)}}))
  expect(new Set(boxes.map(box=>box.x)).size).toBe(2)
  for(let i=1;i<boxes.length;i++){
   const previous=boxes[i-1]!,current=boxes[i]!
   expect(current.x>previous.x||(current.x===previous.x&&current.y>previous.y)).toBe(true)
  }
 }
 await page.setViewportSize({width:390,height:900});await wheel.evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}))
 const touchStart=await point(food),touchEnd=await point(housing)
 const session=await page.context().newCDPSession(page)
 await session.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1})
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[touchStart]})
 await expect(callout).toContainText('Wheel food')
 await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[touchEnd]})
 await expect(callout).toContainText('Wheel housing')
 await expect(page.locator('.refresh-host')).not.toHaveClass(/dragging|refreshing/)
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 const touchBox=(await wheel.boundingBox())!
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:touchBox.x+touchBox.width/2,y:touchBox.y+touchBox.height/2}]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await expect(callout).toHaveCount(0)
 await keyFood.scrollIntoViewIfNeeded()
 const keyBox=(await keyFood.boundingBox())!
 const keyPoint={x:keyBox.x+keyBox.width/2,y:keyBox.y+keyBox.height/2}
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[keyPoint]})
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await expect(callout).toContainText('Wheel food')
 await expect(food).toHaveAttribute('aria-selected','true')
 const keyHousing=key.getByRole('button',{name:'Wheel housing',exact:true})
 const endBox=(await keyHousing.boundingBox())!
 const keyEnd={x:endBox.x+endBox.width/2,y:endBox.y+endBox.height/2}
 const scrollBefore=await page.evaluate(()=>scrollY)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[keyPoint]})
 await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[keyEnd]})
 await expect(callout).toContainText('Wheel housing')
 await expect(housing).toHaveAttribute('aria-selected','true')
 await expect(keyHousing).toHaveAttribute('aria-pressed','true')
 await expect(page.locator('.refresh-host')).not.toHaveClass(/dragging|refreshing/)
 await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
 await expect(callout).toContainText('Wheel housing')
 expect(await page.evaluate(()=>scrollY)).toBe(scrollBefore)
 await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[keyEnd]})
 await session.send('Input.dispatchTouchEvent',{type:'touchCancel',touchPoints:[]})
 await session.detach()
 await keyFood.evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}))
 const mouseFood=(await keyFood.boundingBox())!,mouseHousing=(await keyHousing.boundingBox())!
 const mouseStart={x:mouseHousing.x+mouseHousing.width/2,y:mouseHousing.y+mouseHousing.height/2}
 const mouseEnd={x:mouseFood.x+mouseFood.width/2,y:mouseFood.y+mouseFood.height/2}
 await page.mouse.move(mouseStart.x,mouseStart.y);await page.mouse.down();await page.mouse.move(mouseEnd.x,mouseEnd.y,{steps:10})
 await expect(callout).toContainText('Wheel food');await page.mouse.up()
 await expect(food).toHaveAttribute('aria-selected','true')
 await page.mouse.move(mouseStart.x,mouseStart.y)
 await expect(callout).toContainText('Wheel food')
 await page.screenshot({path:info.outputPath('wheel-selection-phone.png'),fullPage:true})
 await setBudget(50000);await page.reload();await expect(food).toHaveAttribute('stroke-dasharray',/33\.333/);await wheel.focus();await page.keyboard.press('Home')
 await expect(callout).toHaveAccessibleName(/Wheel food, \$250\.00, 50\.0% of expected income/)
 // Geometry uses total allocations when over budget, but callouts always use expected income.
 await expect(food).toHaveAttribute('stroke-dasharray',/33\.333/)
 await setBudget(0);await page.reload();await expect(food).toHaveAccessibleName(/No expected income set/);await wheel.focus();await page.keyboard.press('Home')
 await expect(callout).toContainText('No expected income');await expect(callout).not.toContainText('NaN')
 await page.getByLabel('Budget month',{exact:true}).fill('2035-03')
 await expect(wheel.getByRole('option')).toHaveCount(0);await expect(callout).toHaveCount(0)
 const longName='A very long household category name for center layout'
 await command(request,'category.update',{name:longName,active:true,expected_revision:first.revision},actor.id,first.id)
 await page.reload()
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:900})
  await key.getByRole('button',{name:longName,exact:true}).click()
  await expect(page.locator('.donut-center')).toContainText(longName)
  expect(await page.locator('.donut-center').evaluate(center=>{
   const details=center.querySelector('.donut-callout')!
   return details.scrollHeight<=center.clientHeight+1&&details.scrollWidth<=center.clientWidth+1
  })).toBe(true)
  await wheel.evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}))
  await page.screenshot({path:info.outputPath(`center-details-${width}.png`),fullPage:true})
 }

 await page.setViewportSize({width:390,height:900})
 const scrollSession=await page.context().newCDPSession(page)
 await scrollSession.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1})
 // Gestures beginning in either clear side margin scroll the document.
 for(const side of ['left','right'])for(const delta of [-100,100]){
  await key.evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}))
  const keyBounds=(await key.boundingBox())!,cardBounds=(await page.locator('.budget-chart').boundingBox())!
  const x=side==='left'?(cardBounds.x+keyBounds.x)/2:(keyBounds.x+keyBounds.width+cardBounds.x+cardBounds.width)/2
  const y=Math.max(180,Math.min(650,keyBounds.y+keyBounds.height/2))
  await scrollSession.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
  const before=await page.evaluate(()=>scrollY)
  for(let step=1;step<=8;step++)await scrollSession.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y+delta*step/8}]})
  if(delta<0)await expect.poll(()=>page.evaluate(()=>scrollY)).toBeGreaterThan(before+30)
  else await expect.poll(()=>page.evaluate(()=>scrollY)).toBeLessThan(before-30)
  await scrollSession.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
  await expect(page.locator('.refresh-host')).not.toHaveClass(/dragging|refreshing/)
 }
 await scrollSession.detach()

})
