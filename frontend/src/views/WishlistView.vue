<script setup lang="ts">
import { computed,ref,watch } from 'vue'
import { useRoute } from 'vue-router'
import { rows,state,activeUser } from '../state/household'
import type { Wish } from '../api/models'
import { money } from '../lib/money'
import PlanForm from '../components/PlanForm.vue'
import PurchaseForm from '../components/PurchaseForm.vue'
import AppDialog from '../components/AppDialog.vue'
import PigAvatar from '../components/PigAvatar.vue'
import CommentThread from '../components/CommentThread.vue'
const owner=ref(''),status=ref('active'),adding=ref(false),editing=ref<Wish>(),selected=ref(String(useRoute().query.detail??'')),prefill=ref<Wish>(),purchase=ref<Wish>()
const wishes=computed(()=>rows('wishlist-items').filter(x=>(!owner.value||x.owner_id===owner.value)&&(!status.value||x.status===status.value)))
const detail=computed(()=>rows('wishlist-items').find(x=>x.id===selected.value))
const route=useRoute()
watch(()=>route.query.detail,id=>selected.value=String(id??''))
const user=(id:string)=>rows('users').find(x=>x.id===id)
</script>
<template><div class="page-heading"><div><h1>Wish lists</h1></div><button class="button primary" :disabled="!state.online" @click="adding=true">+ Add wish</button></div><div class="toolbar"><label>Wish-list owner<select v-model="owner"><option value="">Everyone</option><option v-for="u in rows('users')" :key="u.id" :value="u.id">{{u.name}}</option></select></label><label>Wish status<select v-model="status"><option value="active">Active wishes</option><option value="purchased">Purchased</option><option value="archived">Archived</option><option value="">All wishes</option></select></label></div><section v-if="!wishes.length" class="card empty"><h2>No wishes</h2></section><div class="cards-grid"><article v-for="wish in wishes" :key="wish.id" class="card plan-card"><div class="plan-card-top"><PigAvatar :avatar="user(wish.owner_id)?.avatar" :size="38" /><small>{{user(wish.owner_id)?.name}}’s wish</small><span class="pill">{{wish.status}}</span></div><h2><button class="title-button" @click="selected=wish.id">{{wish.name}}</button></h2><strong class="plan-price">{{money(wish.price_minor)}}</strong><p v-if="wish.description" class="plan-description">{{wish.description}}</p><div class="actions"><button class="button small" @click="selected=wish.id">View wish</button><button class="button small subtle" :disabled="!state.online" @click="prefill=wish">Ask for approval</button></div></article></div><PlanForm v-if="adding||editing" kind="wish" :wish="editing" @close="adding=false;editing=undefined" /><PlanForm v-if="prefill" kind="request" :prefill="prefill" @close="prefill=undefined" /><PurchaseForm v-if="purchase" :wish="purchase" @close="purchase=undefined" /><AppDialog v-if="detail" :title="detail.name" @close="selected='' "><strong class="plan-price">{{money(detail.price_minor)}}</strong><p style="white-space:pre-wrap">{{detail.description}}</p><p v-if="detail.url"><a :href="detail.url" target="_blank" rel="noopener noreferrer">Visit item link ↗</a></p><div class="actions"><button v-if="detail.owner_id===activeUser?.id" class="button" :disabled="!state.online" @click="editing=detail;selected=''">Edit wish</button><button class="button" :disabled="!state.online" @click="prefill=detail;selected=''">Ask for approval</button><button class="button" @click="purchase=detail;selected=''">Record purchase</button></div><p class="text-small section-space">Marking a wish purchased does not itself record spending.</p><CommentThread resource="wishlist-items" :id="detail.id" /></AppDialog></template>
