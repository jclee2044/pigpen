<script setup lang="ts">
import { computed,ref,watch } from 'vue'
import { useRoute,useRouter } from 'vue-router'
import PurchaseDetail from '../components/PurchaseDetail.vue'
import { rows } from '../state/household'
import { shell } from '../state/shell'
import { recent } from '../lib/selectors'
import type { Purchase } from '../api/models'
import PurchaseForm from '../components/PurchaseForm.vue'
import PurchaseRows from '../components/PurchaseRows.vue'
const route=useRoute(),router=useRouter()
const detailId=ref(String(route.query.detail??''))
const detail=computed(()=>rows('purchases').find(x=>x.id===detailId.value))
watch(()=>route.query.detail,id=>detailId.value=String(id??''))
function closeDetail(){detailId.value='';void router.replace('/purchases')}
const add=ref(false),edit=ref<Purchase>(),category=ref(''),owner=ref('')
const purchases=computed(()=>recent(rows('purchases').filter(x=>x.transaction_date.slice(0,7)===shell.month&&(!category.value||x.category_id===category.value)&&(!owner.value||x.purchaser_id===owner.value))))
</script>
<template><div class="page-heading"><div><h1>Purchases</h1></div><button class="button primary" @click="add=true">+ Add purchase</button></div><div class="toolbar"><label>Month<input v-model="shell.month" type="month" /></label><label>Category<select v-model="category"><option value="">All categories</option><option v-for="c in rows('categories').filter(x=>x.kind!=='savings')" :key="c.id" :value="c.id">{{c.name}}</option></select></label><label>Purchased by<select v-model="owner"><option value="">Everyone</option><option v-for="user in rows('users')" :key="user.id" :value="user.id">{{user.name}}</option></select></label></div><section class="card"><PurchaseRows :purchases="purchases" @select="p=>detailId=p.id" /></section><PurchaseDetail v-if="detail" :purchase="detail" @close="closeDetail" @edit="edit=detail;closeDetail()" /><PurchaseForm v-if="add||edit" :purchase="edit" @close="add=false;edit=undefined" /></template>
