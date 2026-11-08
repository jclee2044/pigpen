from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from uuid import uuid4
import pytest
from conftest import operation, submit


def food(client):
    return next(x for x in client.get('/api/v1/categories').json()['items'] if x['name']=='Food')


def test_money_rollup_month_isolation_and_copy(client, users):
    actor=users[0]['id']
    parent=next(x for x in client.get('/api/v1/categories').json()['items'] if x['owner_id']==actor)
    child=submit(client,'category.create',dict(name='Books',kind='personal',owner_id=actor,parent_id=parent['id']),actor)
    f=food(client)
    submit(client,'budget.set',dict(month='2026-11',expected_income_minor=100000,
        allocations=[dict(category_id=parent['id'],amount_minor=20000),dict(category_id=f['id'],amount_minor=40000)]),actor)
    for category, amount, day in [(parent['id'],3000,'2026-11-01'),(child['id'],2000,'2026-11-30'),(f['id'],99,'2026-12-01')]:
        submit(client,'purchase.create',dict(item='Synthetic purchase',amount_minor=amount,category_id=category,transaction_date=day),actor)
    nov=client.get('/api/v1/budget-months/2026-11').json()
    assert nov['spent_minor']==5000
    personal=next(x for x in nov['categories'] if x['category_id']==parent['id'])
    assert personal['remaining_minor']==15000
    assert nov['planned_unallocated_minor']==40000
    submit(client,'budget.set',dict(month='2026-12'),actor)
    dec=client.get('/api/v1/budget-months/2026-12').json()
    assert dec['allocated_minor']==60000 and dec['spent_minor']==99
    assert client.get('/api/v1/budget-months/2026-13').status_code==422


@pytest.mark.parametrize('amount',[1.5,True,-10,0,9000000000001])
def test_invalid_purchase_amount(client,users,amount):
    op=operation('purchase.create',dict(item='Item',amount_minor=amount,category_id=food(client)['id'],transaction_date='2026-11-06'),users[0]['id'])
    response=client.post('/api/v1/operations',json=op)
    assert response.status_code==422
    assert 'input' not in str(response.json())
    assert client.get('/api/v1/purchases').json()['items']==[]


def test_purchase_replay_concurrency_and_tombstone(client, users):
    op=operation('purchase.create',dict(item='Item',amount_minor=123,category_id=food(client)['id'],transaction_date='2026-11-06'),users[0]['id'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:client.post('/api/v1/operations',json=op), range(2)))
    assert [r.status_code for r in results]==[200,200]
    assert results[0].json()==results[1].json()
    submit(client,'purchase.delete',dict(expected_revision=1),users[0]['id'],op['entity_id'])
    assert client.post('/api/v1/operations',json=op).json()==results[0].json()
    assert client.get('/api/v1/purchases').json()['items']==[]


def test_purchase_optimistic_revision(client,users):
    actor=users[0]['id']
    payload=dict(item='Item',amount_minor=10,category_id=food(client)['id'],transaction_date='2026-11-06')
    purchase=submit(client,'purchase.create',payload,actor)
    submit(client,'purchase.update',dict(**payload,expected_revision=1),actor,purchase['id'])
    response=client.post('/api/v1/operations',json=operation('purchase.update',dict(**payload,expected_revision=1),actor,purchase['id']))
    assert response.status_code==409
    assert response.json()['error']['details']['revision']==2


def test_edit_plan_retains_archived_allocation_without_allowing_new_inactive_money(client,users):
    actor=users[0]['id']
    category=food(client)
    budget=submit(client,'budget.set',dict(month='2026-11',allocations=[dict(category_id=category['id'],amount_minor=5000)]),actor)
    submit(client,'category.update',dict(name=category['name'],active=False,expected_revision=category['revision']),actor,category['id'])
    data=dict(month='2026-11',expected_revision=budget['revision'],expected_income_minor=100000,
              allocations=[dict(category_id=category['id'],amount_minor=5000)])
    revised=submit(client,'budget.set',data,actor,budget['id'])
    assert client.get('/api/v1/budget-months/2026-11').json()['allocated_minor']==5000
    data['expected_revision']=revised['revision']
    data['allocations'][0]['amount_minor']=6000
    assert client.post('/api/v1/operations',json=operation('budget.set',data,actor,budget['id'])).status_code==422
    assert client.post('/api/v1/operations',json=operation('budget.set',dict(month='2026-12',allocations=data['allocations']),actor)).status_code==422


def test_unsaved_month_inherits_latest_plan_without_copy_or_writes(client, users):
    actor=users[0]['id']; category=food(client)
    plan=submit(client,'budget.set',dict(month='2026-01',expected_income_minor=100000,
        allocations=[dict(category_id=category['id'],amount_minor=20000)]),actor)
    submit(client,'purchase.create',dict(item='January food',amount_minor=1000,
        category_id=category['id'],transaction_date='2026-01-02'),actor)
    later=client.get('/api/v1/budget-months/2026-04').json()
    assert later['budget'] is None
    assert later['allocated_minor']==20000 and later['spent_minor']==0
    assert later['planned_unallocated_minor']==80000
    assert client.get('/api/v1/budget-months/2025-12').json()['allocated_minor']==0
    override=submit(client,'budget.set',dict(month='2026-04',expected_income_minor=120000,allocations=[]),actor)
    assert client.get('/api/v1/budget-months/2026-05').json()['allocated_minor']==0
    assert client.get('/api/v1/budget-months/2026-05').json()['planned_unallocated_minor']==120000
    assert client.get('/api/v1/budget-months/2026-03').json()['allocated_minor']==20000
    assert client.get('/api/v1/budget-months/2026-01').json()['budget']['id']==plan['id']
    assert client.get('/api/v1/budget-months/2026-04').json()['budget']['id']==override['id']


def test_inherited_allocations_exclude_archived_categories(client, users):
    actor=users[0]['id']; category=food(client)
    submit(client,'budget.set',dict(month='2026-01',allocations=[dict(category_id=category['id'],amount_minor=20000)]),actor)
    submit(client,'category.update',dict(name=category['name'],active=False,expected_revision=category['revision']),actor,category['id'])
    assert client.get('/api/v1/budget-months/2026-03').json()['allocated_minor']==0
    assert client.get('/api/v1/budget-months/2026-01').json()['allocated_minor']==20000
