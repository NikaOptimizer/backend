"""Chart drawing persistence; drawings are UI annotations, not strategy logic."""
import json
from json import JSONDecodeError

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from nika.backend.api.drawings.validation import validate_drawing_id, validate_payload, validate_scope
from nika.backend.api.models import Drawing


def serialize(drawing):
    return {
        'id': str(drawing.id),
        'strategy': drawing.strategy_key,
        'provider': drawing.provider,
        'instrument': drawing.instrument_id,
        'tool': drawing.tool,
        'schema_version': drawing.schema_version,
        'revision': drawing.revision,
        'data': drawing.data,
        'updated_at': drawing.updated_at.isoformat(),
    }


@require_GET
def drawing_collection(request):
    try:
        scope = validate_scope(
            request.GET.get('strategy', ''), request.GET.get('provider', ''), request.GET.get('instrument', '')
        )
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)
    return JsonResponse({'drawings': [serialize(drawing) for drawing in Drawing.objects.filter(**scope)]})


@require_http_methods(['PUT', 'DELETE'])
def drawing_detail(request, drawing_id):
    try:
        pk = validate_drawing_id(drawing_id)
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)

    if request.method == 'DELETE':
        # Idempotent: deleting an unknown drawing is not an error.
        Drawing.objects.filter(pk=pk).delete()
        return HttpResponse(status=204)

    try:
        fields = validate_payload(json.loads(request.body.decode('utf-8')))
    except (UnicodeDecodeError, JSONDecodeError):
        return JsonResponse({'detail': 'Body must be valid JSON'}, status=400)
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)

    with transaction.atomic():
        current = Drawing.objects.select_for_update().filter(pk=pk).first()
        if current is None:
            return JsonResponse(serialize(Drawing.objects.create(pk=pk, **fields)), status=201)
        scope = ('strategy_key', 'provider', 'instrument_id', 'tool')
        if any(getattr(current, key) != fields[key] for key in scope):
            return JsonResponse({'detail': 'Drawing scope and tool cannot change'}, status=400)
        if fields['revision'] <= current.revision:
            # A newer edit already landed; return it so the client can adopt it.
            return JsonResponse({'detail': 'Stale revision', 'drawing': serialize(current)}, status=409)
        for key, value in fields.items():
            setattr(current, key, value)
        current.save()
    return JsonResponse(serialize(current))
