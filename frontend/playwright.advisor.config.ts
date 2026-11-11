import { resolve } from 'node:path'
import base from './playwright.config'

const origin = 'http://127.0.0.1:8898'
export default {
  ...base,
  testMatch: 'advisor.spec.ts',
  use: { ...base.use, baseURL: origin, serviceWorkers: 'block' as const },
  webServer: {
    command: `${resolve('../backend/.venv/bin/python')} ../tools/run_test_api.py --port 8898 --static`,
    url: origin + '/api/v1/health',
    reuseExistingServer: false,
  },
}
