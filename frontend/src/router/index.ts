import { createRouter, createWebHistory } from 'vue-router'
import PlaceholderView from '../views/PlaceholderView.vue'
import ProfilesView from '../views/ProfilesView.vue'
export default createRouter({history:createWebHistory(import.meta.env.BASE_URL),routes:[
 {path:'/',name:'dashboard',component:PlaceholderView,props:{title:'Dashboard'}},
 {path:'/purchases',component:PlaceholderView,props:{title:'Purchases'}},
 {path:'/budget',component:PlaceholderView,props:{title:'Budget'}},
 {path:'/wish-lists',component:PlaceholderView,props:{title:'Wish lists'}},
 {path:'/approvals',component:PlaceholderView,props:{title:'Approvals'}},
 {path:'/notifications',component:PlaceholderView,props:{title:'Notifications'}},
 {path:'/profiles',component:ProfilesView},
 {path:'/:pathMatch(.*)*',redirect:'/'},
],scrollBehavior:()=>({top:0})})
