<script setup lang="ts">
import { ref,onUnmounted,watch } from 'vue'
import { getScan,uploadScan,type ReceiptScan } from '../api/receipts'
import { activeUser,state,mutate,message } from '../state/household'
import AppDialog from './AppDialog.vue'
import ReceiptCamera from './ReceiptCamera.vue'
import AppLoading from './AppLoading.vue'
import PurchaseForm from './PurchaseForm.vue'
const emit=defineEmits<{close:[]}>()
const actor=activeUser.value?.id??''
const scan=ref<ReceiptScan>(),file=ref<File>(),error=ref(''),busy=ref(false)
let id=crypto.randomUUID(),time=new Date().toISOString(),timer:ReturnType<typeof setTimeout>|undefined,disposed=false
watch(()=>state.selectedId,()=>emit('close'))
onUnmounted(()=>{disposed=true;clearTimeout(timer)})
async function poll(){
 if(disposed||!scan.value)return
 try{scan.value=await getScan(scan.value.id);error.value=''}catch(e){error.value=message(e)}
 if(!disposed&&['queued','processing'].includes(scan.value.status))timer=setTimeout(()=>void poll(),1500)
}
function choose(photo:File){file.value=photo;id=crypto.randomUUID();time=new Date().toISOString();error.value='';void upload()}
function retake(){clearTimeout(timer);scan.value=undefined;file.value=undefined;error.value=''}
async function upload(){
 if(!file.value||busy.value)return
 if(!state.online){error.value='Reconnect to scan, then retry.';return}
 if(file.value.size>10*1024*1024){error.value='Choose a JPEG, PNG or WebP up to 10 MiB.';return}
 busy.value=true;error.value=''
 try{scan.value=await uploadScan(file.value,actor,id,time);await poll()}catch(e){error.value=message(e)}finally{busy.value=false}
}
async function action(kind:'receipt.retry'|'receipt.cancel',takeAgain=false){
 if(!scan.value||busy.value)return
 busy.value=true;error.value=''
 try{await mutate(kind,{expected_revision:scan.value.revision},scan.value.id);if(kind==='receipt.cancel'){if(takeAgain)retake();else emit('close')}else await poll()}
 catch(e){error.value=message(e);await poll()}finally{busy.value=false}
}
</script>
<template>
 <PurchaseForm v-if="scan?.status==='ready'" :key="scan.id" :receipt="scan" @retake="retake" @close="emit('close')" />
 <ReceiptCamera v-else-if="!scan&&!file" @close="emit('close')" @photo="choose" />
 <AppDialog v-else centered title="Scan receipt" @close="emit('close')">
  <p v-if="error" class="notice error" role="alert">{{error}}</p>
  <template v-if="scan">
   <AppLoading v-if="scan.status==='queued'||scan.status==='processing'" compact :label="scan.status==='processing'?'Reading receipt…':'Scanning receipt…'" />
   <p v-else role="status">{{scan.status==='confirmed'?'This receipt has already been saved.':scan.error??'Scan canceled.'}}</p>
   <button v-if="scan.status==='failed'" class="button primary" :disabled="busy||!state.online" @click="action('receipt.cancel',true)">Retake photo</button>
   <button v-if="scan.status==='failed'" class="button" :disabled="busy||!state.online" @click="action('receipt.retry')">Retry scan</button>
   <button v-if="scan.status!=='confirmed'" class="button scan-cancel" :disabled="busy||!state.online" @click="action('receipt.cancel')">Cancel</button>
  </template>
  <template v-else>
   <AppLoading v-if="busy" compact label="Scanning receipt…" />
   <button v-if="!busy" class="button primary" :disabled="!file||!state.online" @click="upload">Retry scan</button>
   <p v-if="!state.online" class="notice">Reconnect to scan. You can still add a purchase manually.</p>
   <button class="button" :disabled="busy" @click="retake">Retake photo</button>
  </template>
 </AppDialog>
</template>

<style scoped>
.scan-cancel{display:block;width:100%;margin-top:16px}
</style>
