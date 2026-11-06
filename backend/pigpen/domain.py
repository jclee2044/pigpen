"""Framework-free rules. No FastAPI, ORM or storage imports."""
from calendar import monthrange
from datetime import date
from .errors import DomainError

MAX_MINOR = 9_000_000_000_000


def month_bounds(month):
    try:
        if len(month) != 7:
            raise ValueError()
        year, n = map(int, month.split('-'))
        first = date(year, n, 1)
        if first.strftime('%Y-%m') != month or year < 1900 or year > 9998:
            raise ValueError()
        return first.isoformat(), date(year, n, monthrange(year, n)[1]).isoformat()
    except (ValueError, TypeError):
        raise DomainError('month', 'Use a calendar month in YYYY-MM format (1900–9998)')


def previous_month(month):
    month_bounds(month)
    year, n = map(int, month.split('-'))
    return f'{year-1:04d}-12' if n == 1 else f'{year:04d}-{n-1:02d}'


def due_date(month, day):
    first, _ = month_bounds(month)
    year, n = map(int, month.split('-'))
    return date(year, n, min(day, monthrange(year, n)[1])).isoformat()


def all_approved(requester_id, active_ids, votes, request_revision):
    eligible = set(active_ids) - {requester_id}
    approvals = {v['reviewer_id'] for v in votes if v['approved'] and v['request_revision'] == request_revision}
    return bool(eligible) and eligible <= approvals


def budget_summary(month, categories, allocations, purchases, income=(), savings=(), expected_income=0):
    """Roll up Personal children exactly once; planned money is not actual income."""
    month_bounds(month)
    allocation_map = {a['category_id']: a['amount_minor'] for a in allocations if not a['deleted']}
    category_map = {c['id']: c for c in categories}
    spent = {}
    for purchase in purchases:
        if purchase['deleted'] or purchase['transaction_date'][:7] != month:
            continue
        category = category_map[purchase['category_id']]
        target = category['parent_id'] or category['id']
        spent[target] = spent.get(target, 0) + purchase['amount_minor']
    net_contributions = sum((1 if x['kind']=='contribution' else -1) * x['amount_minor'] for x in savings
                            if not x['deleted'] and x['kind']!='opening' and x['transaction_date'][:7] == month)
    rows=[]
    for category in categories:
        if category['parent_id'] or category['deleted']:
            continue
        amount = allocation_map.get(category['id'], 0)
        actual = net_contributions if category['kind']=='savings' else spent.get(category['id'], 0)
        rows.append({'category_id': category['id'], 'name': category['name'], 'kind': category['kind'],
                     'owner_id': category['owner_id'], 'active': category['active'],
                     'allocated_minor': amount, 'actual_minor': actual, 'remaining_minor': amount-actual})
    total_allocated = sum(x['allocated_minor'] for x in rows)
    return {'month': month, 'categories': rows, 'allocated_minor': total_allocated,
            'spent_minor': sum(spent.values()), 'expected_income_minor': expected_income,
            'actual_income_minor': sum(x['amount_minor'] for x in income if not x['deleted'] and x['transaction_date'][:7]==month),
            'planned_unallocated_minor': expected_income-total_allocated,
            'savings_contribution_minor': net_contributions,
            'savings_balance_minor': sum(((-1 if x['kind']=='withdrawal' else 1)*x['amount_minor']) for x in savings
                                        if not x['deleted'] and x['transaction_date'] <= month_bounds(month)[1])}
