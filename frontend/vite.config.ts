import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import { readFileSync,writeFileSync,readdirSync,statSync } from 'node:fs'
import { resolve } from 'node:path'
import { createHash } from 'node:crypto'
function pwaBundle(){return {name:'pigpen-offline-shell',apply:'build' as const,closeBundle(){
 const dist=resolve(import.meta.dirname,'dist');const files:string[]=[]
 function walk(dir:string){for(const name of readdirSync(dir)){const full=resolve(dir,name);if(statSync(full).isDirectory())walk(full);else if(name!=='sw.js'&&!name.endsWith('.map'))files.push('/'+full.slice(dist.length+1))}}
 walk(dist);files.sort();const hash=createHash('sha256');for(const file of files)hash.update(file).update('\0').update(readFileSync(dist+file));const build=hash.digest('hex').slice(0,16)
 const source=readFileSync(resolve(import.meta.dirname,'public/sw.js'),'utf8').replace("'__PIGPEN_BUILD__'",JSON.stringify(build)).replace("'__PIGPEN_PRECACHE__'",JSON.stringify(files))
 writeFileSync(resolve(dist,'sw.js'),source)
}}}
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    pwaBundle(),
  ],
  server: { host: '127.0.0.1', proxy: { '/api': { target: process.env.PIGPEN_API_TARGET || 'http://127.0.0.1:8000' } } },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
