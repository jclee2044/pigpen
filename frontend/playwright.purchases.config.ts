import { resolve } from 'node:path'
import base from './playwright.config'
export default {...base,testMatch:['purchase-interactions.spec.ts','finance.spec.ts','purchase-spending.spec.ts'],use:{...base.use,baseURL:'http://127.0.0.1:8893'},webServer:{command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8893 --static`,url:'http://127.0.0.1:8893/api/v1/health',reuseExistingServer:false}}
