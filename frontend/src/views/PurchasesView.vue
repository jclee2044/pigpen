<script setup lang="ts">
import { computed,ref } from 'vue'
import { state,rows } from '../state/household'
import { shell } from '../state/shell'
import { recent } from '../lib/selectors'
import type { Purchase } from '../api/models'
import PurchaseForm from '../components/PurchaseForm.vue'
import PurchaseRows from '../components/PurchaseRows.vue'
const add=ref(false),edit=ref<Purchase>(),category=ref(''),owner=ref('')
const purchases=computed(()=>recent(rows('purchases').filter(x=>x.transaction_date.slice(0,7)===shell.month&&(!category.value||x.category_id===category.value)&&(!owner.value||x.purchaser_id===owner.value))))
</script>
<template><div class="page-heading"><div><h1 aria-label="Purchases">The little things add up.</h1><p>Your household’s purchases, all in one place.</p></div><button class="button primary" @click="add=true">+ Add purchase</button></div><div class="toolbar"><label>Month<input v-model="shell.month" type="month" /></label><label>Category<select v-model="category"><option value="">All categories</option><option v-for="c in rows('categories').filter(x=>x.kind!=='savings')" :key="c.id" :value="c.id">{{c.name}}</option></select></label><label>Purchased by<select v-model="owner"><option value="">Everyone</option><option v-for="user in rows('users')" :key="user.id" :value="user.id">{{user.name}}</option></select></label></div><section class="card"><PurchaseRows :purchases="purchases" @select="p=>{if(state.online)edit=p}" /></section><PurchaseForm v-if="add||edit" :purchase="edit" @close="add=false;edit=undefined" /></template>
