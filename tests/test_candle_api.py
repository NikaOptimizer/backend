from unittest.mock import patch
from django.test import SimpleTestCase
from nika.data_manager.questdb import CandleStoreError


class CandleApiTest(SimpleTestCase):
    def test_candles_delegate_to_data_manager(self):
        rows = [{'time': 1700000000, 'open': 1, 'high': 3, 'low': 0, 'close': 2, 'volume': 4}]
        with patch('nika.backend.api.candles.DataManager') as manager:
            manager.return_value.get_candles.return_value = rows
            response = self.client.get('/api/candles/', {'symbol': 'id', 'provider': 'test', 'timeframe': '1h', 'period': '1W', 'limit': 12})
            manager.return_value.get_candles.assert_called_once_with(symbol='id', provider='test', timeframe='1h', period='1W', limit=12)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['candles'], rows)

    def test_invalid_inputs_return_400_without_storage_access(self):
        with patch('nika.backend.api.candles.DataManager') as manager:
            for parameters in ({}, {'symbol': 'id', 'provider': 'test', 'limit': 'bad'},
                               {'symbol': "';--", 'provider': 'test'},
                               {'symbol': 'id', 'provider': 'test', 'timeframe': 'bad'},
                               {'symbol': 'id', 'provider': 'test', 'limit': 0}):
                self.assertEqual(self.client.get('/api/candles/', parameters).status_code, 400)
            manager.assert_not_called()

    def test_empty_is_success(self):
        with patch('nika.backend.api.candles.DataManager') as manager:
            manager.return_value.get_candles.return_value = []
            response = self.client.get('/api/candles/', {'symbol': 'missing', 'provider': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['candles'], [])

    def test_store_failures_return_503_without_details(self):
        for path, method in (('/api/candles/?symbol=id&provider=test', 'get_candles'), ('/api/instruments/', 'get_instruments')):
            with patch('nika.backend.api.candles.DataManager') as manager:
                getattr(manager.return_value, method).side_effect = CandleStoreError('private details')
                response = self.client.get(path)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private', response.content.decode())

    def test_instruments_delegate_and_posts_are_rejected(self):
        with patch('nika.backend.api.candles.DataManager') as manager:
            manager.return_value.get_instruments.return_value = [{'instrument_id': 'id', 'provider': 'test'}]
            response = self.client.get('/api/instruments/')
        self.assertEqual(response.json()['instruments'][0]['instrument_id'], 'id')
        for path in ('/api/instruments/', '/api/candles/'):
            self.assertEqual(self.client.post(path).status_code, 405)
