import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
import base from './playwright.config'
export default defineConfig(base,{
 testMatch:'wishlist-delete.spec.ts',
 use:{baseURL:'http://127.0.0.1:5181'},
 webServer:[
  {command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8771`,url:'http://127.0.0.1:8771/api/v1/health',reuseExistingServer:false},
  {command:'npm run dev -- --port 5181 --strictPort',url:'http://127.0.0.1:5181',reuseExistingServer:false,env:{PIGPEN_API_TARGET:'http://127.0.0.1:8771'}},
 ],
})
