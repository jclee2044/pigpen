import { reactive } from 'vue'

const storageKey = 'pigpen-dark-mode'
export const appearance = reactive({ darkMode: false })

function apply(darkMode: boolean) {
 appearance.darkMode = darkMode
 document.documentElement.dataset.theme = darkMode ? 'dark' : 'light'
}

export function initializeAppearance() {
 try { apply(localStorage.getItem(storageKey) === 'true') }
 catch { apply(false) }
 window.addEventListener('storage', event => {
  if (event.key === storageKey || event.key === null) apply(event.newValue === 'true')
 })
}

export function setDarkMode(enabled: boolean) {
 apply(enabled)
 try { localStorage.setItem(storageKey, String(enabled)) }
 catch { /* Appearance remains usable when device storage is unavailable. */ }
}
