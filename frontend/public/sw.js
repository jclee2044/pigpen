/* Build replaces these two values with the exact immutable application shell. */
const BUILD = '__PIGPEN_BUILD__'
const PRECACHE = '__PIGPEN_PRECACHE__'
const CACHE = 'pigpen-shell-' + BUILD
self.addEventListener('install', event => { event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE))) })
self.addEventListener('activate', event => { event.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('pigpen-shell-')&&key!==CACHE).map(key=>caches.delete(key)))),self.clients.claim()])) })
self.addEventListener('message',event=>{if(event.data?.type==='ACTIVATE')self.skipWaiting()})
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url)
 if(event.request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return
 if(event.request.mode==='navigate')event.respondWith(fetch(event.request).then(response=>{if(!response.ok)throw new Error('App server unavailable');return response}).catch(()=>caches.open(CACHE).then(cache=>cache.match('/index.html'))))
 else if(PRECACHE.includes(url.pathname))event.respondWith(caches.open(CACHE).then(cache=>cache.match(url.pathname)).then(cached=>cached||fetch(event.request)))
})
self.addEventListener('push',event=>{
 let id='',body='A household update is waiting.'
 try{const data=event.data?.json();if(typeof data?.notification_id==='string'&&/^[a-f0-9-]{36}$/i.test(data.notification_id))id=data.notification_id;if(typeof data?.body==='string'&&data.body.trim())body=data.body.slice(0,400)}catch{/* Generic notification without private payloads. */}
 event.waitUntil(Promise.all([self.clients.matchAll({type:'window',includeUncontrolled:true}).then(windows=>{for(const client of windows)client.postMessage({type:'PIGPEN_NOTIFICATION'})}),self.registration.showNotification('PigPen',{body,icon:'/icons/icon-192.png',badge:'/icons/icon-192.png',tag:id||'pigpen-update',data:{url:'/notifications'+(id?'?notification='+encodeURIComponent(id):'')}})]))
})
self.addEventListener('notificationclick',event=>{
 event.notification.close()
 const url=new URL(event.notification.data?.url||'/notifications',self.location.origin)
 if(url.origin!==self.location.origin)return
 event.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(async windows=>{
  const window=windows.find(client=>new URL(client.url).origin===self.location.origin)
  if(window){await window.navigate(url.href);return window.focus()}
  return self.clients.openWindow(url.href)
 }))
})
