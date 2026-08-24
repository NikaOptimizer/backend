import json
import os
import unittest

import django
from django.test import Client, SimpleTestCase, override_settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nika.backend.settings')
django.setup()


@override_settings(ROOT_URLCONF='nika.backend.urls')
class StrategyApiTemplateTest(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_strategy_list_endpoint_exists_but_is_not_implemented(self):
        response = self.client.get('/api/strategies/')

        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()['status'], 'not_implemented')
        self.assertIn('database', response.json()['detail'])

    def test_strategy_detail_endpoint_exists_but_is_not_implemented(self):
        response = self.client.get('/api/strategies/example-strategy/')

        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()['strategy_id'], 'example-strategy')
        self.assertEqual(response.json()['status'], 'not_implemented')

    def test_strategy_create_endpoint_exists_but_is_not_implemented(self):
        response = self.client.put(
            '/api/strategies/',
            data=json.dumps({'name': 'Draft Strategy'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()['status'], 'not_implemented')
        self.assertIn('database', response.json()['detail'])


if __name__ == '__main__':
    unittest.main()
