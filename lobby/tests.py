from django.test import TestCase
from channels.testing import WebsocketCommunicator
from memeleague.asgi import application
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class LobbyConsumerTestCase(TestCase):
    def setUp(self):
        self.channel_layer = get_channel_layer()
        self.lobby_code = "TEST123"
        self.group_name = f"lobby_{self.lobby_code}"

    async def test_lobby_connection(self):
        communicator = WebsocketCommunicator(application, f"/ws/lobby/{self.lobby_code}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Disconnect
        await communicator.disconnect()

    async def test_participant_updates(self):
        # Create communicator
        communicator = WebsocketCommunicator(application, f"/ws/lobby/{self.lobby_code}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Simulate sending participant updates
        participants = [{"username": "TestUser"}]
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                "type": "participants_update",
                "participants": participants,
            },
        )

        # Receive response
        response = await communicator.receive_json_from()
        self.assertEqual(response["action"], "update_participants")
        self.assertEqual(response["participants"], participants)

        # Disconnect
        await communicator.disconnect()
