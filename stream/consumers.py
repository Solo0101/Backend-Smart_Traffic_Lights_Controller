# myapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

from webcam import utils
from webcam.constants import PI_COMMUNICATION_GROUP, MOBILE_APP_COMMUNICATION_GROUP
from webcam.websocket_connection_manager import pi_connection_manager

# --- CONSUMER 1: For communication with the Raspberry Pi ---
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

                #TODO: Parse json response from Raspberry Pi and load it into the api_manager

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

# --- CONSUMER 2: For broadcasting intersection status to Flutter clients ---
class MobileAppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # A different group name specifically for status updates

        # Each connected Flutter app joins this group
        await self.channel_layer.group_add(
            MOBILE_APP_COMMUNICATION_GROUP,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket: Flutter client connected: {self.channel_name}")

    async def disconnect(self, close_code):
        # Each Flutter app leaves the group when it disconnects
        await self.channel_layer.group_discard(
            MOBILE_APP_COMMUNICATION_GROUP,
            self.channel_name
        )
        print(f"WebSocket: Flutter client disconnected: {self.channel_name}")

    # This method is called when a status update is broadcast to the group
    async def intersection_status_update(self, event):
        # The event dictionary contains the data we want to send
        message_data = {
            'id': event['id'],
            'status': event['status'],
        }
        # Send the status update to the connected Flutter client
        await self.send(text_data=json.dumps(message_data))



piConsumer = PiConsumer()