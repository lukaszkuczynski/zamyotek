"""This is to test StateMachine"""
from time import sleep

from mqtt_node import MqttNode
from scenario_state_machine import ScenarioResult, ScenarioStateMachine


def create_messages(*simple_messages):
    return [{"msg": msg, "topic": "topic"} for msg in simple_messages]

def test_empty_state_machine_is_nono():
    try:
        ScenarioStateMachine("cant", [])
        assert False
    except Exception:
        assert True

def test_sleep_step():
    steps = [
        {"name": "onesleep", "waiting_time": 0.5, "type": "sleep"},
        {"name": "secondsleep", "waiting_time": 0.5, "type": "sleep"},
    ]
    machine = ScenarioStateMachine("testscenario1", steps)
    machine.start()
    msgs = create_messages(["ping1", "ping2", "ping3"])
    for msg in msgs:
        machine.process_message(msg)
        sleep(1)

def test_mqtt_step():
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

def test_msg_listen_step_interrupted():
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
    msgs = create_messages("ping1", "ping2", "ping3", "ping4")
    msgs[3]["topic"] = "/test/scenariolisten"
    for n, msg in enumerate(msgs):
        res = machine.process_message(msg)
        sleep(1)
    assert machine.interrupted() == True

def test_msg_listen_step_msg_came_ok():
    steps = [
        {
            "name": "listen_msg",
            "type": "receive_msg",
            "topic": "/test/scenariolisten",
            "timeout": 5,
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
    msgs = create_messages("ping1", "ping2", "ping3", "ping4")
    msgs[3]["topic"] = "/test/scenariolisten"
    for n, msg in enumerate(msgs):
        res = machine.process_message(msg)
        sleep(1)
    assert machine.interrupted() == False


def test_few_failed_finally_reaches_ok():
    steps = [
        {
            "name": "listen_msg",
            "type": "receive_msg",
            "topic": "/test/scenario_test_retry",
            "timeout": 3,
            "retries": 1
        },
        {
            "name": "sleep_after_listen",
            "type": "sleep",
            "waiting_time": 0.3,
        },
    ]
    commander_node = MqttNode("commander", "", "", autostart_listening=False)
    machine = ScenarioStateMachine("test_scenario_msg_listen", steps, commander_node)
    machine.start()
    msgs = [
        {"msg": "error:", "topic": "/test/scenario_test_retry"},
        {"msg": "error:", "topic": "/test/scenario_test_retry"},
        {"msg": "ok", "topic": "/test/scenario_test_retry"}
    ]
    for _, msg in enumerate(msgs):
        res = machine.process_message(msg)
        print(res)
        sleep(.3)
    assert res == ScenarioResult.FINISHED

def test_few_failed_finally_never_got_OK():
    steps = [
        {
            "name": "listen_msg",
            "type": "receive_msg",
            "topic": "/test/scenario_test_retry",
            "timeout": 3,
            "retries": 1
        },
        {
            "name": "sleep_after_listen",
            "type": "sleep",
            "waiting_time": 0.3,
        },
    ]
    commander_node = MqttNode("commander", "", "", autostart_listening=False)
    machine = ScenarioStateMachine("test_scenario_msg_listen", steps, commander_node)
    machine.start()
    msgs = [
        {"msg": "error:1", "topic": "/test/scenario_test_retry"},
        {"msg": "error:2", "topic": "/test/scenario_test_retry"},
        {"msg": "error:3", "topic": "/test/scenario_test_retry"},
        {"msg": "error:4", "topic": "/test/scenario_test_retry"},
    ]
    for _, msg in enumerate(msgs):
        res = machine.process_message(msg)
        sleep(.3)
    assert machine.active is True
    assert res is None