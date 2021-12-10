from unittest import TestCase
import unittest
from unittest import main, TestCase
from mqtt_node import MqttNode
from scenario_state_machine import ScenarioStateMachine
from time import sleep
import paho.mqtt.client as mqtt


class ScenarioStateMachineTestCase(TestCase):
    def create_messages(self, *simple_messages):
        return [{"msg": msg} for msg in simple_messages]

    def test_empty_state_machine_is_nono(self):
        def emptyMachine():
            ScenarioStateMachine("cant", [])

        self.assertRaises(Exception, emptyMachine)

    def test_sleep_step(self):
        steps = [
            {"name": "onesleep", "waiting_time": 0.5, "type": "sleep"},
            {"name": "secondsleep", "waiting_time": 0.5, "type": "sleep"},
        ]
        machine = ScenarioStateMachine("testscenario1", steps)
        machine.start()
        msgs = self.create_messages(["ping1", "ping2", "ping3"])
        for msg in msgs:
            machine.process_message(msg)
            sleep(1)

    def test_mqtt_step(self):
        steps = [
            {
                "name": "sendmsg",
                "type": "send_mqtt",
                "topic": "/test/scenariotest",
                "msg": "go",
            }
        ]
        mqtt_node = MqttNode("testnode", "", "")
        machine = ScenarioStateMachine("test_scenario_mqtt", steps, mqtt_node)
        machine.start()


if __name__ == "__main__":
    main()
