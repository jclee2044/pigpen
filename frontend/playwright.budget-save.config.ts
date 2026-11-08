import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
import base from './playwright.config'
export default defineConfig(base,{
 testMatch:['budget-unsaved.spec.ts','budget-editor.spec.ts'],
 use:{baseURL:'http://127.0.0.1:5287'},
 webServer:[
  {command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8887`,url:'http://127.0.0.1:8887/api/v1/health',reuseExistingServer:false},
  {command:'npm run dev -- --port 5287 --strictPort',url:'http://127.0.0.1:5287',reuseExistingServer:false,env:{PIGPEN_API_TARGET:'http://127.0.0.1:8887'}},
 ],
})
