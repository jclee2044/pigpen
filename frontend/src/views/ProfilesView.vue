<script setup lang="ts">
import AppLoading from '../components/AppLoading.vue'
import AppIcon from '../components/AppIcon.vue'
import PurchaseEmptyState from '../components/PurchaseEmptyState.vue'
import { ref } from 'vue'
import { useRoute,useRouter } from 'vue-router'
import { state,rows,household,mutate,selectProfile,setError } from '../state/household'
import type { Avatar } from '../api/generated'
import type { User } from '../api/models'
import PigAvatar from '../components/PigAvatar.vue'
import AvatarEditor from '../components/AvatarEditor.vue'
import AppDialog from '../components/AppDialog.vue'
defineProps<{entry?:boolean}>()
const router=useRouter();const householdName=ref('Our household');const name=ref('');const formOpen=ref(false);const saving=ref(false);const formError=ref('')
const route=useRoute()
const defaultAvatar=():Required<Avatar>=>({background:'cream',bandana:'grass',glasses:'none',hat:'none',eyelashes:'none'})
const avatar=ref(defaultAvatar())
function newProfile(){name.value='';avatar.value=defaultAvatar();formError.value='';formOpen.value=true}
async function initialize(){saving.value=true;try{await mutate('household.initialize',{name:householdName.value});newProfile()}catch(e){setError(e)}finally{saving.value=false}}
async function openEditor(event:MouseEvent,id:string){if(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||event.button!==0)return;event.preventDefault();try{await selectProfile(id);await router.push('/profiles/'+id+'/edit')}catch(e){setError(e)}}
async function choose(id:string){const destination=route.path==='/profiles'?'/':route.fullPath;try{await selectProfile(id);await router.push(destination)}catch(e){setError(e)}}
async function save(){saving.value=true;formError.value='';try{const user=await mutate('user.create',{name:name.value,avatar:avatar.value}) as User;await selectProfile(user.id);formOpen.value=false;await router.push('/')}catch(e){formError.value=e instanceof Error?e.message:'Could not save profile'}finally{saving.value=false}}
</script>
<template>
 <div :class="{'profile-entry':entry}">
 <img v-if="entry" class="entry-logo" src="/icons/icon-512.png" alt="PigPen" width="192" height="192" />
 <div class="page-heading"><div><h1>{{household?(entry?'Choose or create your profile':'Profiles'):'Create household'}}</h1></div><button v-if="household" class="button primary" :disabled="!state.online" @click="newProfile">Add profile</button></div>
 <section v-if="!household" class="onboarding card"><form @submit.prevent="initialize"><AppLoading v-if="saving" compact /><label>Household name<input v-model="householdName" required maxlength="200" /></label><p class="text-small">USD · America/New_York · Shared household records</p><button class="button primary" :disabled="saving||!state.online">{{saving?'Creating…':'Create household'}}</button></form></section>
 <template v-else><PurchaseEmptyState v-if="!entry&&!rows('users').some(x=>x.active)" /><div class="profile-grid"><article v-for="user in rows('users').filter(x=>x.active)" :key="user.id" class="profile-card" :class="{active:user.id===state.selectedId}"><button class="profile-choose" :aria-label="user.name+' — '+(user.id===state.selectedId?'Selected on this device':'Choose this profile')" @click="choose(user.id)"></button><PigAvatar :avatar="user.avatar" :size="68" :label="user.name+'’s pig'" /><strong class="profile-name">{{user.name}}</strong><RouterLink class="profile-edit-link" :to="'/profiles/'+user.id+'/edit'" :aria-label="'Edit '+user.name" :title="'Edit '+user.name" @click="openEditor($event,user.id)"><AppIcon name="edit" /></RouterLink><small class="profile-status">{{user.id===state.selectedId?'Selected on this device':'Choose this profile'}}</small></article></div></template>
 <p v-if="entry&&household" class="entry-help">Choose your profile to enter PigPen, or add a new one. Your choice is saved on this device.</p>
 <AppDialog v-if="formOpen" title="Create profile" @close="formOpen=false"><AppLoading v-if="saving" compact /><form @submit.prevent="save"><div v-if="formError" role="alert" class="notice error">{{formError}}</div><label>Display name<input v-model="name" required maxlength="200" autocomplete="given-name" /></label><AvatarEditor v-model="avatar" /><button class="button primary" :disabled="saving">{{saving?'Saving…':'Create profile'}}</button></form></AppDialog>
 </div>
</template>

<style scoped>
.profile-grid{grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))}
.profile-card{position:relative;display:grid;grid-template-columns:68px minmax(0,1fr) 44px;column-gap:12px;row-gap:0;padding:22px;align-items:center}
.profile-choose{position:absolute;inset:0;width:100%;height:100%;border:0;border-radius:16px;background:transparent;color:inherit}
.profile-card :deep(.pig-avatar){grid-column:1;grid-row:1/3;pointer-events:none}
.profile-card .profile-name{grid-column:2;grid-row:1;pointer-events:none;line-height:1.4;overflow-wrap:anywhere}
.profile-card .profile-status{grid-column:2/4;grid-row:2;pointer-events:none;margin-top:0;line-height:24px}
.profile-edit-link{grid-column:3;grid-row:1;width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:10px;z-index:1}
.profile-edit-link:hover{background:var(--blush)}
.profile-edit-link svg{width:20px;height:20px}
</style>
