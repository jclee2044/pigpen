<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { state,rows,activeUser,household,mutate,selectProfile,setError } from '../state/household'
import type { Avatar } from '../api/generated'
import type { User } from '../api/models'
import PigAvatar from '../components/PigAvatar.vue'
import AvatarEditor from '../components/AvatarEditor.vue'
import AppDialog from '../components/AppDialog.vue'
import InstallCard from '../components/InstallCard.vue'
const router=useRouter();const householdName=ref('Our household');const name=ref('');const editing=ref<User>();const formOpen=ref(false);const saving=ref(false);const formError=ref('')
const defaultAvatar=():Required<Avatar>=>({background:'cream',bandana:'grass',glasses:'none',hat:'none',eyelashes:'none'})
const avatar=ref(defaultAvatar())
function newProfile(){editing.value=undefined;name.value='';avatar.value=defaultAvatar();formError.value='';formOpen.value=true}
function editProfile(){if(!activeUser.value)return;editing.value=activeUser.value;name.value=activeUser.value.name;avatar.value={...activeUser.value.avatar};formError.value='';formOpen.value=true}
async function initialize(){saving.value=true;try{await mutate('household.initialize',{name:householdName.value});newProfile()}catch(e){setError(e)}finally{saving.value=false}}
async function choose(id:string){try{await selectProfile(id);await router.push('/')}catch(e){setError(e)}}
async function save(){saving.value=true;formError.value='';try{if(editing.value){await mutate('user.update',{name:name.value,avatar:avatar.value,active:true,expected_revision:editing.value.revision},editing.value.id)}else{const user=await mutate('user.create',{name:name.value,avatar:avatar.value}) as User;await selectProfile(user.id)}formOpen.value=false;await router.push('/')}catch(e){formError.value=e instanceof Error?e.message:'Could not save profile'}finally{saving.value=false}}
async function archive(){if(!activeUser.value)return;if(!confirm('Archive this profile? Its financial history will remain.'))return;try{await mutate('user.update',{name:activeUser.value.name,avatar:activeUser.value.avatar,active:false,expected_revision:activeUser.value.revision},activeUser.value.id);state.selectedId=''}catch(e){setError(e)}}
</script>
<template>
 <div class="page-heading"><div><p class="eyebrow">SMALL STEPS, TOGETHER</p><h1>{{household?'Who’s planning today?':'Welcome to PigPen'}}</h1><p>{{household?'Choose your profile or make a new pig.':'A shared home for your household’s plans.'}}</p></div><button v-if="household" class="button primary" :disabled="!state.online" @click="newProfile">Add profile</button></div>
 <section v-if="!household" class="onboarding card"><h2>A little planning. More room to live.</h2><p>Start your household, choose a pig, and make a plan together. Everyone in your household can see the shared records.</p><form @submit.prevent="initialize"><label>Household name<input v-model="householdName" required maxlength="200" /></label><p class="text-small">USD · America/New_York · Shared household records</p><button class="button primary" :disabled="saving||!state.online">{{saving?'Creating…':'Create household'}}</button></form></section>
 <template v-else><div class="profile-grid"><button v-for="user in rows('users').filter(x=>x.active)" :key="user.id" class="profile-card" :class="{active:user.id===state.selectedId}" @click="choose(user.id)"><PigAvatar :avatar="user.avatar" :size="68" :label="user.name+'’s pig'" /><span><strong>{{user.name}}</strong><small>{{user.id===state.selectedId?'Selected on this device':'Choose this profile'}}</small></span></button></div><div v-if="activeUser" class="section-heading"><h2>Your profile</h2><div class="actions"><button class="button" :disabled="!state.online" @click="editProfile">Edit name & avatar</button><button class="button danger" :disabled="!state.online||rows('users').filter(x=>x.active).length<2" @click="archive">Archive profile</button></div></div><p class="text-small muted">Profile selection records who made a change. There’s no password or PIN. Queued actions keep the profile that created them.</p></template>
 <InstallCard /><AppDialog v-if="formOpen" :title="editing?'Your pig, your style':'Meet your household pig'" @close="formOpen=false"><form @submit.prevent="save"><div v-if="formError" role="alert" class="notice error">{{formError}}</div><label>Display name<input v-model="name" required maxlength="200" autocomplete="given-name" /></label><AvatarEditor v-model="avatar" /><button class="button primary" :disabled="saving">{{saving?'Saving…':editing?'Save profile':'Create profile'}}</button></form></AppDialog>
</template>
