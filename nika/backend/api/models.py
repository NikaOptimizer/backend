import uuid

from django.db import models


class Drawing(models.Model):
    """A chart drawing owned by a strategy view of one instrument stream.

    `strategy_key` is the frontend strategy identifier stored as plain text;
    strategies have no database model yet, so it is not a foreign key.
    Tool-specific geometry and settings live in `data`, validated by the API.
    """

    LONG_POSITION = 'long_position'
    SHORT_POSITION = 'short_position'
    MARKER = 'marker'
    TOOL_CHOICES = [
        (LONG_POSITION, 'Long position'),
        (SHORT_POSITION, 'Short position'),
        (MARKER, 'Marker'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy_key = models.CharField(max_length=64)
    provider = models.CharField(max_length=64)
    instrument_id = models.CharField(max_length=128)
    tool = models.CharField(max_length=32, choices=TOOL_CHOICES)
    schema_version = models.PositiveSmallIntegerField(default=1)
    revision = models.PositiveIntegerField(default=1)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['strategy_key', 'provider', 'instrument_id'], name='drawing_scope_idx'),
        ]
        ordering = ['created_at']
