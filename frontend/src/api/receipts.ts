import { request } from './client'
export interface ReceiptSuggestions {
 item:string;merchant:string|null;amount_minor:number|null;transaction_date:string|null;description:string;
 line_items:Array<{description:string;line_total_minor:number}>;warnings:string[]
}
export interface ReceiptScan {
 id:string;revision:number;actor_id:string;status:'queued'|'processing'|'ready'|'failed'|'canceled'|'confirmed';
 suggestions:ReceiptSuggestions|null;error:string|null;created_at:string;expires_at:string;
 keep_indefinitely:boolean;expired_at:string|null;purchase_id:string|null
}
export const getScan=(id:string)=>request<ReceiptScan>('/receipt-scans/'+id)
export const listScans=(actor:string)=>request<{items:ReceiptScan[]}>('/receipt-scans?actor_id='+actor)
export function uploadScan(file:File,actor:string,id:string,time:string){
 const body=new FormData();body.append('file',file);body.append('actor_id',actor);body.append('operation_id',id);body.append('client_time',time)
 return request<ReceiptScan>('/receipt-scans',{method:'POST',body},30000)
}
