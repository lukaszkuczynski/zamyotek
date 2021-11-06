from mqtt_node import MqttNode, MqttToSerialNode
import json
import math
from datetime import datetime
from statistics import mean
from itertools import filterfalse

SIDE_AREA_PROPORTION = .3335
TOTAL_WID = 1280
CLOSE_GATE_DISTANCE = 40

TOPIC_SENSOR_DISTANCE = "/sensor/distance"
TOPIC_CAMERA = "camera_out"
TOPIC_MOTOR = "/cmd/motor_move"

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
        self.distance_stack = DistanceStack(3000)
        super().__init__("brain", TOPIC_MOTOR, [TOPIC_CAMERA, TOPIC_SENSOR_DISTANCE])


    def on_message(self, client, userdata, msg):
        print(msg.topic+" - "+str(msg.payload))
        if msg.topic == TOPIC_CAMERA:
            center_msg = json.loads(msg.payload)
            print(center_msg)
            center_x = center_msg['center'][0]
            for zone in self.zones:
                if center_x >= zone[0] and center_x < zone[1]:
                    zone_name = zone[2]
                    if zone_name in ['left','right']:
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
                    self.send(move_dir)
            print(f"avg distance from stack is {self.distance_stack.avg_distance()}")
        elif msg.topic == TOPIC_SENSOR_DISTANCE:
            print("msg on topic DISTANCE")
            distance_msg = json.loads(msg.payload)
            distance_val = float(distance_msg['distance'])
            self.distance_stack.push(distance_val)


class DistanceStack:

    def __init__(self, ms_ttl):
        self.ms_ttl = ms_ttl
        self.__elements = []

    def push(self, el):
        self.__elements.append((datetime.now(), el))
        self.__invalidate()
        print(list(el[1] for el in self.__elements))
        print(f"size = {len(self.__elements)}")

    
    def __invalidate(self):
        def determine(el):
            return (datetime.now() - el[0]).total_seconds() * 1000 > self.ms_ttl 
        self.__elements[:] = filterfalse(determine, self.__elements)

    def avg_distance(self):
        self.__invalidate()
        if len(self.__elements) > 0:
            return mean(el[1] for el in self.__elements)
        else:
            return None


brain = BrainNode()


mqtt_motor_driver = MqttToSerialNode("motor_mqtt", "/cmd/motor_move", "/tty/USB0", 115200)
