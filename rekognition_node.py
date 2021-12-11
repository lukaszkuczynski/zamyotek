from mqtt_node import MqttNode
import json

TOPIC_NOTIFY_PHOTO_TAKEN = "/notify/photo"
TOPIC_NOTIFY_OBJECT_RECOGNIZED = "/notify/object_recognized"


class RekognitionNode(MqttNode):
    def __init__(self):
        super().__init__(
            "rekognition", TOPIC_NOTIFY_OBJECT_RECOGNIZED, TOPIC_NOTIFY_PHOTO_TAKEN
        )

    def recognize_from_path(self, picture_path):
        return "banana"

    def on_message(self, client, userdata, msg):
        camera_photo_msg = json.loads(msg.payload)
        picture_path = camera_photo_msg["msg"]
        self.logger.info("Received picture on %s", picture_path)
        object_class = self.recognize_from_path(picture_path)
        self.send(object_class)


if __name__ == "__main__":
    rekognition_node = RekognitionNode()
