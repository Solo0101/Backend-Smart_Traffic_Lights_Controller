import threading
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from webcam import utils
from webcam.constants import PI_COMMUNICATION_GROUP
from webcam.utils import logger_background


def send_pi_request(message_payload):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        PI_COMMUNICATION_GROUP,
        {
            "type": "group.send.message",  # This will call group_send_message in the consumer
            "data": message_payload
        }
    )
    logger_background.info(f"Sent message to group {PI_COMMUNICATION_GROUP}: {message_payload}")


class PiConnectionStatusManager:
    def __init__(self):
        self._is_connected = False
        self._pi_request_data = {
            "STATE": "", "NSG": 0, "NSY": 0, "EWG": 0, "EWY": 0
        }
        self._lock = threading.Lock()
        self.logger = utils.logger_background

    def set_connected(self, status: bool):
        with self._lock:
            if self._is_connected != status:  # Log only on change
                self.logger.info(f"Pi Connection Status changed to: {status}")
            self._is_connected = status
            if not status:
                # Optionally reset pi_request_data when disconnected
                self.logger.info("Pi disconnected, resetting pi_request_data.")
                self._reset_pi_request_data_internal()

    def is_connected(self) -> bool:
        with self._lock:
            return self._is_connected

    def update_pi_request(self, received_message: dict):
        with self._lock:
            updated_keys = []
            if "STATE" in received_message:
                self._pi_request_data["STATE"] = received_message["STATE"]
                updated_keys.append("STATE")
            if "NSG" in received_message:
                self._pi_request_data["NSG"] = received_message["NSG"]
                updated_keys.append("NSG")
            if "EWG" in received_message:
                self._pi_request_data["EWG"] = received_message["EWG"]
                updated_keys.append("EWG")

            # Handle NSY and EWY with the specific conditional logic:
            # They are only updated if their current value is 0.
            if "NSY" in received_message and self._pi_request_data["NSY"] == 0:
                self._pi_request_data["NSY"] = received_message["NSY"]
                updated_keys.append("NSY")
            if "EWY" in received_message and self._pi_request_data["EWY"] == 0:
                self._pi_request_data["EWY"] = received_message["EWY"]
                updated_keys.append("EWY")

            if updated_keys:
                self.logger.debug(
                    f"Pi request data updated for keys: {updated_keys}. New data: {self._pi_request_data}")

    def get_pi_request_data(self) -> dict:
        with self._lock:
            return self._pi_request_data.copy()

    def _reset_pi_request_data_internal(self):
        self._pi_request_data = {
            "STATE": "", "NSG": 0, "NSY": 0, "EWG": 0, "EWY": 0
        }


pi_connection_manager = PiConnectionStatusManager()