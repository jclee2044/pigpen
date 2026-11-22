from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select
from . import schema as s
from .records import get, expect
from .errors import DomainError
from .domain import budget_summary, month_bounds
from .category_months import CategoryMonthServices


class BudgetServices(CategoryMonthServices):
    def prior_plan(self, c, month):
        return c.execute(select(s.budget_months).where(
            s.budget_months.c.month < month, s.budget_months.c.deleted==False
        ).order_by(s.budget_months.c.month.desc()).limit(1)).mappings().first()

    def summary(self, c, month):
        month_bounds(month)
        budget = c.execute(select(s.budget_months).where(s.budget_months.c.month==month)).mappings().first()
        included, allocations, expected_income = self.resolved_month(c, month)
        def rows(table):
            return list(c.execute(select(table)).mappings())
        result = budget_summary(month, rows(s.categories), allocations, rows(s.purchases),
                                rows(s.income_entries),
                                rows(s.savings_entries),
                                expected_income, included)
        result['budget'] = dict(budget) if budget else None
        return result

    def do_budget_set(self, c, op):
        data = op['data']; month=data['month']
        self.freeze_elapsed(c)
        monthly = self.establish_month(c, month)
        included, frozen_allocations, _ = self.resolved_month(c, month)
        budget = c.execute(select(s.budget_months).where(s.budget_months.c.month==month)).mappings().first()
        if budget:
            budget=dict(budget)
            if budget['id'] != op['entity_id']:
                raise DomainError('budget', 'Use the existing budget ID', 409, budget)
            expect(budget,data['expected_revision'])
        elif data['expected_revision']:
            raise DomainError('revision_conflict','New budgets require revision 0',409)
        new_allocations=data['allocations']
        existing_allocations={r['category_id']:dict(r) for r in c.execute(select(s.allocations).where(
            s.allocations.c.budget_month_id==budget['id'],s.allocations.c.deleted==False)).mappings()} if budget else {}
        if new_allocations is None and budget:
            new_allocations=[{'category_id':a['category_id'],'amount_minor':a['amount_minor']} for a in existing_allocations.values()]
        if new_allocations is None and not budget:
            new_allocations = list(frozen_allocations)
        # Removed allocations remain unchanged, including with an older client.
        retained = {a['category_id']: a for a in frozen_allocations if a['category_id'] not in included}
        if new_allocations is not None:
            supplied = {a['category_id'] for a in new_allocations}
            new_allocations = [*new_allocations, *(a for key, a in retained.items() if key not in supplied)]
        if new_allocations is not None:
            identifiers=[a['category_id'] for a in new_allocations]
            if len(set(identifiers))!=len(identifiers):
                raise DomainError('allocations','Duplicate category allocation')
            for a in new_allocations:
                cat=get(c,s.categories,a['category_id'])
                previous=retained.get(a['category_id'])
                if cat['id'] not in included and (not previous or previous['amount_minor']!=a['amount_minor']):
                    raise DomainError('allocations','Add the category before changing its allocation')
                if cat['parent_id']:
                    raise DomainError('allocations','Subcategories classify purchases; allocate to the parent')
            savings_ids=[a['category_id'] for a in new_allocations if get(c,s.categories,a['category_id'])['kind']=='savings']
            if len(savings_ids)>1:
                raise DomainError('allocations','Use the shared Savings category')
        budget=self.save(c,s.budget_months,dict(id=op['entity_id'],month=month,expected_income_minor=data['expected_income_minor']),budget)
        if new_allocations is not None:
            old={r['category_id']:dict(r) for r in c.execute(select(s.allocations).where(s.allocations.c.budget_month_id==budget['id'])).mappings()}
            for a in new_allocations:
                current=old.pop(a['category_id'],None)
                self.save(c,s.allocations,dict(id=str(uuid5(NAMESPACE_URL,budget['id']+'/'+a['category_id'])),
                    budget_month_id=budget['id'],**a,percentage_basis_points=(
                        (a['amount_minor'] * 10000 + data['expected_income_minor'] // 2) // data['expected_income_minor']
                        if data['expected_income_minor'] else None),deleted=False),current)
            for current in old.values():
                self.save(c,s.allocations,{'deleted':True},current)
        self.save(c, s.category_months, {}, monthly)
        return budget

    def purchase_values(self,c,op,current=None):
        data=dict(op['data']); data.pop('expected_revision',None)
        month = data['transaction_date'][:7]
        cat = self.require_month_category(c, data['category_id'], month, current)
        from .category_months import OTHER_CATEGORY_ID
        explanation = data.get('category_explanation', '').strip()
        if cat['id'] == OTHER_CATEGORY_ID and not explanation:
            raise DomainError('category_explanation', 'Please explain is required for Other')
        if cat['id'] != OTHER_CATEGORY_ID and explanation:
            raise DomainError('category_explanation', 'An explanation is only used with Other')
        data['category_explanation'] = explanation
        self.establish_month(c, month)
        request_revision=data.pop('request_revision',None)
        if data['request_id'] and not current:
            self.link_request(c, data['request_id'], request_revision, op)
        elif current and data['request_id'] != current['request_id']:
            raise DomainError('request','A purchase approval link cannot be reassigned')
        return data

    def do_purchase_create(self,c,op):
        data=self.purchase_values(c,op)
        result=self.save(c,s.purchases,dict(id=op['entity_id'],purchaser_id=op['actor_id'],**data,bill_id=None,bill_due=None))
        self.notify(c,op,'purchase.created','purchases',result['id'])
        self.spending_alerts(c,result['transaction_date'][:7],op,result['category_id'])
        return result

    def do_purchase_update(self,c,op):
        current=get(c,s.purchases,op['entity_id']); expect(current,op['data']['expected_revision'])
        data=self.purchase_values(c,op,current)
        result=self.save(c,s.purchases,data,current)
        self.spending_alerts(c,result['transaction_date'][:7],op,result['category_id'])
        return result

    def do_purchase_delete(self,c,op):
        current=get(c,s.purchases,op['entity_id']); expect(current,op['data']['expected_revision'])
        return self.save(c,s.purchases,{'deleted':True},current)

    def spending_alerts(self,c,month,op,category_id):
        category=get(c,s.categories,category_id)
        target=category['parent_id'] or category['id']
        for row in self.summary(c,month)['categories']:
            if row['category_id']!=target or row['kind']=='savings' or row['actual_minor']<=0:
                continue
            for suffix,hit in [('reached',row['actual_minor']>=row['allocated_minor']),('exceeded',row['actual_minor']>row['allocated_minor'])]:
                if hit:
                    self.notify(c,op,'budget.'+suffix,'categories',row['category_id'],
                                event_key=f"budget:{month}:{row['category_id']}:{suffix}",
                                recipients=[row['owner_id']] if row['owner_id'] else None)
