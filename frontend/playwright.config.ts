import { defineConfig } from '@playwright/test'
export default defineConfig({testDir:'./tests/e2e',testIgnore:'pwa.spec.ts',fullyParallel:false,workers:1,timeout:30000,use:{baseURL:'http://127.0.0.1:5173',launchOptions:{executablePath:process.env.PIGPEN_CHROMIUM || '/usr/bin/chromium',args:['--no-sandbox']},trace:'retain-on-failure'},webServer:[
 {command:'../backend/.venv/bin/python ../tools/run_test_api.py',url:'http://127.0.0.1:8765/api/v1/health',reuseExistingServer:false},
 {command:'npm run dev -- --port 5173 --strictPort',url:'http://127.0.0.1:5173',reuseExistingServer:false,env:{PIGPEN_API_TARGET:'http://127.0.0.1:8765'}},
]})
