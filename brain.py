from mqtt_node import MqttNode
import json

class BrainNode(MqttNode):

    def __init__(self):
        self.zones = [
            [0, 400, "left"],
            [401, 600, "center"],
            [601, 1000, "right"]
        ]
        super().__init__("brain", "motor_move", "camera_out")

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
                self.send(move_cmd)





brain = BrainNode()
