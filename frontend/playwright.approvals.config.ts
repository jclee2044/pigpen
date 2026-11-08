import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
import base from './playwright.config'
export default defineConfig(base,{
 testMatch:['approval-actions.spec.ts','approvals.spec.ts','wishlist-delete.spec.ts','mobile-comments.spec.ts'],
 use:{baseURL:'http://127.0.0.1:5198'},
 webServer:[
  {command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8798`,url:'http://127.0.0.1:8798/api/v1/health',reuseExistingServer:false},
  {command:'npm run dev -- --port 5198 --strictPort',url:'http://127.0.0.1:5198',reuseExistingServer:false,env:{PIGPEN_API_TARGET:'http://127.0.0.1:8798'}},
 ],
})
