import json
from channels.generic.websocket import AsyncWebsocketConsumer


class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.lobby_code = self.scope['url_route']['kwargs']['lobby_code']
        self.group_name = f"lobby_{self.lobby_code}"

        # Join the lobby group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Notify others about the new participant
        await self.broadcast_participants_update()

    async def disconnect(self, close_code):
        # Leave the lobby group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        # Notify others about the updated participant list
        await self.broadcast_participants_update()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == "update_participants":
            # Optionally handle participant updates here
            pass

    async def broadcast_participants_update(self):
        """
        Fetch the current list of participants from a data source and broadcast it to the group.
        """
        # Replace with actual logic to fetch participants (e.g., from Redis)
        participants = self.get_current_participants()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "lobby_update",
                "participants": participants,
            }
        )

    def get_current_participants(self):
        """
        Fetch the current participants. Replace with logic to retrieve participants from your data source.
        """
        # Dummy implementation
        return [
            {"name": "Player1", "profile_pic": "/static/images/player1.png"},
            {"name": "Player2", "profile_pic": "/static/images/player2.png"},
        ]

    async def lobby_update(self, event):
        """
        Send participant list updates to clients.
        """
        participants = event['participants']
        await self.send(text_data=json.dumps({
            "action": "update_participants",
            "participants": participants,
        }))

    async def game_start(self, event):
        """
        Notify clients to transition to the game interface.
        """
        redirect_url = event['redirect_url']
        await self.send(text_data=json.dumps({
            "action": "game_start",
            "redirect_url": redirect_url,
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
