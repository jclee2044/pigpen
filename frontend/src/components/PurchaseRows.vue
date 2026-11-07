<script setup lang="ts">
import type { Purchase } from '../api/models'
import { rows } from '../state/household'
import { money } from '../lib/money'
defineProps<{purchases:Purchase[]}>()
const emit=defineEmits<{select:[Purchase]}>()
const category=(id:string)=>rows('categories').find(c=>c.id===id)
const person=(id:string)=>rows('users').find(u=>u.id===id)?.name??'Archived profile'
</script>
<template><div v-if="!purchases.length" class="empty"><p>No purchases here yet. Your next small step starts with a purchase.</p></div><div v-for="p in purchases" :key="p.id" class="row"><span class="category-icon" :class="category(p.category_id)?.kind">{{category(p.category_id)?.name.charAt(0)}}</span><div class="row-main"><button class="inline-link" @click="emit('select',p)">{{p.item}}</button><p>{{person(p.purchaser_id)}} · {{p.transaction_date}}</p></div><div class="row-end"><strong>{{money(p.amount_minor)}}</strong><small>{{category(p.category_id)?.name}}</small></div></div></template>
