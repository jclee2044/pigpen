import { createRouter, createWebHistory } from 'vue-router'
import ProfilesView from '../views/ProfilesView.vue'
import ProfileEditView from '../views/ProfileEditView.vue'
import DashboardView from '../views/DashboardView.vue'
import BudgetView from '../views/BudgetView.vue'
import PurchasesView from '../views/PurchasesView.vue'
import WishlistView from '../views/WishlistView.vue'
import ApprovalsView from '../views/ApprovalsView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import SettingsView from '../views/SettingsView.vue'
export default createRouter({history:createWebHistory(import.meta.env.BASE_URL),routes:[
 {path:'/',name:'dashboard',component:DashboardView},
 {path:'/purchases',component:PurchasesView},
 {path:'/budget',component:BudgetView},
 {path:'/wish-lists',component:WishlistView},
 {path:'/approvals',component:ApprovalsView},
 {path:'/notifications',component:NotificationsView},
 {path:'/profiles',component:ProfilesView},
 {path:'/profiles/:id/edit',component:ProfileEditView},
 {path:'/settings',component:SettingsView},
 {path:'/:pathMatch(.*)*',redirect:'/'},
],scrollBehavior:()=>({top:0})})
