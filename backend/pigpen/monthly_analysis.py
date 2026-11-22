"""Framework-free monthly review calculations; model output never supplies chart values."""
from .domain import previous_month


OTHER_ID = '00000000-0000-5000-8000-000000000001'


def prior_months(month, count=6):
    result = []
    for _ in range(count):
        if month == '1900-01':
            break
        month = previous_month(month)
        result.append(month)
    return list(reversed(result))


def snapshot(month, summaries, purchases, categories, observed):
    """Input records are confirmed; no SQL, web or model dependency here."""
    current = summaries[month]
    expense_rows = [r for r in current['categories'] if r['kind'] != 'savings']
    saved = []
    category_map = {c['id']: c for c in categories}
    for purchase in purchases:
        if purchase['deleted'] or purchase['transaction_date'][:7] != month:
            continue
        c = category_map[purchase['category_id']]
        saved.append({k: purchase.get(k, '') for k in
                      ('id', 'item', 'merchant', 'transaction_date', 'amount_minor', 'category_id', 'category_explanation')}
                     | {'parent_category_id': c.get('parent_id') or c['id'],
                        'other': c['id'] == OTHER_ID or c['name'].casefold() == 'other'})
    # Prioritize Other evidence, then largest purchases; all totals still cover all records.
    saved.sort(key=lambda p: (not p['other'], -p['amount_minor'], p['id']))
    included = saved[:300]
    comparisons = [m for m in prior_months(month) if m in observed]
    rows = []
    for row in expense_rows:
        history = []
        for m in comparisons:
            old = next((x for x in summaries[m]['categories'] if x['category_id'] == row['category_id']), None)
            if old is not None:
                history.append({'month': m, 'allocated_minor': old['allocated_minor'], 'spent_minor': old['actual_minor']})
        rows.append({'id': row['category_id'], 'name': row['name'],
                     'allocated_minor': row['allocated_minor'], 'spent_minor': row['actual_minor'], 'history': history})
    allocated = sum(r['allocated_minor'] for r in expense_rows)
    return {'month': month, 'totals': {
        'budgeted_minor': allocated, 'spent_minor': current['spent_minor'],
        'remaining_minor': allocated - current['spent_minor'],
        'savings_allocated_minor': sum(r['allocated_minor'] for r in current['categories'] if r['kind'] == 'savings'),
        'savings_actual_minor': current['savings_contribution_minor'], 'income_minor': current['actual_income_minor'],
    }, 'categories': rows, 'purchases': included,
        'coverage': {'comparison_months': comparisons, 'purchase_count': len(saved), 'included_purchase_count': len(included)}}


def materialize(evidence, plan):
    """Validate identifiers/meaning, and build every visualization from exact source cents."""
    categories = {c['id']: c for c in evidence['categories']}
    purchases = {p['id']: p for p in evidence['purchases']}
    findings = []
    seen = set()
    for proposed in plan['findings']:
        kind, identifier = proposed['kind'], proposed['category_id']
        ids = proposed['purchase_ids']
        if len(ids) != len(set(ids)) or not set(ids) <= purchases.keys():
            raise ValueError('Invalid purchase evidence')
        if identifier is not None and identifier not in categories:
            raise ValueError('Invalid category evidence')
        category = categories.get(identifier)
        selected = [purchases[p] for p in ids]
        if category and any(p['parent_category_id'] != identifier for p in selected):
            raise ValueError('Purchase/category mismatch')
        chart = []
        if kind in {'trend', 'budget'}:
            if not category:
                raise ValueError('Category required')
            if kind == 'trend':
                if len(category['history']) < 2:
                    raise ValueError('Insufficient trend history')
                chart = [{'label': h['month'], 'amount_minor': h['spent_minor']} for h in category['history']]
                chart.append({'label': evidence['month'], 'amount_minor': category['spent_minor']})
            else:
                chart = [{'label': 'Budgeted', 'amount_minor': category['allocated_minor']},
                         {'label': 'Spent', 'amount_minor': category['spent_minor']}]
            if not selected:
                selected = sorted((p for p in purchases.values() if p['parent_category_id'] == identifier),
                                  key=lambda p: -p['amount_minor'])[:8]
        elif kind == 'category_group':
            if len(selected) < 2 or any(not p['other'] for p in selected) or not proposed['suggested_category']:
                raise ValueError('New category needs multiple Other purchases')
            total = sum(p['amount_minor'] for p in selected)
            # Use the full category totals, not the bounded model evidence, for the remainder.
            other_ids = {p['parent_category_id'] for p in evidence['purchases'] if p['other']}
            other_total = sum(c['spent_minor'] for c in categories.values() if c['id'] in other_ids)
            chart = [{'label': proposed['suggested_category'], 'amount_minor': total},
                     {'label': 'Remaining Other', 'amount_minor': other_total - total}]
        elif kind == 'observation':
            if not selected and not category:
                raise ValueError('Observation needs evidence')
            chart = [{'label': p['item'], 'amount_minor': p['amount_minor']} for p in selected[:8]]
        else:
            raise ValueError('Unknown finding type')
        signature = (kind, identifier, tuple(sorted(ids)))
        if signature in seen:
            raise ValueError('Duplicate finding')
        seen.add(signature)
        findings.append({'id': f'finding-{len(findings) + 1}', 'kind': kind, 'title': proposed['title'],
                         'explanation': proposed['explanation'], 'category_id': identifier,
                         'suggested_category': proposed['suggested_category'], 'chart': chart,
                         'purchases': [{k: v for k, v in p.items() if k not in {'other', 'parent_category_id'}} for p in selected]})
    return {'summary': plan['summary'], 'totals': evidence['totals'], 'coverage': evidence['coverage'], 'findings': findings}
