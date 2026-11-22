import { resolve } from 'node:path'
import base from './playwright.config'
export default {...base,testMatch:['monthly-categories.spec.ts','category-delete.spec.ts','receipt-scan.spec.ts','category-order.spec.ts','budget-editor.spec.ts','budget-unsaved.spec.ts','finance.spec.ts','offline.spec.ts'],timeout:60000,
 use:{...base.use,hasTouch:true,isMobile:true,viewport:{width:390,height:844},launchOptions:{...base.use?.launchOptions,args:['--no-sandbox','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']},baseURL:'http://127.0.0.1:8899'},
 webServer:{command:`${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8899 --static --receipt-worker`,url:'http://127.0.0.1:8899/api/v1/health',reuseExistingServer:false}}
