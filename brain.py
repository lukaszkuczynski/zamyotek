import logging
from mqtt_node import MqttNode, MqttToSerialNode
import json
import math
from datetime import datetime
from common_objects import AnyObjectStack, DistanceStack
import yaml

SIDE_AREA_PROPORTION = .3335
TOTAL_WID = 1280
CLOSE_GATE_DISTANCE = 10

TOPIC_SENSOR_DISTANCE = "/sensor/distance"
TOPIC_CAMERA = "camera_out"
TOPIC_MOTOR = "/cmd/motor_move"
TOPIC_SERVO = "/cmd/servo_gate"
TOPIC_MODE_CHANGER = "/cmd/brain_mode"
TURNING_TIME_NOOP = 1000
TOO_CLOSE_OBJECT_WIDTH = 800
AHEAD_COMMAND = "ahead,80"

class BrainNode(MqttNode):

    def __init__(self):
        self.last_move_dir = ""
        self.move_mode = "searching"
        center_left = math.floor(0 + (TOTAL_WID * SIDE_AREA_PROPORTION))
        center_right =  math.floor(TOTAL_WID - (TOTAL_WID * SIDE_AREA_PROPORTION))
        self.zones = [
            [0, center_left, "left"],
            [center_left+1, center_right, "central"],
            [center_right+1, TOTAL_WID, "right"]
        ]
        self.distance_stack = DistanceStack(ms_ttl=500, max_val=1000)
        self.turning_time_noop = TURNING_TIME_NOOP
        self.last_turning_time = datetime.now()
        self.motor_stack = AnyObjectStack(ms_ttl = 2000)
        super().__init__("brain", TOPIC_MOTOR, [TOPIC_CAMERA, TOPIC_SENSOR_DISTANCE, TOPIC_MODE_CHANGER])

    def reload_settings(self):
        self.logger.info("Re-loading settings")
        with open("config.yaml", "r") as stream:
            config = yaml.safe_load(stream)
            self.search_classes = config['camera']['classes_search']
            self.return_classes = config['camera']['classes_return']

    def on_message(self, client, userdata, msg):
        if msg.topic == TOPIC_MODE_CHANGER:
            mode_msg = json.loads(msg.payload)
            self.logger.info("Mode changed to %s", mode_msg["mode"])
            if mode_msg["mode"] == "searching":
                self.move_mode = "searching"
            elif mode_msg["mode"] == "return":
                self.move_mode = "return"
        if msg.topic == TOPIC_CAMERA:
            classes_to_follow = []
            if self.move_mode == "searching":
                classes_to_follow = self.search_classes
            elif self.move_mode == "return":
                classes_to_follow = self.return_classes
            center_msg = json.loads(msg.payload)
            if not center_msg['class_label'] in classes_to_follow:
                return
            center_x = center_msg['center'][0]
            width = center_msg['width']
            for zone in self.zones:
                if center_x >= zone[0] and center_x < zone[1]:
                    zone_name = zone[2]
                    if zone_name in ['left','right']:
                        if ((datetime.now() - self.last_turning_time).total_seconds() * 1000) < self.turning_time_noop:
                            self.logger.debug("Skipped turning, last turning time was just before..")
                            move_dir = 'stop'
                        else:
                            self.last_turning_time = datetime.now()
                            move_dir = zone_name
                    else:
                        # center, we have to decide on the basis of distance
                        # default decision is to go ahead
                        move_dir = AHEAD_COMMAND
                        distance = self.distance_stack.avg_distance()
                        if distance is not None:
                            # when distance is small then we should stop
                            if distance < CLOSE_GATE_DISTANCE:
                                move_dir = 'stop'
                        # if width > TOO_CLOSE_OBJECT_WIDTH:
                        #     move_dir = 'stop'
                    self.motor_stack.push(move_dir)
                    self.send(move_dir)
                    if move_dir != self.last_move_dir:
                        if self.move_mode == 'searching':
                            if move_dir == 'stop':
                                self.send_to('close_gate', TOPIC_SERVO)
                            elif move_dir == AHEAD_COMMAND:
                                self.send_to('open_gate', TOPIC_SERVO)
                        else:
                            self.send_to('close_gate', TOPIC_SERVO)
                    self.last_move_dir = move_dir

            print(f"avg distance from stack is {self.distance_stack.avg_distance()}")
            print(f"object closeness width perc is {width / TOO_CLOSE_OBJECT_WIDTH}")
        elif msg.topic == TOPIC_SENSOR_DISTANCE:
            distance_msg = json.loads(msg.payload)
            distance_val = float(distance_msg['distance'])
            self.distance_stack.push(distance_val)
            if not self.motor_stack.most_common():
                move_dir = 'stop'
                self.send(move_dir)
                self.last_move_dir = move_dir
                self.send_to('close_gate', TOPIC_SERVO)


brain = BrainNode()


mqtt_motor_driver = MqttToSerialNode("motor_mqtt", "/cmd/motor_move", "/tty/USB0", 115200)
