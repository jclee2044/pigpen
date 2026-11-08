import { reactive } from 'vue'

const storageKey = 'pigpen-dark-mode'
const centsStorageKey = 'pigpen-show-cents'
export const appearance = reactive({ darkMode: false, showCents: true })

function apply(darkMode: boolean) {
 appearance.darkMode = darkMode
 document.documentElement.dataset.theme = darkMode ? 'dark' : 'light'
}

export function initializeAppearance() {
 try { apply(localStorage.getItem(storageKey) === 'true') }
 catch { apply(false) }
 try { appearance.showCents = localStorage.getItem(centsStorageKey) !== 'false' }
 catch { appearance.showCents = true }
 window.addEventListener('storage', event => {
  if (event.key === storageKey || event.key === null) apply(event.newValue === 'true')
  if (event.key === centsStorageKey || event.key === null) appearance.showCents = event.newValue !== 'false'
 })
}

export function setDarkMode(enabled: boolean) {
 apply(enabled)
 try { localStorage.setItem(storageKey, String(enabled)) }
 catch { /* Appearance remains usable when device storage is unavailable. */ }
}

export function setShowCents(enabled: boolean) {
 appearance.showCents = enabled
 try { localStorage.setItem(centsStorageKey, String(enabled)) }
 catch { /* Display preference remains usable when device storage is unavailable. */ }
}
