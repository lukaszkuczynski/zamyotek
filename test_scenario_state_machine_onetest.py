from unittest import TestCase
import unittest
from unittest import main, TestCase
from mqtt_node import MqttNode
from scenario_state_machine import ScenarioResult, ScenarioStateMachine
from time import sleep
import paho.mqtt.client as mqtt


class ScenarioStateMachineOneTestCase(TestCase):
    def test_mqtt_step(self):
        steps = [
            {
                "name": "sendmsg",
                "type": "send_mqtt",
                "topic": "/test/scenariotest",
                "msg": "go",
            },
            {"name": "onesleep", "waiting_time": 2, "type": "sleep"},
            {
                "name": "sendmsg",
                "type": "send_mqtt",
                "topic": "/test/scenariotest",
                "msg": "go2",
            },
        ]
        mqtt_node = MqttNode("testnode", "", "")
        machine = ScenarioStateMachine("test_scenario_mqtt", steps, mqtt_node)
        machine.start()


if __name__ == "__main__":
    main()
