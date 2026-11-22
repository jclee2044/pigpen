import { request } from './client'

export interface ReviewPurchase { id:string; item:string; merchant:string|null; transaction_date:string; amount_minor:number; category_id:string; category_explanation:string }
export interface Finding { id:string; kind:'trend'|'budget'|'category_group'|'observation'; title:string; explanation:string; category_id:string|null; suggested_category:string|null; chart:{label:string;amount_minor:number}[]; purchases:ReviewPurchase[] }
export interface ReviewSummary { id:string; month:string; created_at:string; finding_count:number; remaining_minor:number; is_preview?:boolean }
export interface Review {
 id:string; month:string; created_at:string; summary:string; findings:Finding[]; data_changed:boolean; chat_enabled:boolean
 totals:{budgeted_minor:number;spent_minor:number;remaining_minor:number;savings_allocated_minor:number;savings_actual_minor:number;income_minor:number}
 coverage:{comparison_months:string[];purchase_count:number;included_purchase_count:number}
}
export interface ReviewList { items:ReviewSummary[]; next_before:string|null; latest:ReviewSummary|null; current_month:string; show_home:boolean; enabled:boolean }
export const getReviews=(before?:string)=>request<ReviewList>('/advisor/reviews'+(before?'?before='+encodeURIComponent(before):''))
export const getReview=(month:string)=>request<Review>('/advisor/reviews/'+encodeURIComponent(month))
