from datetime import UTC, datetime, timedelta
import json
from types import SimpleNamespace
from uuid import uuid4

import httpx2
from openai import OpenAI
import pytest
from sqlalchemy import select, update, func

from conftest import submit
from pigpen import schema as s
from pigpen.advisor import Advisor, Question
from pigpen.errors import DomainError
from pigpen.monthly_analysis import materialize
from pigpen import monthly_reviews as m


def at(value):
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


@pytest.fixture
def review_data(client, users):
    actor = users[0]['id']
    db = client.app.state.database
    with db.transaction() as c:
        categories = {r['name']: r['id'] for r in c.execute(select(s.categories)).mappings()}
    other = categories.get('Other') or submit(client, 'category.create', {'name': 'Other', 'kind': 'expense'}, actor)['id']
    food = categories['Food']
    for month, amount in [('2026-08', 33000), ('2026-09', 39000), ('2026-10', 36000), ('2026-11', 54000)]:
        submit(client, 'budget.set', {'month': month, 'expected_income_minor': 320000,
               'allocations': [{'category_id': food, 'amount_minor': 60000},
                               {'category_id': categories['Savings'], 'amount_minor': 20000}]}, actor)
        submit(client, 'purchase.create', {'item': 'Meal', 'amount_minor': amount, 'category_id': food,
                                         'transaction_date': month + '-03'}, actor)
    pets = []
    for day, amount, item in [('04', 6200, 'Dog food'), ('10', 2800, 'Cat litter')]:
        payload = {'item': item, 'amount_minor': amount, 'category_id': other, 'transaction_date': '2026-11-' + day}
        # Compatible with the independently deployed receipt baseline and the shared checkout.
        if 'category_explanation' in s.purchases.c:
            payload['category_explanation'] = 'Pet supplies'
        pets.append(submit(client, 'purchase.create', payload, actor))
    plan = {'summary': 'Food spending increased; pet supplies could use a category.', 'findings': [
        {'kind': 'trend', 'category_id': food, 'purchase_ids': [], 'title': 'Food rose 50%',
         'explanation': '$540 spent versus a $360 average over August–October.', 'suggested_category': None},
        {'kind': 'category_group', 'category_id': None, 'purchase_ids': [p['id'] for p in pets],
         'title': 'Pet care could use a category', 'explanation': 'Two purchases in Other total $90.', 'suggested_category': 'Pet care'}]}
    return db, actor, plan, pets


def prepare(db, plan):
    assert not m.run_once(db, lambda _: plan, at('2026-11-22T18:00:00'))
    assert m.run_once(db, lambda _: plan, at('2026-12-01T13:00:00'))


def test_explicit_preview_is_readable_idempotent_and_replaced_on_schedule(client, review_data):
    db, actor, plan, pets = review_data
    today = at('2026-11-22T18:00:00')
    assert not m.run_once(db, lambda _: plan, today)
    assert m.preview_now(db, lambda _: plan, today) == '2026-11'
    assert m.preview_now(db, lambda _: pytest.fail('duplicate preview'), today) == '2026-11'
    preview = client.get('/api/v1/advisor/reviews/2026-11').json()
    assert preview['summary'].startswith('Month-to-date preview.')
    archive = m.list_reviews(db, instant=today)
    assert len(archive['items']) == 1 and archive['show_home']
    assert archive['latest']['is_preview'] and archive['latest']['month'] == '2026-11'
    assert not m.list_reviews(db, instant=at('2026-12-01T12:59:59'))['show_home']
    with db.transaction() as c:
        notes = list(c.execute(select(s.notifications).where(s.notifications.c.kind == 'analysis.ready')).mappings())
        assert len(notes) == 3 and all('preview is ready' in n['message'] for n in notes)
    assert not m.run_once(db, lambda _: pytest.fail('premature completion'), today)
    assert m.run_once(db, lambda _: plan, at('2026-12-01T13:00:00'))
    final = m.read_review(db, '2026-11')
    assert final['id'] == preview['id'] and not final['summary'].startswith('Month-to-date preview.')
    assert m.list_reviews(db, instant=at('2026-12-01T13:00:01'))['show_home']
    with db.transaction() as c:
        notes = list(c.execute(select(s.notifications).where(s.notifications.c.kind == 'analysis.ready')).mappings())
        assert len(notes) == 6
        assert len({n['event_key'] for n in notes}) == 2


def test_preview_rejects_records_changed_during_inference(client, review_data):
    db, actor, plan, pets = review_data
    def change(_):
        submit(client, 'purchase.delete', {'expected_revision': 1}, actor, pets[0]['id'])
        return plan
    with pytest.raises(ValueError, match='Records changed'):
        m.preview_now(db, change, at('2026-11-22T18:00:00'))
    with db.transaction() as c:
        assert c.scalar(select(func.count()).select_from(m.reviews)) == 0


