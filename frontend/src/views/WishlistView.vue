<script setup lang="ts">
import SwipeWish from '../components/SwipeWish.vue'
import AppLoading from '../components/AppLoading.vue'
import { useSubmission } from '../lib/submission'
import AppIcon from '../components/AppIcon.vue'
import PurchaseEmptyState from '../components/PurchaseEmptyState.vue'
import { computed,ref,watch } from 'vue'
import { useRoute } from 'vue-router'
import { rows,state,activeUser,mutate } from '../state/household'
import type { Wish } from '../api/models'
import { money } from '../lib/money'
import PlanForm from '../components/PlanForm.vue'
import PurchaseForm from '../components/PurchaseForm.vue'
import AppDialog from '../components/AppDialog.vue'
import PigAvatar from '../components/PigAvatar.vue'
import CommentThread from '../components/CommentThread.vue'
const openId=ref(''),deleting=ref<Wish>()
const {saving,error,retryId,run}=useSubmission()
function requestDelete(wish:Wish){if(saving.value||retryId.value)return;error.value='';selected.value='';deleting.value=wish}
async function deleteWish(){
 const wish=deleting.value
 if(!wish)return
 await run(()=>mutate('wishlist.delete',{expected_revision:wish.revision},wish.id),()=>{deleting.value=undefined;openId.value=''})
}
const owner=ref(''),status=ref('active'),adding=ref(false),editing=ref<Wish>(),selected=ref(String(useRoute().query.detail??'')),prefill=ref<Wish>(),purchase=ref<Wish>()
const wishes=computed(()=>rows('wishlist-items').filter(x=>(!owner.value||x.owner_id===owner.value)&&(!status.value||x.status===status.value)))
const detail=computed(()=>rows('wishlist-items').find(x=>x.id===selected.value))
const route=useRoute()
watch(()=>route.query.detail,id=>selected.value=String(id??''))
const user=(id:string)=>rows('users').find(x=>x.id===id)
</script>
<template><div class="page-heading"><div><h1>Wish lists</h1></div><button class="button primary icon-only" aria-label="Add wish" title="Add wish" :disabled="!state.online" @click="adding=true"><AppIcon name="plus" /></button></div><div class="toolbar"><label>Wish-list owner<select v-model="owner"><option value="">Everyone</option><option v-for="u in rows('users')" :key="u.id" :value="u.id">{{u.name}}</option></select></label><label>Wish status<select v-model="status"><option value="active">Active wishes</option><option value="purchased">Purchased</option><option value="archived">Archived</option><option value="">All wishes</option></select></label></div><section v-if="!wishes.length" class="card empty"><PurchaseEmptyState /></section><div class="cards-grid"><SwipeWish v-for="wish in wishes" :key="wish.id" :id="wish.id" :name="wish.name" :enabled="wish.owner_id===activeUser?.id" :open="openId===wish.id" @reveal="id=>openId=id" @delete="requestDelete(wish)"><article class="card plan-card wish-card"><div class="plan-card-top"><PigAvatar :avatar="user(wish.owner_id)?.avatar" :size="38" /><small>{{user(wish.owner_id)?.name}}’s wish</small><span class="pill">{{wish.status}}</span></div><div class="wish-card-summary"><h2><button class="title-button wish-card-open" aria-haspopup="dialog" @click="selected=wish.id">{{wish.name}}</button></h2><strong class="plan-price">{{money(wish.price_minor)}}</strong></div><p v-if="wish.description" class="plan-description">{{wish.description}}</p></article></SwipeWish></div><AppDialog v-if="deleting" centered title="Delete wish?" @close="!saving&&!retryId&&(deleting=undefined)"><AppLoading v-if="saving" compact /><p>Delete “{{deleting.name}}” from the wish list?</p><div v-if="error" class="notice error" role="alert">{{error}}</div><p v-if="!state.online" class="notice">Reconnect to delete this wish.</p><div class="actions"><button class="button" :disabled="saving||!!retryId" @click="deleting=undefined">Cancel</button><button class="button danger" :disabled="!state.online||saving" @click="deleteWish">{{saving?'Deleting…':retryId?'Retry saved submission':'Delete wish'}}</button></div></AppDialog><PlanForm v-if="adding||editing" kind="wish" :wish="editing" @close="adding=false;editing=undefined" /><PlanForm v-if="prefill" kind="request" :prefill="prefill" @close="prefill=undefined" /><PurchaseForm v-if="purchase" :wish="purchase" @close="purchase=undefined" /><AppDialog v-if="detail" centered :title="detail.name" @close="selected='' "><strong class="plan-price">{{money(detail.price_minor)}}</strong><p style="white-space:pre-wrap">{{detail.description}}</p><p v-if="detail.url"><a :href="detail.url" target="_blank" rel="noopener noreferrer">Visit item link ↗</a></p><div class="actions"><button v-if="detail.owner_id===activeUser?.id" class="button" :disabled="!state.online" @click="editing=detail;selected=''">Edit wish</button><button v-if="detail.owner_id===activeUser?.id" class="button danger" @click="requestDelete(detail)">Delete wish</button><button class="button" :disabled="!state.online" @click="prefill=detail;selected=''">Ask for approval</button><button class="button" @click="purchase=detail;selected=''">Record purchase</button></div><p class="text-small section-space">Marking a wish purchased does not itself record spending.</p><CommentThread resource="wishlist-items" :id="detail.id" /></AppDialog></template>
