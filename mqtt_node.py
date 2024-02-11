import json
import logging
import os
from time import sleep

import paho.mqtt.client as mqtt
import serial


def get_client():
    client = mqtt.Client(hostname="localhost", port=1883)
    client.connect()
    return client


class MqttNode:
    def __init__(
        self,
        nodename,
        topic_pub,
        topic_sub,
        hostname="localhost",
        port=1883,
        log_folder="logs",
        autostart_listening=True,
    ) -> None:
        self.nodename = nodename
        self.logger = self.__setup_logger(log_folder)
        self.hostname = hostname
        self.port = port
        self.topic_pub = topic_pub
        self.topic_sub = topic_sub
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(hostname, port, 60)
        self.reload_settings()
        if autostart_listening:
            self.start_listening()

    def start_listening(self):
        if self.topic_sub != "":
            self.logger.info("Listen forever in loop...")
            self.client.loop_forever()

    def reload_settings(self):
        pass

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info("Connected with result code " + str(rc))
        if self.topic_sub != "":
            if isinstance(self.topic_sub, list):
                topics = [(name, 1) for name in self.topic_sub]
            else:
                topics = self.topic_sub
            self.client.subscribe(topics)
            self.logger.info("subscribed to %s" % self.topic_sub)

    def on_message(self, client, userdata, msg):
        self.logger.debug(str(msg.payload))

    def send(self, message):
        self.send_to(message, self.topic_pub)

    def send_to(self, message, topic):
        if isinstance(message, str):
            text_message = message
            message = {}
            message["msg"] = text_message
            message["topic"] = topic
        elif not isinstance(message, dict):
            raise Exception("Message should be dict or str but is %s!" % type(message))
        message["sender"] = self.nodename
        MAX_RETRIES = 5
        retries = 1
        while retries <= MAX_RETRIES:
            ret = self.client.publish(topic, json.dumps(message), qos=0)
            # self.logger.info(ret.rc)
            if ret.rc != 0:
                self.logger.warn(
                    "Publish..... %s, return_val %s", json.dumps(message), ret.rc
                )
                sleep(0.5)
                retries += 1
            else:
                break
        # self.logger.info("retries %d", retries)
        if retries >= MAX_RETRIES:
            self.logger.error("Maximum number of retries while sending MQTT message!")
            self.client.reconnect()

    def __setup_logger(self, log_folder):
        log_filename = os.path.join(log_folder, self.nodename + ".log")
        logger = logging.getLogger(self.nodename)
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler(log_filename)
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # add the handlers to logger
        logger.addHandler(ch)
        logger.addHandler(fh)
        return logger


class MqttToSerialNode(MqttNode):
    def __init__(self, nodename, topic_sub, port_name, baudrate):
        self.serial_port = self.__create_serial(port_name, baudrate)
        super().__init__(nodename, "", topic_sub)
        self.port_name = port_name
        self.baudrate = baudrate

    def __create_serial(self, port_name, baudrate):
        return serial.Serial(
            port=port_name,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
        )

    def on_message(self, client, userdata, msg):
        self.logger.debug(msg.payload)
        command = json.loads(msg.payload)
        self.logger.debug("Writing to serial command = %s", command)
        command_encoded = (command["msg"] + "\n").encode("ascii")
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
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
        )

    def __start_listening(self):
        while True:
            line_bytes = self.serial_port.readline()
            line = line_bytes.decode("UTF-8")
            self.logger.debug("Received on serial line = %s", line)
            if line.startswith("{"):
                line_dict = json.loads(line)
                self.send(line_dict)
