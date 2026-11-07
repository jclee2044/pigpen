import { test,expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { runInNewContext } from 'node:vm'
test('push worker reveals no financial payload and keeps notification links same-origin',async()=>{
 const listeners:Record<string,(event:unknown)=>void>={}
 let shown:{title:string;options:NotificationOptions}|undefined
 let task:Promise<unknown>|undefined
 let opened=''
 const self={location:{origin:'https://pigpen.example'},addEventListener:(kind:string,callback:(event:unknown)=>void)=>{listeners[kind]=callback},registration:{showNotification:async(title:string,options:NotificationOptions)=>{shown={title,options}}},clients:{matchAll:async()=>[],openWindow:async(url:string)=>{opened=url}}}
 runInNewContext(readFileSync('public/sw.js','utf8'),{self,URL,encodeURIComponent})
 const id='12345678-1234-1234-1234-123456789abc'
 listeners.push!({data:{json:()=>({notification_id:id,amount_minor:999999,item:'Private item'})},waitUntil:(promise:Promise<unknown>)=>{task=promise}})
 await task
 expect(shown?.title).toBe('PigPen');expect(JSON.stringify(shown)).not.toContain('Private item');expect(JSON.stringify(shown)).not.toContain('999999')
 expect(shown?.options.tag).toBe(id)
 listeners.notificationclick!({notification:{data:{url:'https://evil.example'},close:()=>{}},waitUntil:(promise:Promise<unknown>)=>{task=promise}})
 expect(opened).toBe('')
 listeners.notificationclick!({notification:{data:shown?.options.data,close:()=>{}},waitUntil:(promise:Promise<unknown>)=>{task=promise}})
 await task;expect(opened).toBe('https://pigpen.example/notifications?notification='+id)
})

test('worker keeps the shell available during server failures and never caches API requests',async()=>{
 const listeners:Record<string,(event:unknown)=>void>={}
 let task:Promise<unknown>|undefined
 const shell={status:200,body:'cached shell'}
 const self={location:{origin:'https://pigpen.example'},addEventListener:(kind:string,callback:(event:unknown)=>void)=>{listeners[kind]=callback}}
 runInNewContext(readFileSync('public/sw.js','utf8'),{self,URL,fetch:async()=>({ok:false,status:503}),caches:{open:async()=>({match:async()=>shell})}})
 listeners.fetch!({request:{url:'https://pigpen.example/purchases',method:'GET',mode:'navigate'},respondWith:(promise:Promise<unknown>)=>{task=promise}})
 expect(await task).toEqual(shell)
 task=undefined
 listeners.fetch!({request:{url:'https://pigpen.example/api/v1/sync/snapshot',method:'GET'},respondWith:(promise:Promise<unknown>)=>{task=promise}})
 expect(task).toBeUndefined()
})
