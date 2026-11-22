import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
import base from './playwright.config'
export default defineConfig({...base,
 testMatch:['monthly-categories.spec.ts','category-delete.spec.ts','category-order.spec.ts','budget-editor.spec.ts','budget-unsaved.spec.ts','finance.spec.ts','offline.spec.ts','receipt-scan.spec.ts'],
 timeout:60000,
 use:{baseURL:'http://127.0.0.1:5298'},
 webServer:[
  {command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8898`,url:'http://127.0.0.1:8898/api/v1/health',reuseExistingServer:false},
  {command:'npm run dev -- --port 5298 --strictPort',url:'http://127.0.0.1:5298',reuseExistingServer:false,env:{PIGPEN_API_TARGET:'http://127.0.0.1:8898'}},
 ],
})
