from unittest import TestCase
import unittest
from unittest import main, TestCase
from scenario_state_machine import ScenarioStateMachine
from time import sleep


class ScenarioStateMachineTestCase(TestCase):

    def create_messages(self, *simple_messages):
        return [{"msg": msg} for msg in simple_messages]

    def testEmptyStateMachineCantBeCreated(self):
        def emptyMachine():
            ScenarioStateMachine('cant', [])
        self.assertRaises(Exception, emptyMachine)

    def testSleepStep(self):
        steps = [
            {
                "name": "onesleep",
                "waiting_time": 0.5,
                "type": "sleep"
            },
            {
                "name": "secondsleep",
                "waiting_time": 0.5,
                "type": "sleep"
            }
        ]
        machine = ScenarioStateMachine('testscenario1', steps)
        machine.start()
        msgs = self.create_messages(["ping1", "ping2", "ping3"])
        for msg in msgs:
            machine.process_message(msg)
            sleep(1)


if __name__ == '__main__':
    main()
