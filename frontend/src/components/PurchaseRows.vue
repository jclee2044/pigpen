<script setup lang="ts">
import type { Purchase } from '../api/models'
import { rows } from '../state/household'
import { money } from '../lib/money'
import PigAvatar from './PigAvatar.vue'
import PurchaseEmptyState from './PurchaseEmptyState.vue'
defineProps<{purchases:Purchase[]}>()
const emit=defineEmits<{select:[Purchase]}>()
const category=(id:string)=>rows('categories').find(c=>c.id===id)
const person=(id:string)=>rows('users').find(u=>u.id===id)
</script>
<template><PurchaseEmptyState v-if="!purchases.length" /><div v-for="p in purchases" :key="p.id" class="row"><PigAvatar :avatar="person(p.purchaser_id)?.avatar" :size="40" :label="(person(p.purchaser_id)?.name??'Archived profile')+' avatar'" /><div class="row-main"><button class="inline-link" @click="emit('select',p)">{{p.item}}</button><p>{{person(p.purchaser_id)?.name??'Archived profile'}} · {{p.transaction_date}}</p></div><div class="row-end"><strong>{{money(p.amount_minor)}}</strong><small>{{category(p.category_id)?.name}}</small></div></div></template>
