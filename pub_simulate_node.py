from mqtt_node import MqttNode
import time
from argparse import ArgumentParser
import json

class SimPubNode(MqttNode):

    def __init__(self, topic, key, value):
        nodename = "simulate_pub_for_"+topic
        super().__init__(nodename, topic, "")
        self.key = key
        self.value = value
        self.__loop()

    def __loop(self):
        while True:
            value = self.value
            if isinstance(value, str) and "{" in value:
                msg = json.loads(value)
            else:
                msg = {self.key: value}
            self.send(msg)
            time.sleep(1)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--value", default=1)
    parser.add_argument("--topic", default="simulate")
    args = parser.parse_args()
    value = args.value
    if value.isnumeric():
        value = float(value)
    sim = SimPubNode(args.topic, "msg", value)
