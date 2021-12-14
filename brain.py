import logging
from mqtt_node import MqttNode, MqttToSerialNode, get_client
import json
import math
from datetime import datetime
from common_objects import AnyObjectStack, DistanceStack
import yaml
from enum import Enum

from scenario_state_machine import ScenarioResult, ScenarioStateMachine

SIDE_AREA_PROPORTION = 0.3335
TOTAL_WID = 1280
OBJECT_TO_TELL_DISTANCE = 20

TOPIC_SENSOR_DISTANCE = "/sensor/distance"
TOPIC_CAMERA = "camera_out"
TOPIC_MOTOR = "/cmd/motor_move"
TOPIC_SERVO = "/cmd/servo_gate"
TOPIC_MODE_CHANGER = "/cmd/brain_mode"
TOPIC_RELOAD_SETTINGS = "/cmd/reload_settings"
TOPIC_CMD_SERVO_HEAD = "/cmd/servo/head_position"
TOPIC_TAKE_PHOTO = "/cmd/take_photo"
TOPIC_NOTIFY_OBJECT_RECOGNIZED = "/notify/object_recognized"
TOPIC_CMD_SPEAK = "/cmd/speak"
TOPIC_NOTIFY_SPOKEN = "/notify/spoken"


TURNING_TIME_NOOP = 1000
TOO_CLOSE_OBJECT_WIDTH = 800
# AHEAD_COMMAND = "ahead,80"
DEFAULT_AHEAD_SPEED = 70


class BrainMode(Enum):
    IDLE = 0
    FOLLOW = 1
    TELLME = 2


