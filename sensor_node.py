from mqtt_node import SerialToMqttNode
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--port", help="Port to connect to ESP32")
    args = parser.parse_args()

    distance_sensor_node = SerialToMqttNode("distance_node", "/sensor/distance", "/dev/"+args.port, 115200)

