from unittest import TestCase
import unittest
from unittest import main, TestCase
from mqtt_node import MqttNode
from scenario_state_machine import ScenarioResult, ScenarioStateMachine
from time import sleep
import paho.mqtt.client as mqtt


class ScenarioStateMachineTestCase(TestCase):
    def create_messages(self, *simple_messages):
        return [{"msg": msg, "topic": "topic"} for msg in simple_messages]

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

    def test_msg_listen_step_interrupted(self):
        steps = [
            {
                "name": "listen_msg",
                "type": "receive_msg",
                "topic": "/test/scenariolisten",
                "timeout": 2,
            },
            {
                "name": "sleep_after_listen",
                "type": "sleep",
                "waiting_time": 0.3,
            },
        ]
        mqtt_node = MqttNode("testnode", "", "")
        machine = ScenarioStateMachine("test_scenario_msg_listen", steps, mqtt_node)
        machine.start()
        msgs = self.create_messages("ping1", "ping2", "ping3", "ping4")
        msgs[3]["topic"] = "/test/scenariolisten"
        for n, msg in enumerate(msgs):
            res = machine.process_message(msg)
            print(res)
            sleep(1)
        self.assertTrue(machine.interrupted())

    def test_msg_listen_step_msg_came_ok(self):
        steps = [
            {
                "name": "listen_msg",
                "type": "receive_msg",
                "topic": "/test/scenariolisten",
                "timeout": 4,
            },
            {
                "name": "sleep_after_listen",
                "type": "sleep",
                "waiting_time": 0.3,
            },
        ]
        mqtt_node = MqttNode("testnode", "", "")
        machine = ScenarioStateMachine("test_scenario_msg_listen", steps, mqtt_node)
        machine.start()
        msgs = self.create_messages("ping1", "ping2", "ping3", "ping4")
        msgs[3]["topic"] = "/test/scenariolisten"
        for n, msg in enumerate(msgs):
            res = machine.process_message(msg)
            print(res)
            sleep(1)
        self.assertFalse(machine.interrupted())


if __name__ == "__main__":
    main()
