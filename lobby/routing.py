from django.urls import path
from lobby.consumers import LobbyConsumer
from meme_forge.consumers import MemeForgeConsumer

websocket_urlpatterns = [
    path("ws/lobby/<str:lobby_code>/", LobbyConsumer.as_asgi()),
    path("ws/meme_forge/<str:lobby_code>/", MemeForgeConsumer.as_asgi()),
]
