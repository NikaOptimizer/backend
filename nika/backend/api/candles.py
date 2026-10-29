"""HTTP validation and orchestration; storage and aggregation live in data-manager."""
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from nika.data_manager.manager import DataManager
from nika.data_manager.questdb import CandleStoreError, validate_request

logger = logging.getLogger('nika.backend.candles')


def unavailable():
    logger.warning('Candle store request failed')
    return JsonResponse({'detail': 'Candle data is temporarily unavailable. Please retry.'}, status=503)


@require_GET
def candles(request):
    try:
        parameters = {
            'symbol': request.GET.get('symbol', ''),
            'provider': request.GET.get('provider', ''),
            'timeframe': request.GET.get('timeframe', '15m'),
            'period': request.GET.get('period', '1M'),
            'limit': int(request.GET.get('limit', '500')),
        }
        validate_request(**parameters)
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)
    try:
        rows = DataManager().get_candles(**parameters)
    except CandleStoreError:
        return unavailable()
    return JsonResponse({**parameters, 'candles': rows}, json_dumps_params={'allow_nan': False})


@require_GET
def instruments(request):
    try:
        rows = DataManager().get_instruments()
    except CandleStoreError:
        return unavailable()
    return JsonResponse({'instruments': rows})
