import { resolve } from 'node:path'
import base from './playwright.config'
const origin='http://127.0.0.1:8896'
export default {...base,testMatch:['monthly-reviews.spec.ts','advisor.spec.ts'],use:{...base.use,baseURL:origin,serviceWorkers:'block' as const},webServer:{command:`${process.env.PIGPEN_TEST_PYTHON||resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8896 --static`,url:origin+'/api/v1/health',reuseExistingServer:false}}
