import json
import httpx2
from openai import OpenAI
from conftest import submit
from test_budget import food


def test_highlights_cache_invalidation_and_disabled_questions(client, users, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    url = '/api/v1/advisor/insights?month=2026-11'
    before = client.get(url).json()
    assert before == client.get(url).json()
    actor = users[0]['id']
    purchase = submit(client, 'purchase.create', dict(item='Example', amount_minor=990, category_id=food(client)['id'],
                                                      transaction_date='2026-11-02'), actor)
    after = client.get(url).json()
    assert not after['enabled'] and '$9.90' in str(after['insights'])
    submit(client, 'purchase.delete', {'expected_revision': 1}, actor, purchase['id'])
    assert client.get(url).json()['insights'] == before['insights']
    payload = dict(question='How much?', month='2026-11', actor_id=actor)
    assert client.post('/api/v1/advisor/ask', json=payload).status_code == 503
    assert client.post('/api/v1/advisor/ask', json={**payload, 'month': 'bad'}).status_code == 422


def test_provider_wire_tool_scope_and_grounding(client, users, monkeypatch):
    actor = users[0]['id']
    category = food(client)['id']
    purchase = submit(client, 'purchase.create', dict(item='Untrusted text', amount_minor=3025, category_id=category,
                        transaction_date='2026-11-12', description='SECRET receipt notes'), actor)
    requests = []

    def provider(req):
        body = json.loads(req.content)
        assert body['store'] is False and 'SECRET' not in req.content.decode()
        requests.append(body)
        if len(requests) <= 2:
            name = 'delete_purchase' if len(requests) == 1 else 'search_purchases'
            output = [dict(type='function_call', name=name, id='fc_test', call_id='call_test',
                           arguments=json.dumps(dict(month='2026-11', term='Food')))]
        else:
            assert 'Invalid read' in body['input'][-3]['output']
            evidence = json.loads(body['input'][-1]['output'])
            assert evidence['total_minor'] == 3025 and evidence['match_count'] == 1
            output = [dict(type='message', role='assistant', status='completed', id='msg_test',
                           content=[dict(type='output_text', text='Food spending was $30.25.', annotations=[])])]
        return httpx2.Response(200, json=dict(id='resp_test', object='response', status='completed', output=output))

    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-key')
    monkeypatch.setattr('pigpen.advisor.OpenAI', lambda **kwargs: OpenAI(**kwargs, http_client=httpx2.Client(
        transport=httpx2.MockTransport(provider))))
    response = client.post('/api/v1/advisor/ask', json=dict(actor_id=actor, month='2026-11', question='What drove spending?'))
    assert response.status_code == 200, response.text
    assert response.json()['sources'][-1]['path'] == '/purchases?detail=' + purchase['id']
    assert response.json()['answer'] == 'Food spending was $30.25.'


def test_purchase_detail_excludes_private_notes_and_deleted_records(client, users):
    from pigpen.advisor_data import purchase_detail
    actor = users[0]['id']
    item = submit(client, 'purchase.create', dict(item='Tea', amount_minor=450, category_id=food(client)['id'],
                  description='private note', transaction_date='2026-01-31'), actor)
    with client.app.state.database.transaction() as conn:
        details = purchase_detail(conn, item['id'])
    assert details['purchase']['purchaser'] == users[0]['name']
    assert 'private note' not in str(details)
    submit(client, 'purchase.delete', {'expected_revision': 1}, actor, item['id'])
    with client.app.state.database.transaction() as conn:
        assert 'purchase' not in purchase_detail(conn, item['id'])
