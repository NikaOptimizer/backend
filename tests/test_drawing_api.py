import json
import uuid

from django.test import TestCase


def position(**overrides):
    data = {
        'entry': {'time': 1700000000, 'price': 100.0},
        'end_time': 1700036000,
        'target_price': 110.0,
        'stop_price': 95.0,
        'account': {'size': 1000, 'lot_size': 1, 'risk_mode': 'percent', 'risk': 1},
        'style': {'line_color': '#9aa4b2', 'profit_color': '#26a69a', 'stop_color': '#ef5350'},
    }
    data.update(overrides)
    return data


def body(revision=1, tool='long_position', data=None, **scope):
    return {
        'strategy': 'amber-breakout',
        'provider': 'databento',
        'instrument': 'instrument-1',
        'tool': tool,
        'schema_version': 1,
        'revision': revision,
        'data': position() if data is None else data,
        **scope,
    }


class DrawingApiTest(TestCase):
    scope = {'strategy': 'amber-breakout', 'provider': 'databento', 'instrument': 'instrument-1'}

    def put(self, drawing_id, payload):
        return self.client.put(f'/api/drawings/{drawing_id}/', json.dumps(payload), content_type='application/json')

    def test_create_list_update_delete(self):
        drawing_id = str(uuid.uuid4())
        self.assertEqual(self.put(drawing_id, body()).status_code, 201)

        listed = self.client.get('/api/drawings/', self.scope).json()['drawings']
        self.assertEqual([item['id'] for item in listed], [drawing_id])
        self.assertEqual(listed[0]['data']['target_price'], 110.0)

        updated = self.put(drawing_id, body(revision=2, data=position(target_price=120.0)))
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()['data']['target_price'], 120.0)

        self.assertEqual(self.client.delete(f'/api/drawings/{drawing_id}/').status_code, 204)
        self.assertEqual(self.client.delete(f'/api/drawings/{drawing_id}/').status_code, 204)
        self.assertEqual(self.client.get('/api/drawings/', self.scope).json()['drawings'], [])

    def test_list_is_scoped_to_strategy_and_instrument(self):
        self.put(uuid.uuid4(), body())
        self.put(uuid.uuid4(), body(strategy='deep-blue-reversion'))
        self.put(uuid.uuid4(), body(instrument='instrument-2'))
        self.assertEqual(len(self.client.get('/api/drawings/', self.scope).json()['drawings']), 1)

    def test_stale_revision_returns_current_drawing(self):
        drawing_id = uuid.uuid4()
        self.put(drawing_id, body(revision=3))
        response = self.put(drawing_id, body(revision=2, data=position(target_price=130.0)))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['drawing']['revision'], 3)
        self.assertEqual(response.json()['drawing']['data']['target_price'], 110.0)

    def test_scope_and_tool_cannot_change(self):
        drawing_id = uuid.uuid4()
        self.put(drawing_id, body())
        self.assertEqual(self.put(drawing_id, body(revision=2, instrument='other')).status_code, 400)
        short = body(revision=2, tool='short_position', data=position(target_price=90.0, stop_price=105.0))
        self.assertEqual(self.put(drawing_id, short).status_code, 400)

    def test_invalid_payloads_are_rejected(self):
        invalid = [
            body(data=position(target_price=90.0)),
            body(tool='short_position'),
            body(data=position(end_time=1700000000)),
            body(data=position(account={'size': 1000, 'lot_size': 1, 'risk_mode': 'percent', 'risk': 150})),
            body(data=position(style={'line_color': 'red', 'profit_color': '#26a69a', 'stop_color': '#ef5350'})),
            body(revision=0),
            body(tool='trend_line'),
            body(strategy="';--"),
            body(tool='marker', data={'time': 1700000000, 'label': '', 'color': '#f6b73c'}),
        ]
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assertEqual(self.put(uuid.uuid4(), payload).status_code, 400)
        self.assertEqual(self.put('not-a-uuid', body()).status_code, 400)
        bad_json = self.client.put(f'/api/drawings/{uuid.uuid4()}/', '{', content_type='application/json')
        self.assertEqual(bad_json.status_code, 400)

    def test_marker_round_trip(self):
        marker = {'time': 1700000000, 'label': ' Rule marker ', 'color': '#f6b73c'}
        response = self.put(uuid.uuid4(), body(tool='marker', data=marker))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['data']['label'], 'Rule marker')

    def test_list_requires_scope_and_rejects_other_methods(self):
        self.assertEqual(self.client.get('/api/drawings/').status_code, 400)
        self.assertEqual(self.client.post('/api/drawings/').status_code, 405)
        self.assertEqual(self.client.get(f'/api/drawings/{uuid.uuid4()}/').status_code, 405)
