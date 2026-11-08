import { test,expect } from '@playwright/test'
import { seed } from './helpers'
test('glasses shapes and colors preview and persist independently',async({page,request},info)=>{
 const user=await seed(page,request,'Glasses reviewer')
 await page.getByRole('button',{name:'Our household',exact:true}).click();await page.getByRole('link',{name:'Profiles',exact:true}).click()
 await page.getByRole('link',{name:'Edit Glasses reviewer',exact:true}).click()
 const shape=page.getByRole('combobox',{name:'Glasses shape',exact:true}),color=page.getByRole('combobox',{name:'Glasses color',exact:true})
 await expect(color).toBeDisabled();await shape.selectOption('rounded');await color.selectOption('tortoiseshell')
 for(const value of ['aviator','browline','round','square','cat-eye','monocle','sunglasses','rounded']){await shape.selectOption(value);await expect(color).toHaveValue('tortoiseshell')}
 for(const value of ['black','brown','gold','rose','blue','teal','purple','tortoiseshell']){await color.selectOption(value);await expect(page.locator('.avatar-profile img').last()).toHaveAttribute('src',new RegExp('rounded-'+value+'|data:image/svg'))}
 await shape.selectOption('none');await expect(color).toBeDisabled();await shape.selectOption('rounded');await expect(color).toHaveValue('tortoiseshell')
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:info.outputPath('tortoiseshell-editor.png'),fullPage:true})
 await page.getByRole('button',{name:'Save profile',exact:true}).click();await expect(page).toHaveURL(/\/profiles$/)
 const saved=await (await request.get('/api/v1/records/users/'+user.id)).json();expect(saved.avatar.glasses).toBe('rounded-tortoiseshell')
 await page.reload();await page.getByRole('button',{name:'Our household',exact:true}).click();await page.getByRole('link',{name:'Profiles',exact:true}).click();await page.getByRole('link',{name:'Edit Glasses reviewer',exact:true}).click()
 await expect(shape).toHaveValue('rounded');await expect(color).toHaveValue('tortoiseshell')
 await page.waitForFunction(()=>[...document.querySelectorAll('.avatar-profile img')].every(img=>(img as HTMLImageElement).naturalWidth>0))
})
