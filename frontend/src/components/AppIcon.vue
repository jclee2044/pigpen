<script setup lang="ts">
const props = defineProps<{ name: string }>()
const paths: Record<string,string> = {
 comments:'M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5a9.5 9.5 0 0 1 19 0ZM7 9h10M7 13h7',
 profiles:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
 home:'M3 10 12 3l9 7v11h-6v-7H9v7H3Z', receipt:'M6 3h12v18l-3-2-3 2-3-2-3 2V3Zm3 5h6M9 12h6',
 budget:'M3 5h18v16H3ZM3 10h18M8 2v6M16 2v6M8 15h8M12 12v6', heart:'M20.8 4.6c-2.4-2.2-6-1.5-8.8 1.4C9.2 3.1 5.6 2.4 3.2 4.6-2 9.5 5.9 17 12 21c6.1-4 14-11.5 8.8-16.4Z',
 shield:'m12 2 9 4v6c0 5-4 8-9 10-5-2-9-5-9-10V6ZM8 12l3 3 5-6', bell:'M18 8a6 6 0 0 0-12 0c0 8-3 8-3 9h18c0-1-3-1-3-9M10 21h4',
 settings:'m9.5 3-.5 2-2 .9-1.8-.6-2.5 4.3 1.5 1.4v2l-1.5 1.4 2.5 4.3 1.8-.6 2 .9.5 2h5l.5-2 2-.9 1.8.6 2.5-4.3-1.5-1.4v-2l1.5-1.4-2.5-4.3-1.8.6-2-.9-.5-2Zm5.5 9a3 3 0 1 1-6 0 3 3 0 0 1 6 0', edit:'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z', plus:'M12 4v16M4 12h16', arrow:'m9 5 7 7-7 7', check:'m5 12 4 4L19 6', close:'m6 6 12 12M6 18 18 6', sync:'M20 8a8 8 0 0 0-14-3L3 8m0-5v5h5M4 16a8 8 0 0 0 14 3l3-3m0 5v-5h-5',
}
</script>
<template><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="paths[props.name] || paths.home" /></svg></template>
