import { reactive,watch } from 'vue'
import { today } from '../lib/money'
function rememberedMonth(){try{return localStorage.getItem('pigpen-month')||today().slice(0,7)}catch{return today().slice(0,7)}}
export const shell = reactive({ month:rememberedMonth(), message:'', error:'' })
watch(()=>shell.month,value=>{try{localStorage.setItem('pigpen-month',value)}catch{/* Month preference is optional; financial writes use IndexedDB. */}})
