from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select
from . import schema as s
from .domain import due_date, month_bounds
from .records import get, expect
from .errors import DomainError


class FinanceServices:
    def do_income_create(self,c,op):
        return self.save(c,s.income_entries,dict(id=op['entity_id'],user_id=op['actor_id'],**op['data']))

    def do_income_update(self,c,op):
        row=get(c,s.income_entries,op['entity_id']); data=dict(op['data']);expect(row,data.pop('expected_revision'))
        return self.save(c,s.income_entries,data,row)

    def delete_entry(self,c,op,table):
        row=get(c,table,op['entity_id']);expect(row,op['data']['expected_revision'])
        return self.save(c,table,{'deleted':True},row)

    def do_income_delete(self,c,op):
        return self.delete_entry(c,op,s.income_entries)

    def do_savings_create(self,c,op):
        data=op['data']
        if data['kind']=='opening' and c.execute(select(s.savings_entries.c.id).where(s.savings_entries.c.kind=='opening',s.savings_entries.c.deleted==False)).first():
            raise DomainError('opening_exists','An opening savings balance already exists',409)
        return self.save(c,s.savings_entries,dict(id=op['entity_id'],user_id=op['actor_id'],**data))

    def do_savings_delete(self,c,op):
        return self.delete_entry(c,op,s.savings_entries)

    def bill_category(self,c,category_id):
        category=get(c,s.categories,category_id,active=True)
        if category['kind']=='savings':
            raise DomainError('category','Bills must use an expense or Personal category')
        if category['parent_id']:
            get(c,s.categories,category['parent_id'],active=True)

    def do_bill_create(self,c,op):
        self.bill_category(c,op['data']['category_id'])
        return self.save(c,s.recurring_bills,dict(id=op['entity_id'],**op['data'],active=True))

    def do_bill_update(self,c,op):
        row=get(c,s.recurring_bills,op['entity_id']);data=dict(op['data']);expect(row,data.pop('expected_revision'))
        self.bill_category(c,data['category_id'])
        return self.save(c,s.recurring_bills,data,row)

    def do_bill_pay(self,c,op):
        data=op['data'];bill=get(c,s.recurring_bills,data['bill_id'],active=True)
        due=data['due_date']
        if due != due_date(due[:7],bill['due_day']) or due < bill['start_date']:
            raise DomainError('bill_due','Date is not an occurrence of this bill')
        previous=c.execute(select(s.bill_occurrences).where(s.bill_occurrences.c.bill_id==bill['id'],s.bill_occurrences.c.due_date==due)).mappings().first()
        if previous:
            raise DomainError('already_paid','This bill occurrence is already linked to a purchase',409,dict(previous))
        self.bill_category(c,bill['category_id'])
        if data['purchase_id']:
            purchase=get(c,s.purchases,data['purchase_id'])
            if purchase['bill_id'] or purchase['category_id']!=bill['category_id']:
                raise DomainError('bill_link','Purchase is already linked or uses a different category',409)
            purchase=self.save(c,s.purchases,{'bill_id':bill['id'],'bill_due':due},purchase)
        else:
            purchase=self.save(c,s.purchases,dict(id=op['entity_id'],purchaser_id=op['actor_id'],category_id=bill['category_id'],
                item=bill['name'],amount_minor=data['amount_minor'] or bill['amount_minor'],transaction_date=data['transaction_date'],
                merchant=None,description=bill['description'],request_id=None,bill_id=bill['id'],bill_due=due))
            self.notify(c,op,'purchase.created','purchases',purchase['id'])
            self.spending_alerts(c,purchase['transaction_date'][:7],op,purchase['category_id'])
        self.save(c,s.bill_occurrences,dict(id=str(uuid5(NAMESPACE_URL,bill['id']+'/'+due)),bill_id=bill['id'],due_date=due,
            expected_minor=bill['amount_minor'],purchase_id=purchase['id']))
        return purchase

    def upcoming_bills(self,c,month):
        month_bounds(month)
        paid={r['bill_id']:dict(r) for r in c.execute(select(s.bill_occurrences).where(s.bill_occurrences.c.due_date.like(month+'-%'))).mappings()}
        items=[]
        for bill in c.execute(select(s.recurring_bills).where(s.recurring_bills.c.deleted==False)).mappings():
            occurrence=paid.get(bill['id'])
            due=occurrence['due_date'] if occurrence else due_date(month,bill['due_day'])
            if not occurrence and (due<bill['start_date'] or not bill['active']):
                continue
            items.append(dict(id=str(uuid5(NAMESPACE_URL,bill['id']+'/'+due)),bill_id=bill['id'],name=bill['name'],due_date=due,
                              expected_minor=occurrence['expected_minor'] if occurrence else bill['amount_minor'],
                              purchase_id=occurrence['purchase_id'] if occurrence else None))
        return items
