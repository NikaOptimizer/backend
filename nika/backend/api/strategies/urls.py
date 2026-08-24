from django.urls import path

from nika.backend.api.strategies import views

urlpatterns = [
    path('', views.strategy_collection, name='strategy-collection'),
    path('<str:strategy_id>/', views.strategy_detail, name='strategy-detail'),
]
