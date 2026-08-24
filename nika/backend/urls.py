from django.urls import include, path

urlpatterns = [
    path('api/strategies/', include('nika.backend.api.strategies.urls')),
]
