from abc import abstractmethod
from datetime import datetime
from enum import Enum
import time
from typing import overload
from time import sleep
import logging
import os
from mqtt_node import MqttNode


def setup_logger(name, log_folder="logs"):
    log_filename = os.path.join(log_folder, name + ".log")
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
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


class ScenarioResult(Enum):
    NEXT_STEP = 1
    TIMEOUT = 2
    FINISHED = 0
    INACTIVE = 3


class StepFactory:
    def step_from_config(self, cfg, logger, mqtt_node):
        if cfg["type"].lower() == "sleep":
            return SleepStep(cfg, logger)
        elif cfg["type"].lower() == "send_mqtt":
            return MqttSendStep(cfg, logger, mqtt_node)
        elif cfg["type"].lower() == "receive_msg":
            return ReceiveMsgStep(cfg, logger)


step_factory = StepFactory()


class ScenarioStateMachine:
    def __init__(self, name, steps, mqtt_node=None):
        self.logger = setup_logger(name)
        if len(steps) < 1:
            raise Exception("Cannot initiate state machine with 0 steps")
        self.logger.info("Creating scenario '%s' with %d steps", name, len(steps))
        self.steps = [
            step_factory.step_from_config(step, self.logger, mqtt_node)
            for step in steps
            if isinstance(step, dict)
        ]
        # self.logger.debug(steps)
        self.current_step_no = -1
        self.active = True
        self.storage = {}

    def start(self):
        self.active = True
        self.current_step_no = -1
        self.__execute_next_step(msg=None)

    def __execute_next_step(self, msg=None):
        self.current_step_no += 1
        step = self.__current_step()
        if step is None:
            self.finish_scenario()
            # self.current_step_no -= 1
            return ScenarioResult.FINISHED
        self.logger.info("Executing step#%d: %s", self.current_step_no, step.name)
        step_is_not_async = step.execute(msg, self.storage)
        if step_is_not_async:
            self.__execute_next_step(msg)
        return ScenarioResult.NEXT_STEP

    def __current_step(self):
        if self.current_step_no >= len(self.steps):
            return None
        return self.steps[self.current_step_no]

    def __save_to_storage_if_needed(self, step, msg):
        keyname = step.save_to_storage_key
        if keyname:
            self.storage[keyname] = msg

    def process_message(self, msg):
        # self.logger.debug("Processing message ")
        # self.logger.debug(msg)
        if not self.active:
            return ScenarioResult.INACTIVE
        if self.__current_step().is_waiting_for(msg):
            self.__save_to_storage_if_needed(self.__current_step(), msg)
            return self.__execute_next_step(msg)
        else:
            if self.__current_step().is_timeout():
                self.finish_scenario()
                return ScenarioResult.TIMEOUT
            return None

    def interrupted(self):
        self.logger.info("checking interrupt %d", self.current_step_no)
        return not self.active and (self.current_step_no < len(self.steps))

    def finish_scenario(self):
        self.logger.info("Scenario finished!")
        self.active = False


class Step:
    def __init__(self, cfg, logger) -> None:
        self.name = cfg["name"]
        self.logger = logger
        if not "timeout" in cfg:
            self.timeout = 0
        else:
            self.timeout = cfg["timeout"]
        self.save_to_storage_key = cfg.get("save_to_storage_key", None)
        self.read_from_storage_key = cfg.get("read_from_storage_key", None)

    def is_waiting_for(self, msg):
        return False

    def is_timeout(self):
        now = datetime.now()
        if (now - self.started).total_seconds() > self.timeout:
            return True
        return False

    def execute(self, msg=None, storage=None):
        self.started = datetime.now()


class SleepStep(Step):
    def __init__(self, cfg, logger):
        super().__init__(cfg, logger)
        self.waiting_time = cfg["waiting_time"]

    def execute(self, msg=None, storage=None):
        super().execute(msg, storage)
        self.logger.debug("Step name %s", self.name)
        self.logger.info("Executing sleep for %s seconds.", self.waiting_time)
        sleep(self.waiting_time)
        self.logger.debug("Waiting finished")
        return True


class MqttSendStep(Step):
    def __init__(self, cfg, logger, mqtt_node) -> None:
        super().__init__(cfg, logger)
        self.topic_to = cfg["topic"]
        self.msg_from_config = cfg.get("msg")
        self.mqtt_node = mqtt_node

    # complicated logic is here, msg is resolved in the following order:
    # 0. msg written as const in config of step
    # 1. msg from storage (inside of storage dict)
    # 2. msg from the previous operation (in arg of function)
    def __resolve_msg(self, msg_arg, storage):
        if self.msg_from_config:
            self.logger.debug("reading from config arg")
            return self.msg_from_config
        elif self.read_from_storage_key:
            self.logger.debug("reading from storage")
            return storage[self.read_from_storage_key]
        else:
            self.logger.debug("reading from previous op")
            return msg_arg

    def execute(self, msg=None, storage=None):
        super().execute(msg, storage)
        msg = self.__resolve_msg(msg, storage)
        self.logger.info("Will send msg to '%s' topic" % self.topic_to)
        self.mqtt_node.send_to(topic=self.topic_to, message=msg)
        sleep(0.05)
        self.logger.debug("Message from Mqtt send Step sent.")
        return True


class ReceiveMsgStep(Step):
    def __init__(self, cfg, logger) -> None:
        super().__init__(cfg, logger)
        if not "timeout" in cfg:
            raise Exception("This Step requires 'timeout' configuration key")
        self.topic_listen = cfg["topic"]

    def execute(self, msg=None, storage=None):
        super().execute(msg, storage)
        return False

    def is_waiting_for(self, msg):
        topic = msg["topic"]
        if topic == self.topic_listen:
            self.logger.info("I was waiting for it")
            return True
        return False
