import type { Avatar } from './generated'
export interface Row { id: string; revision: number; deleted: boolean; created_at: string; updated_at: string; household_id: string }
export interface Household extends Row { name: string; currency: string; timezone: string; approval_policy: 'all' }
export interface User extends Row { name: string; avatar: Required<Avatar>; active: boolean }
export interface Category extends Row { name: string; kind: 'expense'|'personal'|'savings'; owner_id: string|null; parent_id: string|null; active: boolean }
export interface Budget extends Row { month: string; expected_income_minor: number }
export interface Allocation extends Row { budget_month_id: string; category_id: string; amount_minor: number }
export interface Purchase extends Row { purchaser_id: string; category_id: string; item: string; amount_minor: number; transaction_date: string; merchant: string|null; description: string; request_id: string|null; bill_id: string|null; bill_due: string|null }
export interface Income extends Row { user_id: string; amount_minor: number; transaction_date: string; description: string }
export interface Savings extends Income { kind: 'opening'|'contribution'|'withdrawal' }
export interface Bill extends Row { name: string; amount_minor: number; category_id: string; due_day: number; start_date: string; description: string; active: boolean }
export interface Occurrence { id: string; bill_id: string; name: string; due_date: string; expected_minor: number; purchase_id: string|null }
export interface Wish extends Row { owner_id: string; name: string; price_minor: number; description: string; url: string|null; status: 'active'|'purchased'|'archived' }
export interface Request extends Row { requester_id: string; item: string; amount_minor: number; description: string; url: string|null; category_id: string|null; status: 'open'|'canceled'|'purchased'; purchase_id: string|null; approved_revision: number|null }
export interface Vote extends Row { request_id: string; reviewer_id: string; approved: boolean; request_revision: number }
export interface Comment extends Row { actor_id: string; target_resource: 'wishlist-items'|'approval-requests'; target_id: string; text: string }
export interface Note extends Row { recipient_id: string; kind: string; target_resource: string; target_id: string; read_at: string|null }
export interface Attachment extends Row { purchase_id: string; filename: string; media_type: string; byte_size: number; checksum: string }
export interface Resources { household: Household; users: User; categories: Category; 'budget-months': Budget; allocations: Allocation; purchases: Purchase; income: Income; savings: Savings; 'recurring-bills': Bill; 'bill-occurrences': Row; 'wishlist-items': Wish; 'approval-requests': Request; 'approval-votes': Vote; comments: Comment; notifications: Note; attachments: Attachment }
export type Records = { [K in keyof Resources]: Resources[K][] }
export interface Snapshot { cursor: number; records: Records }
export interface Change { cursor: number; resource: keyof Resources; record: Row }
export interface ChangePage { changes: Change[]; next_cursor: number; has_more: boolean }
export const emptyRecords = (): Records => ({ household:[],users:[],categories:[],'budget-months':[],allocations:[],purchases:[],income:[],savings:[],'recurring-bills':[],'bill-occurrences':[],'wishlist-items':[],'approval-requests':[],'approval-votes':[],comments:[],notifications:[],attachments:[] })
