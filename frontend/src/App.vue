<script setup lang="ts">
import { RouterLink,RouterView } from 'vue-router'
import AppIcon from './components/AppIcon.vue'
import PigAvatar from './components/PigAvatar.vue'
const nav=[['/','Dashboard','home'],['/purchases','Purchases','receipt'],['/budget','Budget','budget'],['/wish-lists','Wish lists','heart'],['/approvals','Approvals','shield']]
</script>
<template>
 <a href="#main" class="skip-link">Skip to content</a>
 <header class="app-header"><RouterLink to="/" class="wordmark" aria-label="PigPen home">pigpen<span>•</span></RouterLink><p class="tagline">A little planning. More room to live.</p><div class="header-actions"><RouterLink to="/notifications" class="icon-button" aria-label="Notifications"><AppIcon name="bell" /></RouterLink><RouterLink to="/profiles" class="profile-link"><PigAvatar /><span><strong>Our household</strong><small>Profiles & settings</small></span></RouterLink></div></header>
 <aside class="sidebar"><p class="eyebrow">OUR HOUSEHOLD</p><nav aria-label="Main navigation"><RouterLink v-for="[path,label,icon] in nav" :key="path" :to="path!" :exact-active-class="'active'"><AppIcon :name="icon!" /><span>{{label}}</span></RouterLink></nav><div class="sidebar-bottom"><div class="little-note"><strong>Small steps, together.</strong><p>A home for your household plans.</p></div><RouterLink to="/profiles" class="settings-link">Profiles & settings</RouterLink></div></aside>
 <main id="main" tabindex="-1"><RouterView /></main>
 <nav class="mobile-nav" aria-label="Mobile navigation"><RouterLink v-for="[path,label,icon] in nav" :key="path" :to="path!" exact-active-class="active"><AppIcon :name="icon!" /><span>{{label}}</span></RouterLink></nav>
</template>
<style src="./style.css"></style>
