<script setup lang="ts">
import { computed, ref } from 'vue'
import PigAvatar from './PigAvatar.vue'
import type { Avatar } from '../api/generated'
import manifest from '../../../assets/avatars/pig-v1/manifest.json'
const avatar=defineModel<Required<Avatar>>({required:true})
const {glasses,...groups}=manifest.groups
const selected=computed(()=>glasses.find(option=>option.id===avatar.value.glasses)??glasses[0]!)
const rememberedColor=ref('original')
const shapes=[...new Set(glasses.map(option=>option.shape))]
const colors=[...new Set(glasses.filter(option=>option.shape!=='none').map(option=>option.frameColor))]
const label=(value:string)=>value==='rounded'?'Rounded / wayfarer':value.charAt(0).toUpperCase()+value.slice(1).replaceAll('-',' ')
const shape=computed({get:()=>selected.value.shape,set:(value:string)=>{
 const color=selected.value.shape==='none'?rememberedColor.value:selected.value.frameColor
 avatar.value.glasses=glasses.find(option=>option.shape===value&&(value==='none'||option.frameColor===color))!.id
}})
const color=computed({get:()=>selected.value.shape==='none'?rememberedColor.value:selected.value.frameColor,set:(value:string)=>{
 rememberedColor.value=value
 avatar.value.glasses=glasses.find(option=>option.shape===shape.value&&option.frameColor===value)!.id
}})
</script>
<template><div class="avatar-profile"><PigAvatar :avatar="avatar" :size="96" /><p>Make your pig feel like you.<br /><small>Choose your colors and accessories.</small></p></div><div class="avatar-options"><label v-for="(options,group) in groups" :key="group">{{group.charAt(0).toUpperCase()+group.slice(1)}}<select v-model="avatar[group]"><option v-for="option in options" :key="option.id" :value="option.id">{{option.label}}</option></select></label><label>Glasses shape<select v-model="shape"><option v-for="value in shapes" :key="value" :value="value">{{value==='none'?'No glasses':label(value)}}</option></select></label><label>Glasses color<select v-model="color" :disabled="shape==='none'"><option v-for="value in colors" :key="value" :value="value">{{label(value)}}</option></select></label></div></template>
