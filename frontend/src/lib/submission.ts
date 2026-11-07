import { ref } from 'vue'
import { message,PendingSubmissionError,retryPending } from '../state/household'
export function useSubmission(){
 const saving=ref(false),error=ref(''),retryId=ref('')
 async function run(action:()=>Promise<unknown>,done:(result:unknown)=>void|Promise<void>){
  if(saving.value)return
  saving.value=true;error.value=''
  try{const result=retryId.value?await retryPending(retryId.value):await action();retryId.value='';await done(result)}
  catch(e){error.value=message(e);if(e instanceof PendingSubmissionError)retryId.value=e.submissionId}
  finally{saving.value=false}
 }
 return {saving,error,retryId,run}
}
