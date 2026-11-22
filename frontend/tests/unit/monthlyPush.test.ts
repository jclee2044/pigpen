import { readFileSync } from 'node:fs'
import { runInNewContext } from 'node:vm'
import { expect, test, vi } from 'vitest'
const worker=readFileSync(new URL('../../public/sw.js',import.meta.url),'utf8')
test.each(['/analyses/2026-11','https://evil.example/analyses/2026-11','/analyses/2026-13','//evil.example','/analyses/2026-11?redirect=elsewhere'])('monthly push restricts destination %s',async url=>{
 const showNotification=vi.fn(),handlers=new Map(),waitUntil=vi.fn()
 runInNewContext(worker,{self:{addEventListener:handlers.set.bind(handlers),clients:{matchAll:async()=>[]},registration:{showNotification}}})
 handlers.get('push')({data:{json:()=>({url,title:'Monthly analysis ready',body:'November analysis is ready.'})},waitUntil})
 await waitUntil.mock.calls[0]![0]
 expect(showNotification.mock.calls[0]![1].data.url).toBe(url==='/analyses/2026-11'?url:'/notifications')
})
