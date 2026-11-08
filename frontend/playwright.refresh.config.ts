import { resolve } from 'node:path'
import base from './playwright.pwa.config'
export default {...base,testMatch:['pull-refresh.spec.ts','app-update.spec.ts'],use:{...base.use,baseURL:'http://127.0.0.1:8879'},webServer:{command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8879 --static`,url:'http://127.0.0.1:8879/api/v1/health',reuseExistingServer:false}}
