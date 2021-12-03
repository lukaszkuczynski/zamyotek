from mqtt_node import MqttNode
from pathlib import Path
import yaml
import json

TOPIC_BRING_ME = "/cmd/zamyotek/bring_me"
CAMERA_RELOAD_FILE = "camera_change_settings"
CONFIG_PATH = "config.yaml"

"""
Listens to AWS IoT topics and reconfigures if needed.
One case is when Alexa skill is triggered, then searching for some object begins..
"""
class AwsListenerNode(MqttNode):

    def __init__(self):
        super().__init__("aws_listener", "" , [TOPIC_BRING_ME])

    def on_message(self, client, userdata, msg):
        if msg.topic == TOPIC_BRING_ME:
            # here we need to "communicate" with camera node, that is triggered when 
            # a file is placed on the hard disk
            # after it data is reloaded

            Path(CAMERA_RELOAD_FILE).touch()
            with open(CONFIG_PATH, "r") as stream:
                config = yaml.safe_load(stream)
                payload_json = json.loads(msg.payload)
                config['camera']['classes_search'] = payload_json["classes"]
            with open(CONFIG_PATH, "w") as write_stream:
                yaml.dump(config, write_stream)


if __name__ == '__main__':
    aws_listener_node = AwsListenerNode()