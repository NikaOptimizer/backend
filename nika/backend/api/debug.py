"""Development diagnostics: bounded reads from a precomputed inspection archive."""
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from nika.data_manager.inspector import Inspector, InspectorUnavailable


def enabled():
    return settings.DEBUG


def reply(payload, status=200):
    response = JsonResponse(payload, status=status, json_dumps_params={'allow_nan': False})
    response['Cache-Control'] = 'no-store'
    return response


@require_GET
def datasets(request):
    if not enabled():
        return reply({'detail': 'Not found.'}, 404)
    try:
        return reply({'datasets': Inspector().datasets()})
    except InspectorUnavailable:
        return reply({'detail': 'Data Inspector archive is unavailable. Generate and configure an inspection archive.'}, 503)


@require_GET
def inspection(request):
    if not enabled():
        return reply({'detail': 'Not found.'}, 404)
    try:
        offset = int(request.GET.get('offset', '0'))
        limit = int(request.GET.get('limit', '300'))
        result = Inspector().inspect(request.GET.get('dataset', ''), request.GET.get('day') or None, offset, limit)
        return reply(result)
    except (ValueError, OverflowError):
        return reply({'detail': 'Invalid request. Use a dataset ID, YYYY-MM-DD day, non-negative offset and limit 1–2000.'}, 400)
    except KeyError:
        return reply({'detail': 'Dataset not found.'}, 404)
    except InspectorUnavailable:
        return reply({'detail': 'Data Inspector archive is unavailable. Generate and configure an inspection archive.'}, 503)
