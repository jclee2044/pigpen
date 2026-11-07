<script setup lang="ts">
const props = defineProps<{ name: string }>()
const paths: Record<string,string> = {
 home:'M3 10 12 3l9 7v11h-6v-7H9v7H3Z', receipt:'M6 3h12v18l-3-2-3 2-3-2-3 2V3Zm3 5h6M9 12h6',
 budget:'M3 5h18v16H3ZM3 10h18M8 2v6M16 2v6M8 15h8M12 12v6', heart:'M20.8 4.6c-2.4-2.2-6-1.5-8.8 1.4C9.2 3.1 5.6 2.4 3.2 4.6-2 9.5 5.9 17 12 21c6.1-4 14-11.5 8.8-16.4Z',
 shield:'m12 2 9 4v6c0 5-4 8-9 10-5-2-9-5-9-10V6ZM8 12l3 3 5-6', bell:'M18 8a6 6 0 0 0-12 0c0 8-3 8-3 9h18c0-1-3-1-3-9M10 21h4',
 settings:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2', plus:'M12 4v16M4 12h16', arrow:'m9 5 7 7-7 7', check:'m5 12 4 4L19 6', close:'m6 6 12 12M6 18 18 6', sync:'M20 8a8 8 0 0 0-14-3L3 8m0-5v5h5M4 16a8 8 0 0 0 14 3l3-3m0 5v-5h-5',
}
</script>
<template><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="paths[props.name] || paths.home" /></svg></template>
