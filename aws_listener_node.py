from mqtt_node import MqttNode
from pathlib import Path
import yaml
import json
from label_identifier import LabelIdentifier

TOPIC_BRING_ME = "/zamyotek/cmd/bring_me"
CAMERA_RELOAD_FILE = "camera_change_settings"
CONFIG_PATH = "config.yaml"
TOPIC_RELOAD_SETTINGS = "/cmd/reload_settings"
LABELS_PATH = "/usr/local/bin/networks/SSD-Mobilenet-v2/ssd_coco_labels.txt"

"""
Listens to AWS IoT topics and reconfigures if needed.
One case is when Alexa skill is triggered, then searching for some object begins..
"""
class AwsListenerNode(MqttNode):

    def __init__(self):
        filename = LABELS_PATH
        self.identifier = LabelIdentifier(filename)
        super().__init__("aws_listener", TOPIC_RELOAD_SETTINGS, [TOPIC_BRING_ME])

    def on_message(self, client, userdata, msg):
        if msg.topic == TOPIC_BRING_ME:
            # here we need to "communicate" with camera node, that is triggered when 
            # a file is placed on the hard disk
            # after it data is reloaded
            Path(CAMERA_RELOAD_FILE).touch()
            with open(CONFIG_PATH, "r") as stream:
                config = yaml.safe_load(stream)
                payload_json = json.loads(msg.payload)
                new_class = payload_json["bring_me_class"]
                if new_class not in self.identifier.all_labels():
                    self.logger.warn(f"Received {new_class} which is not a known label. Class change aborted!")
                    return 1
                self.logger.info(f"Changing classes from {config['camera']['classes_search']} to {new_class}")
                config['camera']['classes_search'] = [new_class]
            with open(CONFIG_PATH, "w") as write_stream:
                yaml.dump(config, write_stream)
            self.send("reload_object_classes")


if __name__ == '__main__':
    aws_listener_node = AwsListenerNode()