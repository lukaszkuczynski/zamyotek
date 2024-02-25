import json
import os
import subprocess
import sys
import wave
from contextlib import closing
from logging import log
from tempfile import gettempdir
from time import sleep

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError

from mqtt_node import MqttNode

TOPIC_CMD_SPEAK = "/cmd/speak"
TOPIC_NOTIFY_SPOKEN = "/notify/spoken"

DEBUG_MODE_NO_AWS = False

class SpeakNode(MqttNode):
    def __init__(self):
        super().__init__(
            "speak",
            TOPIC_NOTIFY_SPOKEN,
            TOPIC_CMD_SPEAK,
            autostart_listening=False,
        )
        session = Session(profile_name="default")
        self.polly = session.client("polly")
        self.start_listening()

    def __call_polly(self, text, lang):
        response = self.polly.synthesize_speech(
            Text=text, OutputFormat="pcm", VoiceId="Matthew", LanguageCode=lang
        )
        return response
    
    def __play_wave_at_path(self, wav_path):
        return subprocess.call(["aplay", "--device","sysdefault:CARD=Device", wav_path])


    def __play_using_temp_file(self, polly_response):
        if "AudioStream" in polly_response:
            # Note: Closing the stream is important because the service throttles on the
            # number of parallel connections. Here we are using contextlib.closing to
            # ensure the close method of the stream object will be called automatically
            # at the end of the with statement's scope.
            path_to_save_temp_file = os.path.join(gettempdir(), "zamyotek_speech.wav")
            with closing(polly_response["AudioStream"]) as stream:
                output = path_to_save_temp_file
                try:
                    # Open a file for writing the output as a binary stream
                    with wave.open(output, 'wb') as wav_file:
                        wav_file.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
                        wav_file.writeframes(stream.read())
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
                return self.__play_wave_at_path(output)

    def on_message(self, client, userdata, msg):
        speak_msg = json.loads(msg.payload)
        message_from_openai = speak_msg["msg"]
        lang = message_from_openai.split("|")[0]
        text_from_openai = message_from_openai.split("|")[1]
        # text_to_speak = "I can see %s" % object_class
        first_sentence = text_from_openai.partition(".")[0]
        text_to_speak = first_sentence
        lang_map = {
            "english": "en-GB",
            "french": "fr-FR",
            "polish": "pl-PL",
            "chinese": "cmn-CN",
            "spanish": "es-ES",
        }
        polly_lang = lang_map.get(lang, "en-GB")
        self.logger.info("Got lanugage %s", lang)
        if DEBUG_MODE_NO_AWS:
            # wav_path = os.path.join(gettempdir(), "zamyotek_speech.wav")
            wav_path = "/home/lukjetson/prj/jetson-voice/data/audio/command_yes.wav"
            self.__play_wave_at_path(wav_path)
        else:
            response = self.__call_polly(text_to_speak, polly_lang)
            self.logger.info(response)
            self.logger.info("I will speak... %s", speak_msg)
            result = self.__play_using_temp_file(response)
            if result == 0:
                self.send("spoken")
            else:
                self.send("error")
                sleep(.5)
                self.on_message(client, userdata, msg)


if __name__ == "__main__":
    speak_node = SpeakNode()
