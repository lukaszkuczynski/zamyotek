import paho.mqtt.client as mqtt
import json
import serial


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
            if isinstance(self.topic_sub, list):
                topics = [(name,1) for name in self.topic_sub]
            else:
                topics = self.topic_sub
            self.client.subscribe(topics)
            print("subscribed to %s" % self.topic_sub)
        print("connected")

    def on_message(self, client, userdata, msg):
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



class MqttToSerialNode(MqttNode):

    def __init__(self, nodename, topic_sub, port_name, baudrate):
        self.serial_port = self.__create_serial(port_name, baudrate)
        super().__init__(nodename, "", topic_sub)
        self.port_name = port_name
        self.baudrate = baudrate


    def __create_serial(self, port_name, baudrate):
        return serial.Serial(
            port=port_name, 
            baudrate = baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

    def on_message(self, client, userdata, msg):
        command = json.loads(msg.payload)
        print(command)
        command_encoded = (command['msg']+"\n").encode("ascii")
        self.serial_port.write(command_encoded)


class SerialToMqttNode(MqttNode):

    def __init__(self, nodename, topic_pub, port_name, baudrate):
        self.serial_port = self.__create_serial(port_name, baudrate)
        super().__init__(nodename, topic_pub, "")
        self.port_name = port_name
        self.baudrate = baudrate
        self.__start_listening()


    def __create_serial(self, port_name, baudrate):
        return serial.Serial(
            port=port_name, 
            baudrate = baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

    def __start_listening(self):
        while True:
            line = self.serial_port.readline()
            print(line)
            line_dict = json.loads(line)
            self.send(line_dict)

