from django.shortcuts import render, redirect, get_object_or_404
from .models import Lobby, LobbyPlayer
import random
import string

# Generate unique lobby code
def generate_lobby_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Create Lobby
def create_lobby(request):
    if request.method == 'POST':
        lobby = Lobby.objects.create(code=generate_lobby_code(), host=request.user)
        LobbyPlayer.objects.create(lobby=lobby, user=request.user)
        return redirect('lobby', lobby_code=lobby.code)
    return render(request, 'lobby/create_lobby.html')

# Join Lobby
def join_lobby(request):
    if request.method == 'POST':
        code = request.POST.get('code').strip()
        lobby = get_object_or_404(Lobby, code=code)
        LobbyPlayer.objects.get_or_create(lobby=lobby, user=request.user)
        return redirect('lobby', lobby_code=lobby.code)
    return render(request, 'lobby/join_lobby.html')

# Lobby Page
def lobby(request, lobby_code):
    lobby = get_object_or_404(Lobby, code=lobby_code)
    players = lobby.players.all()
    return render(request, 'lobby/lobby.html', {'lobby': lobby, 'players': players})
