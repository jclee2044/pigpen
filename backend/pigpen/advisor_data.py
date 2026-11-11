"""Read-only views of confirmed household finances used by the budget assistant."""
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select

from . import schema as s
from .domain import month_bounds, previous_month
from .budget import BudgetServices


def today():
    return datetime.now(ZoneInfo('America/New_York')).date().isoformat()


def revision(conn):
    resources = ('purchases', 'categories', 'allocations', 'budget-months', 'income', 'savings')
    return conn.scalar(select(func.max(s.changes.c.cursor)).where(s.changes.c.resource.in_(resources))) or 0


def comparison(conn, month):
    service = BudgetServices()
    current = service.summary(conn, month)
    prior_month = previous_month(month)
    prior = service.summary(conn, prior_month) if month > '1900-01' else None
    prior_rows = {r['category_id']: r for r in prior['categories']} if prior else {}
    categories = []
    for row in current['categories']:
        old = prior_rows.get(row['category_id'], {}).get('actual_minor', 0)
        if any((row['actual_minor'], row['allocated_minor'], old)):
            categories.append({
                'name': row['name'], 'kind': row['kind'], 'allocated_minor': row['allocated_minor'],
                'actual_minor': row['actual_minor'], 'remaining_minor': row['remaining_minor'],
                'change_from_prior_month_minor': row['actual_minor'] - old,
            })
    return {
        'month': month, 'today': today(), 'comparison_full_month': prior_month if prior else None,
        **{k: v for k, v in current.items() if k.endswith('_minor')},
        'categories': sorted(categories, key=lambda row: -row['actual_minor']),
    }


def highlights(data):
    def dollars(cents):
        return f'${cents // 100:,}.{cents % 100:02d}'
    expenses = [row for row in data['categories'] if row['kind'] != 'savings']
    over = min(expenses, key=lambda row: row['remaining_minor'], default=None)
    lines = []
    if over and over['remaining_minor'] < 0:
        lines.append(f"{over['name']} is {dollars(-over['remaining_minor'])} over its monthly allocation.")
    if expenses and expenses[0]['actual_minor'] > 0:
        top = expenses[0]
        lines.append(f"{top['name']} has the most confirmed spending at {dollars(top['actual_minor'])}.")
    if data['planned_unallocated_minor'] > 0:
        lines.append(f"{dollars(data['planned_unallocated_minor'])} of expected income is available to allocate.")
    return lines or ['There is no confirmed spending to highlight for this month.']


def purchase_search(conn, month, term):
    start, end = month_bounds(month)
    p, c = s.purchases.c, s.categories.c
    parent = s.categories.alias('parent')
    query = select(p.id, p.item, p.merchant, p.transaction_date, p.amount_minor, c.name.label('category')).select_from(
        s.purchases.join(s.categories, p.category_id == c.id).outerjoin(parent, c.parent_id == parent.c.id)
    ).where(p.deleted.is_(False), p.transaction_date.between(start, end))
    if term:
        query = query.where(or_(*(col.icontains(term, autoescape=True) for col in
                                  (p.item, p.merchant, c.name, parent.c.name))))
    matches = query.subquery()
    count, total = conn.execute(select(func.count(), func.sum(matches.c.amount_minor))).one()
    rows = conn.execute(query.order_by(p.amount_minor.desc(), p.id).limit(8)).mappings()
    return {'month': month, 'match_count': count, 'total_minor': total or 0,
            'largest_matches': [dict(row) for row in rows]}


def purchase_detail(conn, purchase_id):
    p, c, u = s.purchases.c, s.categories.c, s.users.c
    query = select(p.id, p.item, p.merchant, p.transaction_date, p.amount_minor,
                   c.name.label('category'), u.name.label('purchaser')).select_from(
        s.purchases.join(s.categories, p.category_id == c.id).join(s.users, p.purchaser_id == u.id)
    ).where(p.id == str(purchase_id), p.deleted.is_(False))
    row = conn.execute(query).mappings().first()
    return {'purchase': dict(row)} if row else {'error': 'Purchase unavailable.'}
