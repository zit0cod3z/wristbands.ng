import json
from channels.generic.websocket import AsyncWebsocketConsumer


class CheckInConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer — each event has its own group.
    When a scan happens the view broadcasts to this group
    so every connected dashboard/scanner updates in real time.
    """

    async def connect(self):
        self.event_pk = self.scope['url_route']['kwargs']['event_pk']
        self.group_name = f'checkin_{self.event_pk}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from group (broadcast from view)
    async def checkin_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
