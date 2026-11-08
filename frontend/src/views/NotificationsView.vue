<script setup lang="ts">
import PushSettings from '../components/PushSettings.vue'
import PurchaseEmptyState from '../components/PurchaseEmptyState.vue'
import { computed,ref,watch } from 'vue'
import { useRouter,useRoute } from 'vue-router'
import { rows,state,activeUser,mutate,setError } from '../state/household'
import type { Note } from '../api/models'
import { noteLabel,noteLink } from '../lib/notifications'
const unreadOnly=ref(false),router=useRouter()
const route=useRoute(),handled=ref('')
const notifications=computed(()=>rows('notifications').filter(x=>x.recipient_id===activeUser.value?.id&&(!unreadOnly.value||!x.read_at)).sort((a,b)=>b.created_at.localeCompare(a.created_at)))
async function open(note:Note){try{if(!note.read_at&&state.online)await mutate('notification.read',{expected_revision:note.revision},note.id);await router.push(noteLink(note))}catch(e){setError(e)}}
watch(()=>[route.query.notification,notifications.value],()=>{const id=route.query.notification;if(typeof id!=='string'||handled.value===id)return;const note=notifications.value.find(x=>x.id===id);if(note){handled.value=id;void open(note)}},{immediate:true})
</script>
<template><div class="page-heading"><div><h1>Notifications</h1></div></div><div class="toolbar"><label class="check-label"><input v-model="unreadOnly" type="checkbox" />Unread only</label></div><section class="card"><div v-if="!notifications.length" class="empty"><PurchaseEmptyState /></div><div v-for="note in notifications" :key="note.id" class="row"><span class="category-icon" :class="{personal:!note.read_at}">{{note.read_at?'✓':'•'}}</span><div class="row-main"><button class="inline-link" @click="open(note)">{{noteLabel(note)}}</button><p>{{new Date(note.created_at).toLocaleString()}}</p></div><span v-if="!note.read_at" class="pill pending">Unread</span></div></section><p v-if="!state.online" class="text-small section-space">Cached updates are available offline. Reconnect to mark them read.</p><PushSettings /></template>
