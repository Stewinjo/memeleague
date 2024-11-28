from django.urls import path
from . import views

app_name = 'lobby'

urlpatterns = [
    path('<str:lobby_code>/', views.lobby, name='lobby'),
]
