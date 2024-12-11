from django.urls import path
from . import views

app_name = 'lobby'

urlpatterns = [
    path('create/', views.create, name='create'),  # Host creates a lobby
    path('join/', views.join, name='join'),  # Join form (enter lobby code)
    path('join/<str:lobby_code>/', views.join, name='join_with_code'),  # Join via code
    path('qr/<str:lobby_code>/', views.qr_code, name='qr_code'),  # QR code generation
    path('<str:lobby_code>/', views.lobby, name='lobby'),  # Unified dashboard
]
