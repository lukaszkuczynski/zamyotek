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

    def start(self):
        self.__execute_next_step()

    def __execute_next_step(self, msg=None):
        self.current_step_no += 1
        step = self.__current_step()
        if step is None:
            self.finish_scenario()
            # self.current_step_no -= 1
            return ScenarioResult.FINISHED
        self.logger.info(
            "Executing step no %d. Named %s", self.current_step_no, step.name
        )
        step_is_not_async = step.execute(msg)
        if step_is_not_async:
            self.__execute_next_step()
        return ScenarioResult.NEXT_STEP

    def __current_step(self):
        if self.current_step_no >= len(self.steps):
            return None
        return self.steps[self.current_step_no]

    def process_message(self, msg):
        self.logger.debug("Processing message ")
        self.logger.debug(msg)
        if not self.active:
            return ScenarioResult.INACTIVE
        if self.__current_step().is_waiting_for(msg):
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
            self.started = datetime.now()

    def is_waiting_for(self, msg):
        return False

    def is_timeout(self):
        now = datetime.now()
        if (now - self.started).total_seconds() > self.timeout:
            return True
        return False

    def execute(self, msg=None):
        pass


class SleepStep(Step):
    def __init__(self, cfg, logger):
        super().__init__(cfg, logger)
        self.waiting_time = cfg["waiting_time"]

    def execute(self, msg=None):
        self.logger.debug("Step name %s", self.name)
        self.logger.info("Executing sleep for %s seconds.", self.waiting_time)
        sleep(self.waiting_time)
        return True


class MqttSendStep(Step):
    def __init__(self, cfg, logger, mqtt_node) -> None:
        super().__init__(cfg, logger)
        self.topic_to = cfg["topic"]
        self.msg = cfg.get("msg")
        self.mqtt_node = mqtt_node

    def execute(self, msg=None):
        if msg is None:
            msg = self.msg
        self.logger.info("Will send msg to '%s' topic" % self.topic_to)
        self.mqtt_node.send_to(topic=self.topic_to, message=self.msg)
        return True


class ReceiveMsgStep(Step):
    def __init__(self, cfg, logger) -> None:
        super().__init__(cfg, logger)
        if not "timeout" in cfg:
            raise Exception("This Step requires 'timeout' configuration key")
        self.topic_listen = cfg["topic"]

    def execute(self, msg=None):
        return False

    def is_waiting_for(self, msg):
        topic = msg["topic"]
        if topic == self.topic_listen:
            self.logger.info("I was waiting for it")
            return True
        return False
