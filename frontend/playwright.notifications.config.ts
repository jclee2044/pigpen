import { defineConfig } from '@playwright/test'
import pwa from './playwright.pwa.config'
export default defineConfig({...pwa,testMatch:['notification-prompt.spec.ts']})
