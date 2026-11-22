"""Monthly category membership and frozen inherited plans; no HTTP dependencies."""
from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select
from . import schema as s
from .domain import month_bounds
from .records import get
from .errors import DomainError

OTHER_CATEGORY_ID = '00000000-0000-5000-8000-000000000001'


def calendar_months(start, end):
    while start <= end:
        yield start
        year, month = map(int, start.split('-'))
        if year == 9999 and month == 12:
            break
        start = f'{year + (month == 12):04d}-{month % 12 + 1:02d}'


def resolve_month(month, categories, months, budgets, allocations):
    """One resolver for membership and expected money; reads never establish months."""
    exact = next((x for x in months if not x['deleted'] and x['month'] == month), None)
    source = exact or max((x for x in months if not x['deleted'] and x['month'] < month),
                          key=lambda x: x['month'], default=None)
    ids = list(source['category_ids']) if source else [x['id'] for x in categories if x['active'] and not x['deleted']]
    if OTHER_CATEGORY_ID not in ids and any(x['id'] == OTHER_CATEGORY_ID for x in categories):
        ids.append(OTHER_CATEGORY_ID)
    budget = next((x for x in budgets if not x['deleted'] and x['month'] == (source['month'] if source else month)), None)
    if budget:
        amounts = [dict(category_id=x['category_id'], amount_minor=x['amount_minor']) for x in allocations
                   if not x['deleted'] and x['budget_month_id'] == budget['id']]
        income = budget['expected_income_minor']
    elif source:
        amounts, income = source['inherited_allocations'], source['inherited_income_minor']
    else:
        amounts, income = [], 0
    if not exact:
        amounts = [a for a in amounts if a['category_id'] in ids]
    return ids, amounts, income


class CategoryMonthServices:
    def current_month(self, c):
        return datetime.now(ZoneInfo(self.household(c)['timezone'])).strftime('%Y-%m')

    def month_state(self, c, month):
        month_bounds(month)
        return c.execute(select(s.category_months).where(s.category_months.c.month == month)).mappings().first()

    def resolved_month(self, c, month):
        month_bounds(month)
        def rows(table):
            return list(c.execute(select(table)).mappings())
        return resolve_month(month, rows(s.categories), rows(s.category_months), rows(s.budget_months), rows(s.allocations))

    def establish_month(self, c, month):
        existing = self.month_state(c, month)
        if existing:
            return dict(existing)
        ids, amounts, income = self.resolved_month(c, month)
        return self.save(c, s.category_months, dict(
            id=str(uuid5(NAMESPACE_URL, self.household(c)['id'] + '/categories/' + month)),
            month=month, category_ids=ids, inherited_allocations=amounts, inherited_income_minor=income))

    def freeze_elapsed(self, c):
        earliest = c.execute(select(s.category_months.c.month).order_by(s.category_months.c.month).limit(1)).scalar()
        if earliest:
            for month in calendar_months(earliest, self.current_month(c)):
                self.establish_month(c, month)

    def check_month_revision(self, c, month, revision):
        current = self.month_state(c, month)
        if (current['revision'] if current else 0) != revision:
            raise DomainError('revision_conflict', 'This month changed. Load the latest records and try again.', 409, dict(current) if current else None)

    def require_month_category(self, c, category_id, month, current=None):
        category = get(c, s.categories, category_id)
        if category['kind'] == 'savings':
            raise DomainError('category', 'Record savings as savings movements, not purchases')
        # Editing a historical purchase does not require re-adding its category.
        unchanged = current and current['category_id'] == category_id and current['transaction_date'][:7] == month
        if category['owner_id'] and not unchanged:
            get(c, s.users, category['owner_id'], active=True)
        ids, _, _ = self.resolved_month(c, month)
        if not unchanged and (category_id not in ids or (category['parent_id'] and category['parent_id'] not in ids)):
            raise DomainError('category_unavailable', 'This category is not available for the purchase month. Add it again or choose another category.',
                              409, {'month': month, 'category_id': category_id})
        return category

    def do_category_include(self, c, op):
        data = op['data']; month = data['month']
        self.check_month_revision(c, month, data['expected_revision'])
        category = get(c, s.categories, op['entity_id'])
        if category['owner_id'] and category['owner_id'] != op['actor_id']:
            raise DomainError('actor', 'Only the owner can change a Personal category', 403)
        if category['id'] == OTHER_CATEGORY_ID or (category['kind'] == 'personal' and not category['parent_id']):
            raise DomainError('category', 'This category is always available')
        if category['owner_id']:
            get(c, s.users, category['owner_id'], active=True)
        self.freeze_elapsed(c)
        current = self.establish_month(c, month)
        ids = list(current['category_ids'])
        if data['included']:
            # Re-adding a child explicitly includes its parent, but not siblings.
            for identifier in [category['parent_id'], category['id']]:
                if identifier and identifier not in ids:
                    ids.append(identifier)
        else:
            children = set(c.execute(select(s.categories.c.id).where(s.categories.c.parent_id == category['id'])).scalars())
            ids = [identifier for identifier in ids if identifier != category['id'] and identifier not in children]
        return self.save(c, s.category_months, {'category_ids': ids}, current)
