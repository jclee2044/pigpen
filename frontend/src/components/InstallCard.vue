<script setup lang="ts">
import { ref,shallowRef,onMounted,onUnmounted } from 'vue'
import { standalone,isIos,pwa } from '../lib/pwa'
interface InstallPrompt extends Event { prompt:()=>Promise<void>;userChoice:Promise<{outcome:string}> }
const installed=ref(standalone()),prompt=shallowRef<InstallPrompt>(),error=ref('')
const capture=(event:Event)=>{event.preventDefault();prompt.value=event as InstallPrompt}
const complete=()=>{installed.value=true;prompt.value=undefined}
onMounted(()=>{window.addEventListener('beforeinstallprompt',capture);window.addEventListener('appinstalled',complete)})
onUnmounted(()=>{window.removeEventListener('beforeinstallprompt',capture);window.removeEventListener('appinstalled',complete)})
async function install(){try{await prompt.value?.prompt();const choice=await prompt.value?.userChoice;if(choice?.outcome==='accepted')installed.value=true;prompt.value=undefined}catch{error.value='Use your browser’s install option to add PigPen.'}}
</script>
<template><section class="card section-space"><h2>A little home on your home screen.</h2><p v-if="installed">PigPen is running as an installed app.</p><template v-else><p v-if="isIos()">In Safari, tap Share, then Add to Home Screen. Turn on “Open as Web App” if offered, then tap Add.</p><p v-else>Install PigPen from your browser’s install button to open it in its own app window.</p><button v-if="prompt" class="button primary" @click="install">Install PigPen</button></template><p class="text-small">{{pwa.ready?'Offline app shell is ready.':'Offline installation finishes after your first online visit to the production app.'}} Previously loaded data and saved actions remain on this device.</p><p v-if="pwa.error||error" role="alert" class="notice error">{{pwa.error||error}}</p></section></template>
