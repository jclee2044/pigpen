import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
export default defineConfig({testDir:'./tests/e2e',testIgnore:['pwa.spec.ts','live-data.spec.ts','notification-prompt.spec.ts'],fullyParallel:false,workers:1,timeout:30000,use:{baseURL:'http://127.0.0.1:5186',launchOptions:{executablePath:process.env.PIGPEN_CHROMIUM || '/usr/bin/chromium',args:['--no-sandbox']},trace:'retain-on-failure'},webServer:[
 {command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8876`,url:'http://127.0.0.1:8876/api/v1/health',reuseExistingServer:false},
 {command:'npm run dev -- --port 5186 --strictPort',url:'http://127.0.0.1:5186',reuseExistingServer:false,env:{PIGPEN_API_TARGET:'http://127.0.0.1:8876'}},
]})
