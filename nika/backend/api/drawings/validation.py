"""Validation for drawing payloads; the frontend contract is schema version 1."""
import math
import re
import uuid

from nika.backend.api.models import Drawing

SCHEMA_VERSION = 1
KEY_PATTERN = re.compile(r'^[A-Za-z0-9._:-]{1,128}$')
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$')
POSITION_TOOLS = {Drawing.LONG_POSITION, Drawing.SHORT_POSITION}
TOOLS = {choice for choice, _ in Drawing.TOOL_CHOICES}


def validate_scope(strategy, provider, instrument):
    for name, value, limit in (('strategy', strategy, 64), ('provider', provider, 64), ('instrument', instrument, 128)):
        if not isinstance(value, str) or len(value) > limit or not KEY_PATTERN.match(value):
            raise ValueError(f'Invalid {name}')
    return {'strategy_key': strategy, 'provider': provider, 'instrument_id': instrument}


def validate_drawing_id(value):
    try:
        return uuid.UUID(value)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError('Invalid drawing id') from exc


def validate_payload(payload):
    """Return model fields for a PUT body or raise ValueError."""
    if not isinstance(payload, dict):
        raise ValueError('Body must be a JSON object')
    fields = validate_scope(payload.get('strategy'), payload.get('provider'), payload.get('instrument'))

    tool = payload.get('tool')
    if tool not in TOOLS:
        raise ValueError('Unknown tool')
    if payload.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Unsupported schema_version')
    revision = payload.get('revision')
    if not _is_int(revision) or revision < 1:
        raise ValueError('revision must be a positive integer')

    data = payload.get('data')
    if not isinstance(data, dict):
        raise ValueError('data must be an object')
    data = validate_position(tool, data) if tool in POSITION_TOOLS else validate_marker(data)

    return {**fields, 'tool': tool, 'schema_version': SCHEMA_VERSION, 'revision': revision, 'data': data}


def validate_position(tool, data):
    entry = _object(data, 'entry')
    entry_time = _timestamp(entry, 'time')
    entry_price = _number(entry, 'price')
    end_time = _timestamp(data, 'end_time')
    target = _number(data, 'target_price')
    stop = _number(data, 'stop_price')

    if end_time <= entry_time:
        raise ValueError('end_time must be after entry time')
    if tool == Drawing.LONG_POSITION and not stop < entry_price < target:
        raise ValueError('Long position requires stop < entry < target')
    if tool == Drawing.SHORT_POSITION and not target < entry_price < stop:
        raise ValueError('Short position requires target < entry < stop')

    account = _object(data, 'account')
    risk_mode = account.get('risk_mode')
    if risk_mode not in ('percent', 'amount'):
        raise ValueError('account.risk_mode must be percent or amount')
    risk = _number(account, 'risk', positive=True)
    if risk_mode == 'percent' and risk > 100:
        raise ValueError('account.risk percent must not exceed 100')

    style = _object(data, 'style')
    return {
        'entry': {'time': entry_time, 'price': entry_price},
        'end_time': end_time,
        'target_price': target,
        'stop_price': stop,
        'account': {
            'size': _number(account, 'size', positive=True),
            'lot_size': _number(account, 'lot_size', positive=True),
            'risk_mode': risk_mode,
            'risk': risk,
        },
        'style': {key: _color(style, key) for key in ('line_color', 'profit_color', 'stop_color')},
    }


def validate_marker(data):
    label = data.get('label')
    if not isinstance(label, str) or not 0 < len(label.strip()) <= 80:
        raise ValueError('label must be 1-80 characters')
    return {'time': _timestamp(data, 'time'), 'label': label.strip(), 'color': _color(data, 'color')}


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _object(data, key):
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f'{key} must be an object')
    return value


def _timestamp(data, key):
    value = data.get(key)
    if not _is_int(value) or value < 0:
        raise ValueError(f'{key} must be a UTC Unix timestamp in seconds')
    return value


def _number(data, key, positive=False):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{key} must be a finite number')
    if positive and value <= 0:
        raise ValueError(f'{key} must be positive')
    return value


def _color(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not COLOR_PATTERN.match(value):
        raise ValueError(f'{key} must be a hex color')
    return value
