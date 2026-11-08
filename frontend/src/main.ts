import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { initializeAppearance } from './state/appearance'

initializeAppearance()

const app = createApp(App)

app.use(router)

app.mount('#app')
