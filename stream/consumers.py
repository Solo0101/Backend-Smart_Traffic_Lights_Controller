# myapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

from webcam import utils
from webcam.constants import PI_COMMUNICATION_GROUP
from webcam.websocket_connection_manager import pi_connection_manager

class PiConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        pi_connection_manager.set_connected(True)
        utils.logger_main.debug(f"WebSocket: Raspberry Pi connected: {self.channel_name}")
        print(f"WebSocket: Raspberry Pi connected: {self.channel_name}")

        await self.channel_layer.group_add(
            PI_COMMUNICATION_GROUP,
            self.channel_name
        )

        await self.send(text_data=json.dumps({
            "connection_type": "websocket",
            "message": "Connection established with Django server!"
        }))

    async def disconnect(self, close_code):
        utils.logger_main.debug(f"WebSocket: Raspberry Pi disconnected: {self.channel_name} with code: {close_code}")
        print(f"WebSocket: Raspberry Pi disconnected: {self.channel_name} with code: {close_code}")
        pi_connection_manager.set_connected(False)

        pass


    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                text_data_json = json.loads(text_data)
                utils.logger_main.debug(f"Received WebSocket message payload: {text_data_json}")

                if isinstance(text_data_json, dict):
                    pi_connection_manager.update_pi_request(text_data_json)
                else:
                    utils.logger_main.warning(f"Received WebSocket message payload is not a dict: {text_data_json}")

                await self.send(text_data=json.dumps({
                    "info": "DEBUG",
                    "message": f"Server received: {text_data_json}"  # Echo back the payload
                }))
            except json.JSONDecodeError:
                utils.logger_main.error(f"Failed to decode JSON from WebSocket: {text_data}")
            except Exception as e:
                utils.logger_main.error(f"Error processing WebSocket message: {e}", exc_info=True)

        elif bytes_data:
            # Process the received binary message (e.g., deserialize from MessagePack)
            utils.logger_main.debug(f"Received binary data: {bytes_data}")
            print(f"Received binary data: {bytes_data}")
            # Example: Echoing back the binary data
            await self.send(bytes_data=bytes_data)

    async def group_send_message(self, event):
        """
        Handles messages sent to the group this consumer is part of.
        The 'type' in channel_layer.group_send should be 'group.send.message'
        """
        message_data = event['data']
        await self.send(text_data=json.dumps(message_data))

piConsumer = PiConsumer()