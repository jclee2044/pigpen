from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from uuid import uuid4
from sqlalchemy import select, update, MetaData
from conftest import operation, submit
from pigpen import schema as s
from pigpen.category_months import OTHER_CATEGORY_ID
from pigpen.database import Database, migrate
from pigpen.budget import BudgetServices


def records(client):
    return client.get('/api/v1/sync/snapshot').json()['records']


def category(client, name='Food'):
    return next(x for x in records(client)['categories'] if x['name'] == name)


def include(client, actor, identifier, month, included):
    state = next((x for x in records(client)['category-months'] if x['month'] == month), None)
    return submit(client, 'category.include', dict(month=month, included=included,
                  expected_revision=state['revision'] if state else 0), actor, identifier)


def purchase(client, actor, identifier, month, **extra):
    return submit(client, 'purchase.create', dict(item='Synthetic', amount_minor=123,
                  category_id=identifier, transaction_date=month+'-02', **extra), actor)


def summary(client, month):
    return client.get('/api/v1/budget-months/'+month).json()


def test_month_removal_preserves_money_readd_identity_and_saved_neighbors(client, users):
    actor = users[0]['id']; food = category(client)['id']
    plan = submit(client, 'budget.set', dict(month='2040-01', expected_income_minor=10000,
                  allocations=[dict(category_id=food, amount_minor=5000)]), actor)
    purchase(client, actor, food, '2040-01')
    purchase(client, actor, food, '2040-03')  # Establish March before changing February.
    before = {m: summary(client, m) for m in ['2040-01', '2040-03']}
    include(client, actor, food, '2040-02', False)
    feb = summary(client, '2040-02')
    assert feb['allocated_minor'] == 5000
    assert next(x for x in feb['categories'] if x['category_id'] == food)['active'] is False
    for month in before:
        assert summary(client, month) == before[month]
    assert summary(client, '2040-04')['allocated_minor'] == 5000  # March is independent.
    include(client, actor, food, '2040-03', False)
    assert summary(client, '2040-04')['allocated_minor'] == 0
    include(client, actor, food, '2040-02', True)
    purchase(client, actor, food, '2040-02')
    assert summary(client, '2040-02')['spent_minor'] == 123
    assert len([c for c in records(client)['categories'] if c['id'] == food]) == 1
    assert summary(client, '2040-01')['budget']['id'] == plan['id']


def test_stale_month_edits_conflict_and_retry_is_exactly_once(client, users):
    actor = users[0]['id']; food = category(client)['id']
    op = operation('category.include', dict(month='2041-01', included=False, expected_revision=0), actor, food)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post('/api/v1/operations', json=op), range(2)))
    assert [r.status_code for r in results] == [200, 200]
    assert results[0].json() == results[1].json()
    stale = deepcopy(op); stale['operation_id'] = str(uuid4()); stale['data']['included'] = True
    assert client.post('/api/v1/operations', json=stale).status_code == 409
    assert food not in next(x for x in records(client)['category-months'] if x['month']=='2041-01')['category_ids']


def test_backdating_existing_edits_date_changes_and_offline_recovery(client, users):
    actor = users[0]['id']; food = category(client)['id']
    existing = purchase(client, actor, food, '2042-01')
    queued = operation('purchase.create', dict(item='Queued', amount_minor=321, category_id=food,
                       transaction_date='2042-02-02'), actor)
    include(client, actor, food, '2042-02', False)
    outcome = client.post('/api/v1/sync/push', json={'operations':[queued]}).json()['outcomes'][0]
    assert not outcome['ok'] and outcome['error']['code'] == 'category_unavailable'
    include(client, actor, food, '2042-01', False)
    edit = dict(item='Corrected', amount_minor=500, category_id=food, transaction_date='2042-01-03', expected_revision=1)
    submit(client, 'purchase.update', edit, actor, existing['id'])
    edit.update(transaction_date='2042-02-03', expected_revision=2)
    assert client.post('/api/v1/operations', json=operation('purchase.update', edit, actor, existing['id'])).status_code == 409
    include(client, actor, food, '2042-02', True)
    for _ in range(2):
        assert client.post('/api/v1/sync/push', json={'operations':[queued]}).json()['outcomes'][0]['ok']
    assert len([p for p in records(client)['purchases'] if p['id']==queued['entity_id']]) == 1


def test_parent_child_removal_and_personal_protection(client, users):
    actor = users[0]['id']; parent = category(client, 'Subscriptions')['id']
    child = submit(client, 'category.create', dict(name='Streaming', parent_id=parent, month='2043-01'), actor)
    purchase(client, actor, child['id'], '2043-01')
    include(client, actor, parent, '2043-01', False)
    state = next(x for x in records(client)['category-months'] if x['month']=='2043-01')
    assert parent not in state['category_ids'] and child['id'] not in state['category_ids']
    include(client, actor, child['id'], '2043-01', True)
    state = next(x for x in records(client)['category-months'] if x['month']=='2043-01')
    assert parent in state['category_ids'] and child['id'] in state['category_ids']
    assert summary(client, '2043-01')['spent_minor'] == 123
    personal = next(c for c in records(client)['categories'] if c['owner_id']==actor)
    assert client.post('/api/v1/operations', json=operation('category.include', dict(month='2043-01', included=False, expected_revision=state['revision']), actor, personal['id'])).status_code == 422


