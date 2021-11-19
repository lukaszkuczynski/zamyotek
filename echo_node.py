from platform import machine
from mqtt_node import MqttNode




class EchoNode(MqttNode):


    def on_message(self, client, userdata, msg):
        self.logger.info("on message")
        return super().on_message(client, userdata, msg)


if __name__ == '__main__':
    echo_node = EchoNode("echo", "", "/echo")