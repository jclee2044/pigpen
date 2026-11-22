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
import AnalysesView from '../views/AnalysesView.vue'
export default createRouter({history:createWebHistory(import.meta.env.BASE_URL),routes:[
 {path:'/',name:'dashboard',component:DashboardView},
 {path:'/analyses',component:AnalysesView},
 {path:'/analyses/:month',component:AnalysesView,beforeEnter:to=>/^\d{4}-(0[1-9]|1[0-2])$/.test(String(to.params.month))||'/analyses'},
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
