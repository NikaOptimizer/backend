from django.urls import path

from nika.backend.api.drawings import views

urlpatterns = [
    path('', views.drawing_collection, name='drawing-collection'),
    path('<str:drawing_id>/', views.drawing_detail, name='drawing-detail'),
]
