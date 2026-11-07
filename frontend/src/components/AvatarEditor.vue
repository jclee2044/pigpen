<script setup lang="ts">
import PigAvatar from './PigAvatar.vue'
import type { Avatar } from '../api/generated'
import manifest from '../../../assets/avatars/pig-v1/manifest.json'
const avatar=defineModel<Required<Avatar>>({required:true})
const groups=manifest.groups
</script>
<template><div class="avatar-profile"><PigAvatar :avatar="avatar" :size="96" /><p>Make your pig feel like you.<br /><small>Choose your colors and accessories.</small></p></div><div class="avatar-options"><label v-for="(options,group) in groups" :key="group">{{group.charAt(0).toUpperCase()+group.slice(1)}}<select v-model="avatar[group]"><option v-for="option in options" :key="option.id" :value="option.id">{{option.label}}</option></select></label></div></template>