def test_schedule_timezone_five_days_and_idempotent_notification(client, review_data):
    db, actor, plan, pets = review_data
    assert not m.run_once(db, lambda _: plan, at('2026-11-22T18:00:00'))
    assert not m.run_once(db, lambda _: plan, at('2026-12-01T12:59:59'))
    assert m.run_once(db, lambda _: plan, at('2026-12-01T13:00:00'))
    assert not m.run_once(db, lambda _: pytest.fail('duplicate model call'), at('2026-12-01T13:00:01'))
    with db.transaction() as c:
        notes = list(c.execute(select(s.notifications).where(s.notifications.c.kind == 'analysis.ready')).mappings())
        assert len(notes) == 3
        assert all(n['message'] == 'Sir Pennysworth’s November 2026 analysis is ready.' for n in notes)
        assert c.scalar(select(func.count()).select_from(s.outbox).where(s.outbox.c.notification_id.in_([n['id'] for n in notes]))) == 3
    # UTC December 6 is still local December 5 until 05:00.
    assert m.list_reviews(db, instant=at('2026-12-06T04:59:59'))['show_home']
    assert not m.list_reviews(db, instant=at('2026-12-06T05:00:00'))['show_home']
    report = client.get('/api/v1/advisor/reviews/2026-11').json()
    assert report['totals'] == {'budgeted_minor': 60000, 'spent_minor': 63000, 'remaining_minor': -3000,
                               'savings_allocated_minor': 20000, 'savings_actual_minor': 0, 'income_minor': 0}
    assert [p['amount_minor'] for p in report['findings'][0]['chart']] == [33000,39000,36000,54000]
    assert [p['amount_minor'] for p in report['findings'][1]['chart']] == [9000,0]
    assert client.get('/api/v1/advisor/reviews?before=bad').status_code == 422
    assert client.get('/api/v1/advisor/reviews/2026-12').status_code == 404


def test_saved_report_survives_corrections_and_chat_uses_server_context(client, review_data, monkeypatch):
    db, actor, plan, pets = review_data
    prepare(db, plan)
    original = m.read_review(db, '2026-11')
    submit(client, 'purchase.delete', {'expected_revision': 1}, actor, pets[0]['id'])
    changed = m.read_review(db, '2026-11')
    assert changed['data_changed'] and changed['totals'] == original['totals']
    assert changed['findings'] == original['findings']
    calls = []
    def respond(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output=[], status='completed', output_text='The saved review included dog food.')
    provider = SimpleNamespace(responses=SimpleNamespace(create=respond))
    question = Question(actor_id=actor, month='2026-11', question='Which purchases?', review_month='2026-11', finding_id='finding-2')
    result = Advisor(db).answer(question, provider)
    context = json.loads(calls[0]['input'][-1]['content'])['saved_monthly_review']
    assert context['selected_finding']['id'] == 'finding-2'
    assert context['selected_finding']['purchases'][0]['id'] == pets[0]['id']
    assert result['sources'][1]['path'] == '/analyses/2026-11'
    with pytest.raises(DomainError):
        Advisor(db).answer(question.model_copy(update={'finding_id': 'fabricated'}), provider)
    with pytest.raises(DomainError):
        Advisor(db).answer(question.model_copy(update={'review_month': '2026-10'}), provider)


def test_failure_retry_lease_recovery_and_invalid_evidence(review_data):
    db, actor, plan, pets = review_data
    start = at('2026-12-01T13:00:00')
    m.run_once(db, lambda _: plan, at('2026-11-22T18:00:00'))
    bad = {**plan, 'findings': [{**plan['findings'][0], 'purchase_ids': [str(uuid4())]}]}
    assert not m.run_once(db, lambda _: bad, start)
    with db.transaction() as c:
        row = c.execute(select(m.reviews)).mappings().one()
        assert row['status'] == 'pending' and row['attempts'] == 1
        assert not c.scalar(select(s.notifications.c.id).where(s.notifications.c.kind == 'analysis.ready'))
    assert not m.run_once(db, lambda _: pytest.fail('backoff skipped'), start + timedelta(seconds=30))
    def generate(evidence):
        assert not m.run_once(db, lambda _: pytest.fail('lease ignored'), start + timedelta(minutes=3))
        return plan
    assert m.run_once(db, generate, start + timedelta(minutes=3))
    with db.transaction() as c:
        evidence = m.evidence_at(c, '2026-11')
    missing = {**evidence, 'categories': [{**c, 'history': []} for c in evidence['categories']]}
    with pytest.raises(ValueError, match='history'):
        materialize(missing, plan)
    with pytest.raises(ValueError, match='Other'):
        materialize(evidence, {**plan, 'findings': [{**plan['findings'][1], 'purchase_ids': [pets[0]['id']]}]})


