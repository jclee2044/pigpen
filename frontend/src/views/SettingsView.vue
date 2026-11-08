<script setup lang="ts">
import { appearance, setDarkMode, setShowCents } from '../state/appearance'
import PushSettings from '../components/PushSettings.vue'
</script>

<template>
 <div class="page-heading"><div><h1>Settings</h1></div></div>
 <section class="card appearance-settings" aria-labelledby="appearance-heading">
  <h2 id="appearance-heading">Appearance</h2>
  <label class="check-label"><input type="checkbox" role="switch" :checked="appearance.darkMode" @change="setDarkMode(($event.target as HTMLInputElement).checked)" />Dark mode</label>
  <p class="text-small">Use a dark background with lighter text. Your choice is saved on this device.</p>
  <label class="check-label section-space"><input type="checkbox" role="switch" :checked="appearance.showCents" @change="setShowCents(($event.target as HTMLInputElement).checked)" />Show cents</label>
  <p class="text-small">When off, amounts display rounded to the nearest dollar. Saved amounts and editing fields keep their cents. Your choice is saved on this device.</p>
 </section>
 <PushSettings />
</template>
