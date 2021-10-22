import paho.mqtt.client as mqtt
import json


class MqttNode:

    def __init__(self, nodename, topic_pub, topic_sub, hostname="localhost", port=1883) -> None:
        self.nodename = nodename
        self.hostname = hostname
        self.port = port
        self.topic_pub = topic_pub
        self.topic_sub = topic_sub
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(hostname, port, 60)
        if topic_sub != "":
            self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        if self.topic_sub != "":
            self.client.subscribe(self.topic_sub)
            self.send("connected!")
        print("connected")

    def on_message(self, client, userdata, msg):
        msg['sender'] = self.nodename
        print(msg.topic+" "+str(msg.payload))

    def send(self, message):
        if isinstance(message, str):
            text_message = message
            message = {}
            message['msg'] = text_message
        elif not isinstance(message, dict):
            raise Exception("Message should be dict!")
        message['sender'] = self.nodename
        self.client.publish(self.topic_pub, json.dumps(message))


#node = MqttNode("testnode", "/test/pub", "/test/sub")
