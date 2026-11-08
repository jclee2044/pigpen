<script setup lang="ts">
import AppIcon from './AppIcon.vue'
import AppLoading from './AppLoading.vue'
import { computed,ref } from 'vue'
import type { Category } from '../api/models'
import { activeUser,mutate,rows,state } from '../state/household'
import { useSubmission } from '../lib/submission'
import AppDialog from './AppDialog.vue'
import CategoryForm from './CategoryForm.vue'
import CategoryDeleteDialog from './CategoryDeleteDialog.vue'
import SwipeWish from './SwipeWish.vue'
const groups=computed(()=>{
 const categories=rows('categories')
 return categories.filter(c=>!c.parent_id).map(parent=>({parent,items:[parent,...categories.filter(c=>c.parent_id===parent.id)]}))
})
const emit=defineEmits<{close:[]}>()
const editing=ref<Category>(),restoring=ref<Category>(),adding=ref(false),parent=ref<Category>()
const deleting=ref<Category>(),openId=ref('')
function canDelete(category:Category){return category.active&&canEdit(category)&&!(category.kind==='personal'&&!category.parent_id)}
const {saving,error,retryId,run}=useSubmission()
function canEdit(category:Category){return !category.owner_id||category.owner_id===activeUser.value?.id}
async function unarchive(category:Category){
 restoring.value=category
 await run(()=>mutate('category.update',{name:category.name,active:true,expected_revision:category.revision},category.id),()=>{restoring.value=undefined})
 if(!retryId.value)restoring.value=undefined
}
</script>
<template>
 <CategoryDeleteDialog v-if="deleting" :category="deleting" @close="deleting=undefined" @deleted="deleting=undefined" />
 <CategoryForm v-else-if="editing||adding" :category="editing" :parent-category="parent" @close="editing=undefined;adding=false;parent=undefined" />
 <AppDialog v-else title="Manage categories" @close="emit('close')"><AppLoading v-if="saving" compact label="Saving…" />
  <div class="category-toolbar"><button class="button primary icon-only" aria-label="Add category" title="Add category" :disabled="!state.online" @click="adding=true"><AppIcon name="plus" /></button></div>
  <div v-if="error" role="alert" class="notice error">{{error}}</div>
  <button v-if="retryId&&restoring" class="button" :disabled="saving||!state.online" @click="unarchive(restoring)">Retry unarchive</button>
  <div class="category-list"><div v-for="group in groups" :key="group.parent.id" class="category-group" :aria-label="group.parent.name">
  <SwipeWish v-for="category in group.items" :key="category.id" :id="category.id" :name="category.name+' category'" :enabled="canDelete(category)&&state.online&&!saving&&!retryId" :open="openId===category.id" @reveal="openId=$event" @delete="deleting=category">
  <div class="category-row" :class="{'subcategory-row':category.parent_id}">
   <div class="row-main"><strong>{{category.name}}</strong><p v-if="!category.active" class="text-small">Archived</p></div>
   <div v-if="canEdit(category)" class="actions">
    <button class="button icon-only category-edit" :aria-label="'Edit name of '+category.name" :title="'Edit '+category.name" :disabled="!state.online||saving||!!retryId" @click="editing=category"><AppIcon name="edit" /></button>
    <button v-if="!category.active&&!(category.kind==='personal'&&!category.parent_id)" class="button small" :aria-label="'Unarchive '+category.name" :disabled="!state.online||saving||!!retryId" @click="unarchive(category)">{{saving&&restoring?.id===category.id?'Restoring…':'Unarchive'}}</button>
   </div>
  </div>
  </SwipeWish>
  <div v-if="group.parent.active&&canEdit(group.parent)&&(group.parent.allows_subcategories||group.parent.kind==='personal')" class="category-footer">
    <button class="button small" :aria-label="'Add subcategory to '+group.parent.name" :disabled="!state.online||saving||!!retryId" @click="parent=group.parent;adding=true">+ Add subcategory</button>
  </div>
  </div></div>
 </AppDialog>
</template>
<style scoped>
.category-toolbar{display:flex;justify-content:flex-end;margin-bottom:12px}
.category-list{display:grid;gap:12px}
.category-group{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:0 12px;min-width:0}
.category-group :deep(.wish-swipe){border-radius:0}
.category-row{background:var(--paper);display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:12px;padding:12px 0}
.subcategory-row{margin-left:16px;padding:8px 0;border-top:1px solid var(--line)}
.subcategory-row strong{font-size:14px;font-weight:400}
.row-main{min-width:0;flex:1 1 100px;overflow-wrap:anywhere}
.row-main p{margin:4px 0 0}
.actions{justify-content:flex-end}
.category-footer{padding:8px 0 12px}
.category-edit{width:35.2px;height:35.2px;min-height:35.2px;padding:8px;border-radius:8.8px}
.category-edit svg{width:14.4px;height:14.4px}
</style>
