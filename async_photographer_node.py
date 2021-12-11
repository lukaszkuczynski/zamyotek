from mqtt_node import MqttNode
from pathlib import Path
import yaml
import json
from label_identifier import LabelIdentifier

CAMERA_TAKE_PICTURE_FILE = "camera_take_picture"
TOPIC_TAKE_PHOTO = "/cmd/take_photo"

"""
Tells camera to take photo
"""


class AsyncPhotographerNode(MqttNode):
    def __init__(self):
        super().__init__("async_photographer", "", TOPIC_TAKE_PHOTO)

    def on_message(self, client, userdata, msg):
        self.logger.info(
            "Creating file at %s to tell camera to take photo while in the loop"
            % CAMERA_TAKE_PICTURE_FILE
        )
        Path(CAMERA_TAKE_PICTURE_FILE).touch()


if __name__ == "__main__":
    photographer_node = AsyncPhotographerNode()