def test_catchup_archives_older_month_without_notification_and_empty_month(review_data):
    db, actor, plan, pets = review_data
    quiet = {'summary': 'No significant patterns stand out.', 'findings': []}
    m.run_once(db, lambda _: quiet, at('2026-10-22T18:00:00'))
    assert m.run_once(db, lambda _: quiet, at('2026-12-03T13:00:00'))
    with db.transaction() as c:
        assert not c.scalar(select(s.notifications.c.id).where(s.notifications.c.kind == 'analysis.ready'))
    assert m.run_once(db, lambda _: plan, at('2026-12-03T13:01:00'))
    page = m.list_reviews(db, limit=1)
    assert [r['month'] for r in page['items']] == ['2026-11'] and page['next_before'] == '2026-11'
    assert [r['month'] for r in m.list_reviews(db, before=page['next_before'])['items']] == ['2026-10']
    # An interrupted process relinquishes its month after the durable lease expires.
    with db.transaction(write=True) as c:
        c.execute(insert_review('2026-12', pets[0]['household_id'], at('2027-01-01T13:00:00')))
    assert m.run_once(db, lambda _: {'summary': 'No recorded purchases this month.', 'findings': []}, at('2027-01-01T13:06:00'))
    assert m.read_review(db, '2026-12')['totals']['spent_minor'] == 0


def insert_review(month, household_id, stamp):
    return m.reviews.insert().values(id=str(uuid4()), household_id=household_id, month=month, status='pending', attempts=0,
        next_attempt=stamp.isoformat(), lease_token='interrupted', lease_until=(stamp+timedelta(minutes=5)).isoformat())


def test_provider_structured_output_and_refusal(monkeypatch, review_data):
    db, actor, plan, pets = review_data
    with db.transaction() as c:
        evidence = m.evidence_at(c, '2026-11')
    bodies = []
    def provider(req):
        body = json.loads(req.content);bodies.append(body)
        assert body['store'] is False and body['text']['format']['type'] == 'json_schema'
        assert body['text']['format']['strict'] is True
        return httpx2.Response(200, json={'id':'resp_test','object':'response','status':'completed',
            'output':[{'type':'message','role':'assistant','status':'completed','id':'msg_test',
                       'content':[{'type':'output_text','text':json.dumps(plan),'annotations':[]}]}]})
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-key')
    monkeypatch.setattr(m,'OpenAI',lambda **kwargs:OpenAI(**kwargs,http_client=httpx2.Client(transport=httpx2.MockTransport(provider))))
    assert m.generate(evidence) == plan
    assert len(bodies) == 1


def test_parent_children_and_missing_months_are_not_double_counted(review_data):
    db, actor, plan, pets = review_data
    with db.transaction() as c:
        evidence = m.evidence_at(c, '2026-11')
    assert evidence['coverage']['comparison_months'] == ['2026-08','2026-09','2026-10']
    assert len(evidence['categories'][0]['history']) <= 3
    assert evidence['totals']['spent_minor'] == 63000


def test_child_purchases_roll_up_once(client, review_data):
    db, actor, plan, pets = review_data
    parent = next(c for c in client.get('/api/v1/categories').json()['items'] if c['name'] == 'Subscriptions')
    child = submit(client, 'category.create', {'name': 'Music', 'kind': 'expense', 'parent_id': parent['id']}, actor)
    submit(client, 'purchase.create', {'item': 'Monthly music', 'category_id': child['id'], 'amount_minor': 1000,
                                     'transaction_date': '2026-11-12'}, actor)
    with db.transaction() as c:
        evidence = m.evidence_at(c, '2026-11')
    assert evidence['totals']['spent_minor'] == 64000
    assert next(c for c in evidence['categories'] if c['id'] == parent['id'])['spent_minor'] == 1000
    assert not any(c['id'] == child['id'] for c in evidence['categories'])


def test_generation_race_retries_without_partial_publication(client, review_data):
    db, actor, plan, pets = review_data
    m.run_once(db, lambda _: plan, at('2026-11-22T18:00:00'))
    def changing_generator(_):
        submit(client, 'purchase.delete', {'expected_revision': 1}, actor, pets[0]['id'])
        return plan
    assert not m.run_once(db, changing_generator, at('2026-12-01T13:00:00'))
    with db.transaction() as c:
        assert c.scalar(select(m.reviews.c.status)) == 'pending'
        assert not c.scalar(select(s.notifications.c.id).where(s.notifications.c.kind == 'analysis.ready'))


def test_monthly_outbox_delivers_safe_deep_link_once(client, review_data):
    from test_attachments_push import subscription
    from pigpen.push import deliver_once
    db, actor, plan, pets = review_data
    subscription(client, actor)
    # Drain unrelated fixture notifications before publishing the review.
    while deliver_once(db, lambda sub, payload: 200):
        pass
    prepare(db, plan)
    payloads = []
    while deliver_once(db, lambda sub, payload: payloads.append(payload) or 200):
        pass
    assert len(payloads) == 1
    assert payloads[0]['url'] == '/analyses/2026-11'
    assert payloads[0]['title'] == 'Monthly analysis ready'
    assert '$' not in payloads[0]['body'] and 'Food' not in payloads[0]['body']
    assert not deliver_once(db, lambda sub, payload: pytest.fail('Duplicate push'))
