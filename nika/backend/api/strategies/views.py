import json
from json import JSONDecodeError

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

NOT_IMPLEMENTED_STATUS = 501
DATABASE_PENDING_DETAIL = 'Strategy API contract exists, but database-backed strategy storage is not implemented yet.'


def not_implemented_response(payload: dict) -> JsonResponse:
    return JsonResponse(
        {
            'status': 'not_implemented',
            'detail': DATABASE_PENDING_DETAIL,
            **payload,
        },
        status=NOT_IMPLEMENTED_STATUS,
    )


@require_http_methods(['GET', 'PUT'])
def strategy_collection(request: HttpRequest) -> JsonResponse:
    if request.method == 'GET':
        return list_strategies(request)

    return create_strategy(request)


def list_strategies(request: HttpRequest) -> JsonResponse:
    return not_implemented_response(
        {
            'endpoint': 'strategy_list',
            'method': request.method,
            'strategies': [],
        }
    )


def create_strategy(request: HttpRequest) -> JsonResponse:
    payload = parse_json_body(request)
    return not_implemented_response(
        {
            'endpoint': 'strategy_create',
            'method': request.method,
            'received': payload,
        }
    )


@require_http_methods(['GET'])
def strategy_detail(request: HttpRequest, strategy_id: str) -> JsonResponse:
    return not_implemented_response(
        {
            'endpoint': 'strategy_detail',
            'method': request.method,
            'strategy_id': strategy_id,
        }
    )


def parse_json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, JSONDecodeError):
        return {}

    if isinstance(payload, dict):
        return payload

    return {'value': payload}
