import json
import sys
from pathlib import Path

import yaml

from label_identifier import LabelIdentifier
from mqtt_node import MqttNode

TOPIC_TAKE_PHOTO = "/cmd/take_photo"

"""
Tells camera to take photo
"""


class AsyncPhotographerNode(MqttNode):
    def __init__(self, async_flag_filepath):
        self.async_flag_filepath = async_flag_filepath
        super().__init__("async_photographer", "", TOPIC_TAKE_PHOTO, autostart_listening=False)
        self.logger.info(f"Will touch the path = {async_flag_filepath}")
        self.start_listening()

    def on_message(self, client, userdata, msg):
        
        self.logger.info(
            "Creating file at %s to tell camera to take photo while in the loop"
            % self.async_flag_filepath
        )
        result = Path(self.async_flag_filepath).touch()



if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        raise Exception("Expecting to have a path for the file to touch")
    async_flag_filepath = args[1]
    photographer_node = AsyncPhotographerNode(async_flag_filepath)
