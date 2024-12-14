from django.test import TestCase
from channels.testing import WebsocketCommunicator
from memeleague.asgi import application
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class GamemodeConsumerTestCase(TestCase):
    def setUp(self):
        self.channel_layer = get_channel_layer()
        self.lobby_code = "GAME123"
        self.group_name = f"game_{self.lobby_code}"

    async def test_gamemode_connection(self):
        communicator = WebsocketCommunicator(application, f"/ws/meme_forge/{self.lobby_code}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Disconnect
        await communicator.disconnect()

    async def test_meme_submission(self):
        communicator = WebsocketCommunicator(application, f"/ws/meme_forge/{self.lobby_code}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Simulate meme submission
        meme_data = {"text": "Test Meme", "author": "User1"}
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                "type": "game_message",
                "action": "meme_submission",
                "meme": meme_data,
            },
        )

        # Receive response
        response = await communicator.receive_json_from()
        self.assertEqual(response["action"], "meme_submission")
        self.assertEqual(response["data"], meme_data)

        # Disconnect
        await communicator.disconnect()
