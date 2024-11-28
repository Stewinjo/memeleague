from django.db import models
from django.conf import settings
from django.utils.timezone import now

class Lobby(models.Model):
    code = models.CharField(max_length=6, unique=True)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_lobbies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lobby {self.code}"


class LobbyPlayer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lobby_players',
        default=1  # Replace 1 with the ID of a placeholder user
    )
    lobby = models.ForeignKey(Lobby, on_delete=models.CASCADE, related_name='players')
    joined_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} in Lobby {self.lobby.code}"
