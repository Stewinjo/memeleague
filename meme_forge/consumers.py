import json
from lobby.consumers import GamemodeConsumer

class MemeForgeConsumer(GamemodeConsumer):
    """
    Consumer for the MemeForge gamemode.
    Inherits logic from GamemodeConsumer.
    """
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == "submit_meme":
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
            vote_data = data['vote']
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'game_message',
                    'action': 'vote',
                    'vote': vote_data
                }
            )

        # Call parent receive for additional actions
        await super().receive(text_data)
