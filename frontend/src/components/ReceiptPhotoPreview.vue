<script setup lang="ts">
import { ref } from 'vue'
import PurchaseImageViewer from './PurchaseImageViewer.vue'
defineProps<{src:string}>()
const expanded=ref(false)
</script>
<template>
 <button type="button" class="receipt-photo" aria-label="Enlarge receipt photo" @click="expanded=true"><img :src="src" alt="Receipt photo" /></button>
 <PurchaseImageViewer v-if="expanded" :src="src" filename="Receipt photo" @close="expanded=false" />
</template>
<style scoped>
.receipt-photo{display:block;max-width:100%;margin:0 auto 12px;padding:0;border:0;background:transparent;border-radius:10px;overflow:hidden;cursor:zoom-in}
.receipt-photo img{display:block;max-width:100%;max-height:260px;object-fit:contain}
</style>
