from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from nika.data_manager.inspector import InspectorUnavailable


@override_settings(DEBUG=True)
class DebugApiTest(SimpleTestCase):
    def test_catalog_and_inspection(self):
        with patch('nika.backend.api.debug.Inspector') as store:
            store.return_value.datasets.return_value = [{'id': 'source'}]
            self.assertEqual(self.client.get('/api/debug/datasets/').json()['datasets'], [{'id': 'source'}])
            store.return_value.inspect.return_value = {'rows': [], 'day': '2024-01-01'}
            result = self.client.get('/api/debug/inspection/', {'dataset': 'source', 'day': '2024-01-01', 'offset': '3', 'limit': '10'})
            store.return_value.inspect.assert_called_once_with('source', '2024-01-01', 3, 10)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result['Cache-Control'], 'no-store')

    def test_errors_do_not_expose_paths_or_credentials(self):
        for path, method in [('/api/debug/datasets/', 'datasets'), ('/api/debug/inspection/', 'inspect')]:
            with patch('nika.backend.api.debug.Inspector') as store:
                getattr(store.return_value, method).side_effect = InspectorUnavailable('/private/secret')
                response = self.client.get(path)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private', response.content.decode())
        with patch('nika.backend.api.debug.Inspector') as store:
            store.return_value.inspect.side_effect = KeyError('missing')
            self.assertEqual(self.client.get('/api/debug/inspection/').status_code, 404)
            store.return_value.inspect.side_effect = ValueError('invalid')
            self.assertEqual(self.client.get('/api/debug/inspection/').status_code, 400)
        self.assertEqual(self.client.get('/api/debug/inspection/?offset=bad').status_code, 400)

    def test_disabled_outside_debug_and_read_only(self):
        for path in ['/api/debug/datasets/', '/api/debug/inspection/']:
            with override_settings(DEBUG=False), patch('nika.backend.api.debug.Inspector') as store:
                self.assertEqual(self.client.get(path).status_code, 404)
                store.assert_not_called()
            self.assertEqual(self.client.post(path).status_code, 405)
