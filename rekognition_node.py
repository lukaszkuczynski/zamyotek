from mqtt_node import MqttNode
import json
import boto3
from abc import abstractclassmethod

TOPIC_NOTIFY_PHOTO_TAKEN = "/notify/photo"
TOPIC_NOTIFY_OBJECT_RECOGNIZED = "/notify/object_recognized"


class RekognitionNode(MqttNode):
    def __init__(self):
        self.label_strategy = LabelChoiceRememberingStrategy()
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
        object_class = self.label_strategy.choose_label(labels_and_confidence)
        self.logger.info(
            "Choosing label - (strategy %s) : '%s'",
            type(self.label_strategy),
            object_class,
        )
        self.send(object_class)


class LabelChoiceStrategy:
    @abstractclassmethod
    def choose_label(self, labels_and_confidence):
        pass


class LabelChoiceStrategyFirst(LabelChoiceStrategy):
    def choose_label(self, labels_and_confidence):
        return labels_and_confidence[0][0]


class LabelChoiceRememberingStrategy(LabelChoiceStrategy):
    def __init__(self):
        self.chosen_labels = set()

    def choose_label(self, labels_and_confidence):
        labels_only = [tup[0] for tup in labels_and_confidence]
        for label in labels_only:
            if label in self.chosen_labels:
                continue
            else:
                self.chosen_labels.add(label)
                return label
        # last resort, all labels are there, we choose the 1st one
        return labels_only[0]


if __name__ == "__main__":
    rekognition_node = RekognitionNode()
