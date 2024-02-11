import base64
import json
import os
from abc import abstractclassmethod

import boto3
import requests

from mqtt_node import MqttNode

TOPIC_NOTIFY_PHOTO_TAKEN = "/notify/photo"
TOPIC_NOTIFY_OBJECT_RECOGNIZED = "/notify/object_recognized"

DEBUG_MODE_NO_AWS = True


class OpenAiVisionNode(MqttNode):
    def __init__(self, api_key):
        self.api_key = api_key
        super().__init__(
            "openai_vision", TOPIC_NOTIFY_OBJECT_RECOGNIZED, TOPIC_NOTIFY_PHOTO_TAKEN
        )

    def __choose_choice(self, choices):
        return choices[0]

    def get_picture_message(self, picture_path):
        base64_image = self.__encode_image(picture_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": "Tell me in one sentence what do you see?"
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                    }
                ]
                }
            ],
            "max_tokens": 100
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        print(response.json())
        choice = self.__choose_choice(response.json()['choices'])
        return choice['message']['content']


    def __encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    def on_message(self, client, userdata, msg):
        camera_photo_msg = json.loads(msg.payload)
        picture_path = camera_photo_msg["msg"]

        message = self.get_picture_message(picture_path)

        self.send(message)



if __name__ == "__main__":
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    openai_node = OpenAiVisionNode(OPENAI_API_KEY)
