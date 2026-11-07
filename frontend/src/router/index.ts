import { createRouter, createWebHistory } from 'vue-router'
import PlaceholderView from '../views/PlaceholderView.vue'
import ProfilesView from '../views/ProfilesView.vue'
import DashboardView from '../views/DashboardView.vue'
import BudgetView from '../views/BudgetView.vue'
import PurchasesView from '../views/PurchasesView.vue'
export default createRouter({history:createWebHistory(import.meta.env.BASE_URL),routes:[
 {path:'/',name:'dashboard',component:DashboardView},
 {path:'/purchases',component:PurchasesView},
 {path:'/budget',component:BudgetView},
 {path:'/wish-lists',component:PlaceholderView,props:{title:'Wish lists'}},
 {path:'/approvals',component:PlaceholderView,props:{title:'Approvals'}},
 {path:'/notifications',component:PlaceholderView,props:{title:'Notifications'}},
 {path:'/profiles',component:ProfilesView},
 {path:'/:pathMatch(.*)*',redirect:'/'},
],scrollBehavior:()=>({top:0})})
