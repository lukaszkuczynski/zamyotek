from mqtt_node import MqttToSerialNode
from argparse import ArgumentParser

TOPIC_CMD_SERVO_HEAD = "/cmd/servo/head_position"


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", help="Port to connect to ESP32")
    args = parser.parse_args()

    mqtt_motor_driver = MqttToSerialNode(
        "servo_mqtt",
        ["/cmd/servo_gate", TOPIC_CMD_SERVO_HEAD],
        "/dev/" + args.port,
        115200,
    )
