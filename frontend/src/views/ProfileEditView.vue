<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AvatarEditor from '../components/AvatarEditor.vue'
import AppDialog from '../components/AppDialog.vue'
import { state, rows, activeUser, mutate, selectProfile, clearProfile } from '../state/household'
import type { User } from '../api/models'

const route=useRoute(),router=useRouter()
const profile=computed(()=>rows('users').find(user=>user.id===route.params.id&&user.active))
const draft=ref<User>(),saving=ref(false),error=ref(''),confirming=ref(false)
const lastProfile=computed(()=>rows('users').filter(user=>user.active).length<2)
watch(()=>profile.value?.id,async()=>{
 draft.value=profile.value?{...profile.value,avatar:{...profile.value.avatar}}:undefined
 error.value='';confirming.value=false
 if(profile.value)try{await selectProfile(profile.value.id)}catch(e){error.value=e instanceof Error?e.message:'Could not select profile'}
},{immediate:true})
async function save(){
 if(!draft.value)return
 saving.value=true;error.value=''
 try{
  await mutate('user.update',{name:draft.value.name,avatar:draft.value.avatar,active:true,expected_revision:draft.value.revision},draft.value.id)
  await router.push('/profiles')
 }catch(e){error.value=e instanceof Error?e.message:'Could not save profile'}finally{saving.value=false}
}
async function remove(){
 if(!profile.value||lastProfile.value)return
 saving.value=true;error.value=''
 try{
  const user=profile.value
  await mutate('user.update',{name:user.name,avatar:user.avatar,active:false,expected_revision:user.revision},user.id)
  await router.replace('/profiles')
  await clearProfile()
 }catch(e){error.value=e instanceof Error?e.message:'Could not delete profile'}finally{saving.value=false;confirming.value=false}
}
</script>
<template>
 <div class="profile-editor">
  <div class="page-heading"><h1>Edit profile</h1><RouterLink class="button" to="/profiles">Back to profiles</RouterLink></div>
  <p v-if="error" class="notice error" role="alert">{{error}}</p>
  <template v-if="draft&&profile">
   <form class="card" data-defer-app-update @submit.prevent="save">
    <fieldset :disabled="saving||!state.online||activeUser?.id!==profile.id">
     <label>Display name<input v-model="draft.name" required maxlength="200" autocomplete="given-name" /></label>
     <AvatarEditor v-model="draft.avatar" />
     <div class="actions"><button class="button primary">{{saving?'Saving…':'Save profile'}}</button><RouterLink class="button" to="/profiles">Cancel</RouterLink></div>
    </fieldset>
   </form>
   <section class="card delete-profile" aria-labelledby="delete-profile-title">
    <h2 id="delete-profile-title">Delete profile</h2>
    <p>This removes the profile from the profile list. Its financial history will remain.</p>
    <p v-if="lastProfile" class="text-small">Keep at least one active profile. Add another profile before deleting this one.</p>
    <button class="button danger" :disabled="saving||!state.online||lastProfile||activeUser?.id!==profile.id" @click="confirming=true">Delete profile</button>
   </section>
  </template>
  <section v-else class="card"><p>This profile is no longer available.</p><RouterLink to="/profiles">Return to profiles</RouterLink></section>
  <AppDialog v-if="confirming&&profile" title="Delete profile?" @close="!saving&&(confirming=false)">
   <p>Delete {{profile.name}}’s profile? It will no longer appear in the profile list. Its financial history will remain.</p>
   <div class="actions"><button class="button" :disabled="saving" @click="confirming=false">Cancel</button><button class="button danger" :disabled="saving||!state.online||lastProfile" @click="remove">{{saving?'Deleting…':'Confirm delete'}}</button></div>
  </AppDialog>
 </div>
</template>
<style scoped>
.profile-editor{max-width:760px;margin-inline:auto}
.page-heading h1{margin:0}
.delete-profile{margin-top:48px}
@media(max-width:480px){.page-heading{align-items:flex-start;flex-direction:column}}
</style>
