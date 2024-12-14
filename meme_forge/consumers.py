from lobby.consumers import LobbyConsumer

class MemeForgeConsumer(LobbyConsumer):
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data['action']

        if action == "submit_meme":
            meme_data = data['meme']
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'meme_submission',
                    'meme': meme_data
                }
            )
        elif action == "vote_meme":
            vote_data = data['vote']
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'vote_cast',
                    'vote': vote_data
                }
            )

    async def meme_submission(self, event):
        await self.send(text_data=json.dumps({
            'action': 'meme_submission',
            'meme': event['meme']
        }))

    async def vote_cast(self, event):
        await self.send(text_data=json.dumps({
            'action': 'vote',
            'vote': event['vote']
        }))
