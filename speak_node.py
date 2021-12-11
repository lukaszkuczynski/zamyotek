from mqtt_node import MqttNode
import json

TOPIC_CMD_SPEAK = "/cmd/speak"
TOPIC_NOTIFY_SPOKEN = "/notify/spoken"


class SpeakNode(MqttNode):
    def __init__(self):
        super().__init__("rekognition", TOPIC_NOTIFY_SPOKEN, TOPIC_CMD_SPEAK)

    def on_message(self, client, userdata, msg):
        speak_msg = json.loads(msg.payload)
        self.logger.info("I will speak... %s", speak_msg)
        self.send("spoken")


if __name__ == "__main__":
    speak_node = SpeakNode()
