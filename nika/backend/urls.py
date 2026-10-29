from django.urls import include, path

from nika.backend.api.candles import candles, instruments
from nika.backend.api.debug import datasets, inspection

urlpatterns = [
    path("api/debug/datasets/", datasets, name="debug-datasets"),
    path("api/debug/inspection/", inspection, name="debug-inspection"),
    path("api/candles/", candles, name="candles"),
    path("api/instruments/", instruments, name="instruments"),
    path('api/drawings/', include('nika.backend.api.drawings.urls')),
    path('api/strategies/', include('nika.backend.api.strategies.urls')),
]
