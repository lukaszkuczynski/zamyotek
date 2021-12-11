from logging import log
from mqtt_node import MqttNode
import json
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir


TOPIC_CMD_SPEAK = "/cmd/speak"
TOPIC_NOTIFY_SPOKEN = "/notify/spoken"


class SpeakNode(MqttNode):
    def __init__(self):
        super().__init__(
            "rekognition",
            TOPIC_NOTIFY_SPOKEN,
            TOPIC_CMD_SPEAK,
            autostart_listening=False,
        )
        session = Session(profile_name="zamyotek")
        self.polly = session.client("polly")
        self.start_listening()

    def __call_polly(self, text):
        response = self.polly.synthesize_speech(
            Text=text, OutputFormat="mp3", VoiceId="Joanna"
        )
        return response

    def __play_using_temp_file(self, polly_response):
        if "AudioStream" in polly_response:
            # Note: Closing the stream is important because the service throttles on the
            # number of parallel connections. Here we are using contextlib.closing to
            # ensure the close method of the stream object will be called automatically
            # at the end of the with statement's scope.
            path_to_save_temp_file = os.path.join(gettempdir(), "zamyotek_speech.mp3")
            with closing(polly_response["AudioStream"]) as stream:
                output = path_to_save_temp_file
                try:
                    # Open a file for writing the output as a binary stream
                    with open(output, "wb") as file:
                        file.write(stream.read())
                except IOError as error:
                    self.logger.error(error)
                    # Could not write to file, exit gracefully
                    print(error)
                    sys.exit(-1)
            # Play the audio using the platform's default player
            if sys.platform == "win32":
                os.startfile(output)
            else:
                # The following works on macOS and Linux. (Darwin = mac, xdg-open = linux).
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, output])

    def on_message(self, client, userdata, msg):
        speak_msg = json.loads(msg.payload)
        object_class = speak_msg["msg"]
        text_to_speak = "I can see %s" % object_class
        response = self.__call_polly(text_to_speak)
        self.logger.info(response)
        self.logger.info("I will speak... %s", speak_msg)
        self.__play_using_temp_file(response)
        self.send("spoken")


if __name__ == "__main__":
    speak_node = SpeakNode()
