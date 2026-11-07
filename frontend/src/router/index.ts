import { createRouter, createWebHistory } from 'vue-router'
import PlaceholderView from '../views/PlaceholderView.vue'
export default createRouter({history:createWebHistory(import.meta.env.BASE_URL),routes:[
 {path:'/',name:'dashboard',component:PlaceholderView,props:{title:'Dashboard'}},
 {path:'/purchases',component:PlaceholderView,props:{title:'Purchases'}},
 {path:'/budget',component:PlaceholderView,props:{title:'Budget'}},
 {path:'/wish-lists',component:PlaceholderView,props:{title:'Wish lists'}},
 {path:'/approvals',component:PlaceholderView,props:{title:'Approvals'}},
 {path:'/notifications',component:PlaceholderView,props:{title:'Notifications'}},
 {path:'/profiles',component:PlaceholderView,props:{title:'Profiles & settings'}},
 {path:'/:pathMatch(.*)*',redirect:'/'},
],scrollBehavior:()=>({top:0})})
