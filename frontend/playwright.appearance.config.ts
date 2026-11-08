import { resolve } from 'node:path'
import base from './playwright.pwa.config'
export default {...base,testMatch:['appearance.spec.ts'],use:{...base.use,baseURL:'http://127.0.0.1:8883'},webServer:{command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8883 --static`,url:'http://127.0.0.1:8883/api/v1/health',reuseExistingServer:false}}
