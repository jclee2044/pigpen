import type { ChangePage,Snapshot,Records } from '../api/models'
import { emptyRecords } from '../api/models'
export function applyPage(snapshot:Snapshot,page:ChangePage):Snapshot{
 const records:Records=JSON.parse(JSON.stringify(snapshot.records))
 let cursor=snapshot.cursor
 for(const change of page.changes){
  if(!(change.resource in emptyRecords())||!Number.isSafeInteger(change.cursor)||change.cursor<=cursor||typeof change.record.id!=='string'||!Number.isSafeInteger(change.record.revision))throw new Error('Could not safely read the latest changes. Update PigPen before syncing again.')
  const existing=records[change.resource].find(x=>x.id===change.record.id)
  if(!existing||existing.revision<=change.record.revision){
   Object.assign(records,{[change.resource]:[...records[change.resource].filter(x=>x.id!==change.record.id),change.record]})
  }
  cursor=change.cursor
 }
 if(cursor!==page.next_cursor||(!page.changes.length&&page.has_more))throw new Error('Incomplete sync page. No local cursor was advanced.')
 return {cursor,records}
}