class BrainNode(MqttNode):
    def __init__(self):
        self.last_move_dir = ""
        center_left = math.floor(0 + (TOTAL_WID * SIDE_AREA_PROPORTION))
        center_right = math.floor(TOTAL_WID - (TOTAL_WID * SIDE_AREA_PROPORTION))
        self.zones = [
            [0, center_left, "left"],
            [center_left + 1, center_right, "central"],
            [center_right + 1, TOTAL_WID, "right"],
        ]
        self.distance_stack = DistanceStack(ms_ttl=500, max_val=1000)
        self.turning_time_noop = TURNING_TIME_NOOP
        self.last_turning_time = datetime.now()
        self.motor_stack = AnyObjectStack(ms_ttl=2000)
        self.speed = DEFAULT_AHEAD_SPEED
        few_steps = [
            {
                "name": "look_down",
                "type": "send_mqtt",
                "topic": TOPIC_CMD_SERVO_HEAD,
                "msg": "godown",
            },
            {"name": "servo_travel_down", "waiting_time": 3, "type": "sleep"},
            {
                "name": "look_up",
                "type": "send_mqtt",
                "topic": TOPIC_CMD_SERVO_HEAD,
                "msg": "goup",
            },
        ]
        steps = [
            {
                "name": "look_down",
                "type": "send_mqtt",
                "topic": TOPIC_CMD_SERVO_HEAD,
                "msg": "godown",
            },
            {"name": "servo_travel_down", "waiting_time": 2, "type": "sleep"},
            {
                "name": "take_photo",
                "type": "send_mqtt",
                "topic": TOPIC_TAKE_PHOTO,
                "msg": "takeit",
            },
            {
                "name": "recognize_photo",
                "type": "receive_msg",
                "topic": TOPIC_NOTIFY_OBJECT_RECOGNIZED,
                "save_to_storage_key": "object_class",
                "timeout": 4,
            },
            {
                "name": "look_up",
                "type": "send_mqtt",
                "topic": TOPIC_CMD_SERVO_HEAD,
                "msg": "goup",
            },
            {"name": "servo_travel_up", "waiting_time": 2, "type": "sleep"},
            {
                "name": "speak_msg",
                "read_from_storage_key": "object_class",
                "type": "send_mqtt",
                "topic": TOPIC_CMD_SPEAK,
            },
            {
                "name": "wait_for_speech",
                "type": "receive_msg",
                "topic": TOPIC_NOTIFY_SPOKEN,
                "timeout": 5,
            },
            {
                "name": "sleep_idle_time_after_scenario",
                "waiting_time": 1,
                "type": "sleep",
            },
        ]
        scenario_node = MqttNode("scenario", "", "")
        self.tell_me_scenario = ScenarioStateMachine(
            "tell_me_scenario", steps, scenario_node
        )
        # this should be follow
        super().__init__(
            "brain",
            TOPIC_MOTOR,
            [
                TOPIC_CAMERA,
                TOPIC_SENSOR_DISTANCE,
                TOPIC_MODE_CHANGER,
                TOPIC_RELOAD_SETTINGS,
                TOPIC_NOTIFY_OBJECT_RECOGNIZED,
                TOPIC_NOTIFY_SPOKEN,
            ],
            autostart_listening=False,
        )
        self.change_mode(BrainMode.FOLLOW)
        self.start_listening()

    def reload_settings(self):
        self.logger.info("Re-loading settings")
        with open("config.yaml", "r") as stream:
            config = yaml.safe_load(stream)
            self.search_classes = config["camera"]["classes_search"]
            self.return_classes = config["camera"]["classes_return"]

    def change_mode(self, brain_mode):
        self.logger.info("Setting Brain to mode %s" % brain_mode)
        self.brain_mode = brain_mode
        if self.brain_mode == BrainMode.TELLME:
            self.tell_me_scenario.start()

    def on_message(self, client, userdata, msg):
        if msg.topic == TOPIC_MODE_CHANGER:
            mode_msg = json.loads(msg.payload)
            self.logger.info("Mode changed to %s", mode_msg["mode"])
            if mode_msg["mode"] == "follow":
                self.brain_mode = BrainMode.FOLLOW
            elif mode_msg["mode"] == "tellme":
                self.brain_mode = BrainMode.TELLME
        if self.brain_mode == BrainMode.IDLE:
            self.logger.debug(
                "Brain idle. I won't do anything with msg on topic %s", msg.topic
            )
        elif self.brain_mode == BrainMode.TELLME:
            mode_msg = json.loads(msg.payload)
            process_result = self.tell_me_scenario.process_message(mode_msg)
            self.logger.debug("Process result %s", process_result)
            if process_result in (ScenarioResult.FINISHED, ScenarioResult.INACTIVE):
                self.logger.info(
                    "Scenario in brain finished - state %s!", process_result
                )
                # self.change_mode(BrainMode.FOLLOW)
                self.change_mode(BrainMode.IDLE)
            elif process_result == ScenarioResult.TIMEOUT:
                self.logger.warn("Timeout. Tellme scenario failed :(")
                self.change_mode(BrainMode.FOLLOW)
        elif self.brain_mode == BrainMode.FOLLOW:
            if msg.topic == TOPIC_RELOAD_SETTINGS:
                self.reload_settings()
            elif msg.topic == TOPIC_CAMERA:
                classes_to_follow = self.search_classes
                center_msg = json.loads(msg.payload)
                if not center_msg["class_label"] in classes_to_follow:
                    return
                center_x = center_msg["center"][0]
                width = center_msg["width"]
                for zone in self.zones:
                    if center_x >= zone[0] and center_x < zone[1]:
                        zone_name = zone[2]
                        if zone_name in ["left", "right"]:
                            if (
                                (
                                    datetime.now() - self.last_turning_time
                                ).total_seconds()
                                * 1000
                            ) < self.turning_time_noop:
                                self.logger.debug(
                                    "Skipped turning, last turning time was just before.."
                                )
                                move_dir = "stop"
                            else:
                                self.last_turning_time = datetime.now()
                                move_dir = zone_name
                        else:
                            # center, we have to decide on the basis of distance
                            # default decision is to go ahead
                            move_dir = f"ahead,{self.speed}"
                            distance = self.distance_stack.avg_distance()
                            if distance is not None:
                                # when distance is small then we should stop and start telling what's that
                                if distance < OBJECT_TO_TELL_DISTANCE:
                                    move_dir = "stop"
                                    self.change_mode(BrainMode.TELLME)
                                elif distance < OBJECT_TO_TELL_DISTANCE + 10:
                                    self.speed = DEFAULT_AHEAD_SPEED - 30
                                elif distance < OBJECT_TO_TELL_DISTANCE + 20:
                                    self.speed = DEFAULT_AHEAD_SPEED - 20
                                elif distance < OBJECT_TO_TELL_DISTANCE + 30:
                                    self.speed = DEFAULT_AHEAD_SPEED - 15
                                elif distance < OBJECT_TO_TELL_DISTANCE + 50:
                                    self.speed = DEFAULT_AHEAD_SPEED - 10
                                else:
                                    self.speed = DEFAULT_AHEAD_SPEED

                        self.motor_stack.push(move_dir)
                        if move_dir != self.last_move_dir:
                            self.send(move_dir)
                        self.last_move_dir = move_dir

                self.logger.debug(
                    f"avg distance from stack is {self.distance_stack.avg_distance()}"
                )
                self.logger.debug(
                    f"object closeness width perc is {width / TOO_CLOSE_OBJECT_WIDTH}"
                )
            elif msg.topic == TOPIC_SENSOR_DISTANCE:
                distance_msg = json.loads(msg.payload)
                distance_val = float(distance_msg["distance"])
                self.distance_stack.push(distance_val)
                if not self.motor_stack.most_common():
                    move_dir = "stop"
                    self.send(move_dir)
                    self.last_move_dir = move_dir
                avg_distance = self.distance_stack.avg_distance()
                if avg_distance is not None:
                    # when distance is small then we should stop and start telling what's that
                    if self.brain_mode == BrainMode.FOLLOW:
                        if avg_distance < OBJECT_TO_TELL_DISTANCE:
                            self.change_mode(BrainMode.TELLME)


brain = BrainNode()


mqtt_motor_driver = MqttToSerialNode(
    "motor_mqtt", "/cmd/motor_move", "/tty/USB0", 115200
)