def test_other_requires_separate_explanation_and_legacy_replay_hash(client, users, settings):
    actor = users[0]['id']
    for explanation in ['', '   ']:
        response = client.post('/api/v1/operations', json=operation('purchase.create', dict(item='Other purchase', amount_minor=50, category_id=OTHER_CATEGORY_ID, transaction_date='2044-01-02', category_explanation=explanation), actor))
        assert response.status_code == 422
    p = purchase(client, actor, OTHER_CATEGORY_ID, '2044-01', category_explanation='One-off permit', description='Original notes')
    assert p['category_explanation']=='One-off permit' and p['description']=='Original notes'
    assert summary(client, '2044-01')['spent_minor']==123
    from pigpen.advisor_data import purchase_search
    with Database(settings).transaction() as c:
        assert purchase_search(c, '2044-01', 'permit')['match_count']==1
    op = operation('purchase.create', dict(item='Legacy', amount_minor=20, category_id=category(client)['id'], transaction_date='2044-01-03'), actor)
    response = client.post('/api/v1/operations', json=op)
    assert response.status_code == 200
    from pydantic import TypeAdapter
    from pigpen.contracts import Operation
    legacy = TypeAdapter(Operation).validate_python(op).model_dump(mode='json')
    legacy['data'].pop('category_explanation')
    digest = sha256(json.dumps(legacy, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    with Database(settings).transaction(write=True) as c:
        c.execute(update(s.operations).where(s.operations.c.id==op['operation_id']).values(payload_hash=digest))
    assert client.post('/api/v1/operations', json=op).json()==response.json()


def test_old_global_remove_is_blocked_and_bill_payment_checks_month(client, users):
    actor = users[0]['id']; food = category(client)
    legacy = operation('category.update', dict(name=food['name'], active=False, expected_revision=food['revision']), actor, food['id'])
    assert client.post('/api/v1/operations', json=legacy).json()['error']['code']=='update_required'
    bill = submit(client, 'bill.create', dict(name='Food box', amount_minor=100, category_id=food['id'], due_day=5, start_date='2045-01-05'), actor)
    include(client, actor, food['id'], '2045-02', False)
    payment = operation('bill.pay', dict(bill_id=bill['id'], due_date='2045-02-05', transaction_date='2045-02-05'), actor)
    assert client.post('/api/v1/operations', json=payment).json()['error']['code']=='category_unavailable'
    assert not records(client)['bill-occurrences']
    include(client, actor, food['id'], '2045-02', True)
    assert client.post('/api/v1/operations', json=payment).status_code==200


def test_migration_preserves_original_financial_records_and_every_month_total(settings):
    migrate(settings, '0014')
    db = Database(settings)
    with db.transaction(write=True) as c:
        tables = MetaData(); tables.reflect(c)
        h, u, food, retired = [str(uuid4()) for _ in range(4)]
        def add(table, **values):
            data = dict(revision=1, deleted=False, created_at='2025-01-01', updated_at='2025-01-01', **values)
            if table!='households': data['household_id']=h
            c.execute(tables.tables[table].insert().values(**data))
        add('households', id=h, singleton=1, name='Synthetic', currency='USD', timezone='America/New_York', approval_policy='all', category_order=[], wishlist_order=[])
        add('users', id=u, name='Owner', name_key='owner', avatar={}, active=True, wishlist_order=[])
        for identifier, name, active in [(food,'Food',True),(retired,'Retired',False)]:
            add('categories', id=identifier, name=name, kind='expense', owner_id=None, parent_id=None, active=active, allows_subcategories=False)
        b = str(uuid4())
        add('budget_months', id=b, month='2025-01', expected_income_minor=10000)
        for identifier, amount in [(food,2000),(retired,3000)]:
            add('allocations', id=str(uuid4()), budget_month_id=b, category_id=identifier, amount_minor=amount, percentage_basis_points=amount)
            add('purchases', id=str(uuid4()), purchaser_id=u, category_id=identifier, item='Before migration', amount_minor=100, transaction_date='2025-01-02', merchant=None, description='', request_id=None, bill_id=None, bill_due=None)
        before = {name:[dict(r) for r in c.execute(select(tables.tables[name])).mappings()] for name in ['purchases','allocations','budget_months','categories']}
    migrate(settings)
    with db.transaction() as c:
        assert not c.exec_driver_sql('PRAGMA foreign_key_check').all()
        for name in before:
            table = s.metadata.tables[name]
            after = {r['id']:dict(r) for r in c.execute(select(table)).mappings()}
            for old in before[name]:
                assert {k:after[old['id']][k] for k in old} == old
        service = BudgetServices()
        assert service.summary(c,'2025-01')['allocated_minor']==5000
        assert service.summary(c,'2025-01')['spent_minor']==200
        for month in ['2025-02','2025-12','2026-01']:
            assert service.summary(c,month)['allocated_minor']==2000
            assert service.summary(c,month)['spent_minor']==0
            assert service.summary(c,month)['expected_income_minor']==10000
        assert service.summary(c,'2024-12')['allocated_minor']==0


def test_elapsed_months_freeze_before_historical_correction(client, users, monkeypatch):
    from pigpen.category_months import CategoryMonthServices
    monkeypatch.setattr(CategoryMonthServices, 'current_month', lambda self, c: '2047-03')
    actor = users[0]['id']; food = category(client)['id']
    jan = submit(client, 'budget.set', dict(month='2047-01', expected_income_minor=10000,
                 allocations=[dict(category_id=food, amount_minor=3000)]), actor)
    submit(client, 'budget.set', dict(month='2047-01', expected_revision=jan['revision'], expected_income_minor=20000,
           allocations=[dict(category_id=food, amount_minor=7000)]), actor, jan['id'])
    assert summary(client,'2047-01')['allocated_minor']==7000
    for month in ['2047-02','2047-03']:
        assert summary(client,month)['allocated_minor']==3000
        assert summary(client,month)['expected_income_minor']==10000
    include(client, actor, food, '2047-03', False)
    assert summary(client,'2047-04')['allocated_minor']==0
    assert summary(client,'2047-02')['allocated_minor']==3000
