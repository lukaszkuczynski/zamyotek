from mqtt_node import MqttNode
import json
import boto3

TOPIC_NOTIFY_PHOTO_TAKEN = "/notify/photo"
TOPIC_NOTIFY_OBJECT_RECOGNIZED = "/notify/object_recognized"


class RekognitionNode(MqttNode):
    def __init__(self):
        super().__init__(
            "rekognition", TOPIC_NOTIFY_OBJECT_RECOGNIZED, TOPIC_NOTIFY_PHOTO_TAKEN
        )

    def recognize_from_path(self, picture_path):
        client = boto3.client("rekognition")
        with open(picture_path, "rb") as image:
            response = client.detect_labels(Image={"Bytes": image.read()})
        labels_and_confidence = [
            (label["Name"], label["Confidence"]) for label in response["Labels"]
        ]
        self.logger.debug(labels_and_confidence)
        return labels_and_confidence

    def on_message(self, client, userdata, msg):
        camera_photo_msg = json.loads(msg.payload)
        picture_path = camera_photo_msg["msg"]
        self.logger.info("Received picture on %s", picture_path)
        labels_and_confidence = self.recognize_from_path(picture_path)
        object_class = labels_and_confidence[0][0]
        self.logger.info(
            "Choosing label - blunt shot for the 1st one : '%s'", object_class
        )
        self.send(object_class)


if __name__ == "__main__":
    rekognition_node = RekognitionNode()
