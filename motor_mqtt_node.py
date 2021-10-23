from mqtt_node import MqttToSerialNode
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--port", help="Port to connect to ESP32")
    args = parser.parse_args()

    mqtt_motor_driver = MqttToSerialNode("motor_mqtt", "/cmd/motor_move", "/dev/"+args.port, 115200)

