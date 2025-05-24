# myapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PiConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # self.room_name = self.scope['url_route']['kwargs']['room_name'] # Example if using URL routing with params
        # self.room_group_name = f'chat_{self.room_name}'
        # await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket: Raspberry Pi connected: {self.channel_name}")
        await self.send(text_data=json.dumps({
            "connection_type": "websocket",
            "message": "Connection established with Django server!"
        }))

    async def disconnect(self, close_code):
        print(f"WebSocket: Raspberry Pi disconnected: {self.channel_name} with code: {close_code}")
        # await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        pass  # Add any cleanup logic here


    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json.get("message")
            # Process the received text message
            print(f"Received text message: {message}")
            await self.send(text_data=json.dumps({
                "connection_type": "echo_message",
                "message": f"Server received: {message}"
            }))
        elif bytes_data:
            # Process the received binary message (e.g., deserialize from MessagePack)
            print(f"Received binary data: {bytes_data}")
            # Example: Echoing back the binary data
            await self.send(bytes_data=bytes_data)