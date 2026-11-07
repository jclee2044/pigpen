import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
export default defineConfig({testDir:'./tests/e2e',testMatch:'pwa.spec.ts',workers:1,timeout:30000,use:{baseURL:'http://127.0.0.1:8766',launchOptions:{executablePath:process.env.PIGPEN_CHROMIUM || '/usr/bin/chromium',args:['--no-sandbox']},trace:'retain-on-failure'},webServer:{command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8766 --static`,url:'http://127.0.0.1:8766/api/v1/health',reuseExistingServer:false}})
