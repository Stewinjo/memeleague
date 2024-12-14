import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
import redis

# Redis client
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.lobby_code = self.scope['url_route']['kwargs']['lobby_code']
        self.lobby_group_name = f"lobby_{self.lobby_code}"
        self.username = self.scope['user'].username if self.scope['user'].is_authenticated else "Guest"

        # Add user to Redis presence list
        redis_client.sadd(f"lobby:{self.lobby_code}:users", self.username)

        # Join lobby group
        await self.channel_layer.group_add(
            self.lobby_group_name,
            self.channel_name
        )
        await self.accept()

        # Notify all participants about the new user
        await self.update_participants()

    async def disconnect(self, close_code):
        # Remove user from Redis presence list
        redis_client.srem(f"lobby:{self.lobby_code}:users", self.username)

        # Leave the lobby group
        await self.channel_layer.group_discard(
            self.lobby_group_name,
            self.channel_name
        )

        # Notify all participants about the user leaving
        await self.update_participants()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            # Broadcast a chat message
            message = data.get("message")
            await self.channel_layer.group_send(
                self.lobby_group_name,
                {
                    "type": "chat_message",
                    "message": f"{self.username}: {message}",
                }
            )

    async def update_participants(self):
        # Get all users from Redis
        participants = list(redis_client.smembers(f"lobby:{self.lobby_code}:users"))

        # Notify all clients about updated participants
        await self.channel_layer.group_send(
            self.lobby_group_name,
            {
                "type": "participants_update",
                "participants": participants,
            }
        )

    async def participants_update(self, event):
        participants = event["participants"]
        await self.send(text_data=json.dumps({
            "action": "update_participants",
            "participants": participants,
        }))

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({
            "action": "chat_message",
            "message": message,
        }))

class GamemodeConsumer(LobbyConsumer):
    """
    A base consumer for all gamemode-specific consumers. Inherits logic from LobbyConsumer.
    """
    async def connect(self):
        # Call parent logic
        await super().connect()

        # Additional setup specific to the gamemode
        self.game_group_name = f"game_{self.lobby_code}"
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )

    async def disconnect(self, close_code):
        # Call parent logic
        await super().disconnect()

        # Additional cleanup specific to the gamemode
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == "submit_meme":
            # Handle meme submission
            meme_data = data['meme']
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'action': 'meme_submission',
                    'meme': meme_data
                }
            )

        elif action == "vote_meme":
            # Handle meme voting
            vote_data = data['vote']
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'action': 'vote',
                    'vote': vote_data
                }
            )

        # Call parent receive for common actions
        await super().receive(text_data)

    async def game_message(self, event):
        action = event['action']
        data = event.get('meme') or event.get('vote')

        # Send game-specific messages
        await self.send(text_data=json.dumps({
            'action': action,
            'data': data
        }))
