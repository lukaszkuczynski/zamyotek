from mqtt_node import MqttNode, MqttToSerialNode
import json
import math

SIDE_AREA_PROPORTION = .3335
TOTAL_WID = 1280

class BrainNode(MqttNode):

    def __init__(self):
        center_left = math.floor(0 + (TOTAL_WID * SIDE_AREA_PROPORTION))
        center_right =  math.floor(TOTAL_WID - (TOTAL_WID * SIDE_AREA_PROPORTION))
        self.zones = [
            [0, center_left, "left"],
            [center_left+1, center_right, "stop"],
            [center_right+1, TOTAL_WID, "right"]
        ]
        print(self.zones)
        super().__init__("brain", "/cmd/motor_move", "camera_out")

    def on_message(self, client, userdata, msg):
        print(msg.topic+" zzz "+str(msg.payload))
        center_msg = json.loads(msg.payload)
        print(center_msg)
        center_x = center_msg['center'][0]
        for zone in self.zones:
            if center_x >= zone[0] and center_x < zone[1]:
                move_cmd = {
                    "move_dir": zone[2]
                }
                move_cmd = zone[2]
                self.send(move_cmd)


brain = BrainNode()


mqtt_motor_driver = MqttToSerialNode("motor_mqtt", "/cmd/motor_move", "/tty/USB0", 115200)
