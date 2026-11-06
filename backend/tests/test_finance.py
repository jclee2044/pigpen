from conftest import operation, submit


def test_income_savings_are_not_double_counted(client,users):
    actor=users[0]['id']
    submit(client,'budget.set',dict(month='2026-11',expected_income_minor=100000),actor)
    submit(client,'income.create',dict(description='Salary',amount_minor=50000,transaction_date='2026-11-01'),actor)
    for kind,amount,day in [('opening',100000,'2026-10-01'),('contribution',5000,'2026-11-03'),('withdrawal',1000,'2026-11-04')]:
        submit(client,'savings.create',dict(kind=kind,amount_minor=amount,transaction_date=day),actor)
    summary=client.get('/api/v1/budget-months/2026-11').json()
    assert summary['actual_income_minor']==50000
    assert summary['expected_income_minor']==100000
    assert summary['spent_minor']==0
    assert summary['savings_contribution_minor']==4000
    assert summary['savings_balance_minor']==104000
    duplicate=operation('savings.create',dict(kind='opening',amount_minor=99,transaction_date='2026-11-01'),actor)
    assert client.post('/api/v1/operations',json=duplicate).status_code==409


def test_month_end_bill_paid_once(client,users):
    actor=users[0]['id']
    category=next(c for c in client.get('/api/v1/categories').json()['items'] if c['name']=='Housing')
    bill=submit(client,'bill.create',dict(name='Rent',amount_minor=10000,category_id=category['id'],due_day=31,start_date='2026-01-01'),actor)
    due=client.get('/api/v1/bill-occurrences?month=2026-02').json()['items'][0]
    assert due['due_date']=='2026-02-28' and due['purchase_id'] is None
    assert client.get('/api/v1/budget-months/2026-02').json()['spent_minor']==0
    op=operation('bill.pay',dict(bill_id=bill['id'],due_date='2026-02-28',transaction_date='2026-02-28'),actor)
    paid=client.post('/api/v1/operations',json=op)
    assert paid.status_code==200
    assert client.post('/api/v1/operations',json=op).json()==paid.json()
    op['operation_id']='d268f064-a3dd-4f80-99f2-712530766cc2'
    assert client.post('/api/v1/operations',json=op).status_code==409
    assert len(client.get('/api/v1/purchases').json()['items'])==1
    assert client.get('/api/v1/budget-months/2026-02').json()['spent_minor']==10000
