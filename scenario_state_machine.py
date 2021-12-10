from datetime import datetime
from enum import Enum
import time
from typing import overload
from time import sleep
import logging
import os
import paho.mqtt.client as mqtt


def setup_logger(name, log_folder="logs"):
    log_filename = os.path.join(log_folder, name + ".log")
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    def step_from_config(self, cfg, logger):
        if cfg['type'].lower() == 'sleep':
            return SleepStep(cfg, logger)


step_factory = StepFactory()


class ScenarioStateMachine():

    def __init__(self, name, steps, mqtt_conn):
        self.logger = setup_logger(name)
        if len(steps) < 1:
            raise Exception("Cannot initiate state machine with 0 steps")
        self.logger.info(
            "Creating scenario '%s' with %d steps", name, len(steps))
        self.steps = [step_factory.step_from_config(
            step, self.logger) for step in steps if isinstance(step, dict)]
        self.current_step_no = 0
        self.active = True

    def start(self):
        self.__execute_next_step()

    def __execute_next_step(self):
        step = self.__current_step()
        if step is None:
            self.active = False
            return ScenarioResult.FINISHED
        step_is_not_async = step.execute()
        self.current_step_no += 1
        if step_is_not_async:
            self.__execute_next_step()

    def __current_step(self):
        if self.current_step_no >= len(self.steps):
            return None
        return self.steps[self.current_step_no]

    def process_message(self, msg):
        if not self.active:
            return ScenarioResult.INACTIVE
        if self.__current_step().is_waiting_for(msg):
            self.__execute_next_step()
            return ScenarioResult.NEXT_STEP
        else:
            if self.__current_step().is_timeout():
                return ScenarioResult.TIMEOUT
            return None


class Step():
    def __init__(self, cfg, logger) -> None:
        self.name = cfg['name']
        self.logger = logger
        if not 'timeout' in cfg:
            self.timeout = 0
        else:
            self.timeout = cfg['timeout']
            self.started = datetime.now()

    def is_waiting_for(self, msg):
        return False

    def is_timeout(self):
        now = datetime.now()
        if (now - self.started).total_seconds() * 1000 > self.timeout:
            return True
        return False

    def execute(self):
        pass


class SleepStep(Step):

    def __init__(self, cfg, logger):
        super().__init__(cfg, logger)
        self.waiting_time = cfg['waiting_time']

    def execute(self):
        self.logger.debug("Step name %s", self.name)
        self.logger.info("Executing sleep for %s seconds.", self.waiting_time)
        sleep(self.waiting_time)
        return True


class SendMqttStep(Step):

    def __init__(self, cfg, logger) -> None:
        super().__init__(cfg, logger)
        self.client = mqtt.Client()
        hostname = cfg['hostname'] | "locahost"
        port = cfg['port'] | 1883
        self.client.connect(hostname, port, 60)
