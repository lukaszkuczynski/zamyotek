from mqtt_node import MqttNode, MqttToSerialNode
import json
import math
from datetime import datetime
from common_objects import AnyObjectStack, DistanceStack

SIDE_AREA_PROPORTION = .3335
TOTAL_WID = 1280
CLOSE_GATE_DISTANCE = 30

TOPIC_SENSOR_DISTANCE = "/sensor/distance"
TOPIC_CAMERA = "camera_out"
TOPIC_MOTOR = "/cmd/motor_move"
TURNING_TIME_NOOP = 1000
TOO_CLOSE_OBJECT_WIDTH = 800

class BrainNode(MqttNode):

    def __init__(self):
        center_left = math.floor(0 + (TOTAL_WID * SIDE_AREA_PROPORTION))
        center_right =  math.floor(TOTAL_WID - (TOTAL_WID * SIDE_AREA_PROPORTION))
        self.zones = [
            [0, center_left, "left"],
            [center_left+1, center_right, "central"],
            [center_right+1, TOTAL_WID, "right"]
        ]
        print(self.zones)
        self.distance_stack = DistanceStack(ms_ttl=2000, max_val=1000)
        self.turning_time_noop = TURNING_TIME_NOOP
        self.last_turning_time = datetime.now()
        self.motor_stack = AnyObjectStack(ms_ttl = 2000)
        super().__init__("brain", TOPIC_MOTOR, [TOPIC_CAMERA, TOPIC_SENSOR_DISTANCE])


    def on_message(self, client, userdata, msg):
        #print(msg.topic+" - "+str(msg.payload))
        if msg.topic == TOPIC_CAMERA:
            center_msg = json.loads(msg.payload)
            print(center_msg)
            center_x = center_msg['center'][0]
            width = center_msg['width']
            for zone in self.zones:
                if center_x >= zone[0] and center_x < zone[1]:
                    zone_name = zone[2]
                    if zone_name in ['left','right']:
                        if ((datetime.now() - self.last_turning_time).total_seconds() * 1000) < self.turning_time_noop:
                            print("Skipped")
                            move_dir = 'stop'
                        else:
                            self.last_turning_time = datetime.now()
                            move_dir = zone_name
                    else:
                        # center, we have to decide on the basis of distance
                        # default decision is to go ahead
                        move_dir = 'ahead'
                        distance = self.distance_stack.avg_distance()
                        if distance is not None:
                            # when distance is small then we should stop
                            if distance < CLOSE_GATE_DISTANCE:
                                move_dir = 'stop'
                        if width > TOO_CLOSE_OBJECT_WIDTH:
                            move_dir = 'stop'
                    self.motor_stack.push(move_dir)
                    self.send(move_dir)
            print(f"avg distance from stack is {self.distance_stack.avg_distance()}")
            print(f"object closeness width perc is {width / TOO_CLOSE_OBJECT_WIDTH}")
        elif msg.topic == TOPIC_SENSOR_DISTANCE:
           # print("msg on topic DISTANCE")
            distance_msg = json.loads(msg.payload)
            distance_val = float(distance_msg['distance'])
            self.distance_stack.push(distance_val)
            if not self.motor_stack.most_common():
                self.send('stop')


brain = BrainNode()


mqtt_motor_driver = MqttToSerialNode("motor_mqtt", "/cmd/motor_move", "/tty/USB0", 115200)
