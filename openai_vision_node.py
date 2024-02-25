import base64
import json
import os
import struct
import subprocess
import wave
from abc import abstractclassmethod
from datetime import datetime
from time import sleep

import boto3
import requests
from pvrecorder import PvRecorder

from mqtt_node import MqttNode

TOPIC_NOTIFY_PHOTO_TAKEN = "/notify/photo"
TOPIC_NOTIFY_OBJECT_RECOGNIZED = "/notify/object_recognized"
TOPIC_CMD_SERVO_HEAD = "/cmd/servo/head_position"

RECORDING_FOLDER = "/tmp"

DEBUG_MODE_NO_AWS = True
NO_OF_SECONDS_RECORDING = 5
DEFAULT_PROMPT = "Tell me in one sentence what do you see?"

import logging

logger = logging.getLogger()


class OpenAiVisionNode(MqttNode):
    def __init__(self, api_key):
        self.api_key = api_key
        super().__init__(
            "openai_vision", TOPIC_NOTIFY_OBJECT_RECOGNIZED, TOPIC_NOTIFY_PHOTO_TAKEN, autostart_listening=True
        )

    def __choose_choice(self, choices):
        return choices[0]

    def get_picture_message(self, picture_path, prompt=DEFAULT_PROMPT):
        base64_image = self.__encode_image(picture_path)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.logger.debug("Sending picture from %s top OpenAI", picture_path)
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 200,
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )
        response_json = response.json()
        self.logger.debug(response_json)
        if "error" in response_json:
            self.logger.error(response_json["error"]["message"])
            return response_json["error"]["message"]
        else:
            choice = self.__choose_choice(response_json["choices"])
            return choice["message"]["content"]

    def __record_message(self, no_of_seconds):
        frequency = 8000
        device_id = 1
        all_frames_count = no_of_seconds * frequency * 2
        frame_length = 512
        no_of_frames = all_frames_count
        recorder = PvRecorder(frame_length, device_id)
        audio = []
        recording_path = os.path.join(
            RECORDING_FOLDER,
            f"ttbot_recording_{datetime.isoformat(datetime.now())}.wav",
        )
        self.logger.debug("Start recording...")
        recorder.start()
        current_frame_recorded_count = 0
        while current_frame_recorded_count < all_frames_count:
            frame = recorder.read()
            audio.extend(frame)
            current_frame_recorded_count += len(frame)
        recorder.stop()
        self.logger.debug("Recording finished.")
        with wave.open(recording_path, "w") as f:
            nchannels = 2
            sampwidth = 2
            f.setparams((nchannels, sampwidth, frequency, no_of_frames, "NONE", "NONE")) # pylint:disable=no-member
            f.writeframes(struct.pack("h" * len(audio), *audio))# pylint:disable=no-member
        recorder.delete()
        self.logger.info("Recorded file on %s", recording_path)
        return recording_path

    def recognize_speech(self):
        recording_path = self.__record_message(NO_OF_SECONDS_RECORDING)
        # recording_path = "/tmp/ttbot_recording.wav"

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "whisper-1",
            "response_format": "verbose_json"
        }
        self.logger.debug("Will request transcripion from OpenAI")
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            data=payload,
            files=dict(file=(recording_path, open(recording_path, 'rb'), "audio/wav")),
        )
        self.logger.debug("Transcription finished")
        response_json = response.json()
        transcribed_text = response_json['text']
        language = response_json['language']
        self.logger.info("Text transcribed is '%s'", transcribed_text)
        return transcribed_text, language

    def __encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
        

    def on_message(self, client, userdata, msg):
        camera_photo_msg = json.loads(msg.payload)
        picture_path = camera_photo_msg["msg"]
        self.change_color("blue")
        prompt, language = self.recognize_speech()
        if len(prompt) < 4:
            logger.warning("I heard almost nothing, falling back to the default prompt : '%s'", DEFAULT_PROMPT)
            prompt = DEFAULT_PROMPT
        self.change_color("red")
        message = self.get_picture_message(picture_path, prompt)
        print(message)
        self.send(language+"|"+message)


if __name__ == "__main__":
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    openai_node = OpenAiVisionNode(OPENAI_API_KEY)

