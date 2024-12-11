import json, random, string, qrcode
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils.safestring import mark_safe
import redis
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from core.views import user_is_authenticated
from core.dataclasses import *


# Redis connection
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

#-------- Helper Functions --------

def generate_lobby_code():
    """
    Generate a random alphanumeric lobby code and ensure it doesn't already exist in Redis.
    """
    while True:
        lobby_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        lobby_key = generate_lobby_key(lobby_code)
        if not redis_client.exists(lobby_key):  # Check Redis for existing code
            return lobby_code

def generate_lobby_key(lobby_code:str):
    """
    Generate a unique Redis key for the given lobby code.
    """
    return f"lobby:{lobby_code}"

def save_lobby_to_redis(lobby:Lobby):
    """
    Save a Lobby instance to Redis.
    """
    redis_client.set(generate_lobby_key(lobby.code), lobby.serialize(), ex=7200)

def load_lobby_from_redis(lobby_code:str) -> Lobby:
    """
    Load a Lobby instance from Redis.
    """
    data = redis_client.get(generate_lobby_key(lobby_code))
    if data:
        return Lobby.deserialize(data)
    return None

#-------- View Functions --------

def create(request:HttpResponse):
    """Host creates a lobby."""
    # Generate a unique 5-character lobby code
    lobby_code = generate_lobby_code()

    # Store the lobby in Redis with a TTL of 1 hour
    lobby = Lobby(
        code= lobby_code,
        creator= "Host",  # Host is a device, not a player
        participants= [],
        game_started= False,
        gamemode= None,
        settings= {}
        )

    save_lobby_to_redis(lobby)

    # Store the lobby code in the host's session
    request.session['host_lobby_code'] = lobby_code

    # Redirect the host to the unified lobby
    return redirect('lobby:lobby', lobby_code=lobby_code)

def qr_code(request:HttpResponse, lobby_code):
    """Generate a QR code for the lobby invite link."""
    invite_link = f"{request.scheme}://{request.get_host()}/lobby/join/{lobby_code}/"
    qr = qrcode.make(invite_link)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer, content_type="image/png")

def join(request:HttpResponse, lobby_code=None):
    """Allow logged-in or guest users to join a lobby."""
    # Use the URL parameter if provided
    lobby_code = lobby_code or request.POST.get("lobby_code", "").upper()

    # Redirect unauthenticated users to login or guest registration page with a "next" parameter
    if not user_is_authenticated(request):
        return redirect(f"/?next=/lobby/join/{lobby_code}/")

    # Handle Post request
    if request.method == "POST":
        # If the code is empty, display an error
        if not lobby_code:
            return render(request, 'lobby/join.html', {"error": "Lobby code is required."})

        # Retrieve the lobby from Redis
        lobby = load_lobby_from_redis(lobby_code)

        if not lobby:
            return render(request, 'lobby/join.html', {"error": "Invalid or expired lobby code."})

        # Add the user to the participants list
        if request.user.is_authenticated:
            username = request.user.username
            profile_pic = "/static/images/default_pic.png"  # Replace with real profile picture logic
        else:
            user:GuestUser = GuestUser.get_guest_user_from_session(request)
            username = user.username
            profile_pic = user.profile_picture

        # Ensure the user is not the host and add to participants if not already present
        if username not in [p["name"] for p in lobby.participants]:
            lobby.participants.append({"name": username, "profile_pic": profile_pic})
            save_lobby_to_redis(lobby)

        #  # Send a WebSocket message to update participants
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     f"lobby_{lobby_code}",
        #     {
        #         "type": "lobby_message",
        #         "message": {
        #             "type": "update_participants",
        #             "participants": lobby["participants"]
        #         }
        #     }
        # )

        # Redirect directly to the lobby
        return redirect('lobby:lobby', lobby_code=lobby_code)

    # # Handle "Other" request
    # if lobby_code:
    #     # If a lobby code is provided, retrieve the lobby from Redis
    #     lobby = load_lobby_from_redis(lobby_code)

    #     if not lobby:
    #         return render(request, 'lobby/join.html', {"error": "Invalid or expired lobby code."})

    #     lobby = json.loads(lobby_data)
    #     participants = [
    #         participant for participant in lobby["participants"] if participant.get("name") != "Host"
    #     ]
    #     return redirect('lobby:lobby', lobby_code=lobby_code)

    # If GET request and no lobby code is provided, render the join page
    return render(request, 'lobby/join.html')

def lobby(request: HttpResponse, lobby_code):
    """
    lobby for both the host and participants.
    Redirects unauthenticated users to the join view for proper handling.
    """

    # Retrieve the lobby from Redis
    lobby = load_lobby_from_redis(lobby_code)

    if not lobby:
        return render(request, 'lobby/join.html', {"error": "Invalid or expired lobby code."})

    # Redirect unauthenticated users to the join view
    if not user_is_authenticated(request):
        return redirect(f"/?next=/lobby/join/{lobby_code}/")

    # Determine user role
    is_host = (
        "host_lobby_code" in request.session and request.session["host_lobby_code"] == lobby_code
    )

    if is_host:
        can_start_game = len(lobby.participants) >= 2
    else:
        can_start_game = False

        if request.user.is_authenticated:
            username = request.user.username
        else:
            username = GuestUser.get_guest_user_from_session(request).username

        # Redirect unjoined users to the join view
        if not is_host and username not in [p["name"] for p in lobby.participants]:
            return redirect('lobby:join_with_code', lobby_code=lobby_code)

    # Define gamemodes
    gamemodes = [gamemode.get_class().get_settings() for gamemode in Gamemodes] + [{"key":"dummy","name":"Dummy"}]

    return render(
        request,
        'lobby/lobby.html',
        {
            "lobby": lobby,
            "participants": lobby.participants,
            "is_host": is_host,
            "can_start_game": can_start_game,
            "gamemodes": gamemodes,
        }
    )
