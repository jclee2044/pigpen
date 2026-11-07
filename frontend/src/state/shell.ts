import { reactive } from 'vue'
import { today } from '../lib/money'
export const shell = reactive({ month:today().slice(0,7), message:'', error:'' })
