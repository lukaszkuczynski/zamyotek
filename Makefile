build:
	pip install -r requirements.txt

MODEL_NAME=ssd-mobilenet-v2
#MODEL_NAME=ssd-inception-v2
camera:
	echo $(MODEL_NAME)
	python3 ./detectnet-camera.py --camera=/dev/video0 --network=$(MODEL_NAME)

brain:
	python3 ./brain.py

ESP32_PORT_MOTORS != dmesg | grep tty | grep attached | grep "usb 1-3.2.2" | tail -n 1 | sed -En "s/.*(tty.*)/\1/p"
ESP32_PORT_SENSORS != dmesg | grep tty | grep attached | grep "usb 1-3.2.1" | tail -n 1 | sed -En "s/.*(tty.*)/\1/p"
ESP32_PORT_SERVOS != dmesg | grep tty | grep attached | grep "usb 1-3.2.3" | tail -n 1 | sed -En "s/.*(tty.*)/\1/p"


motor:
	python3 ./motor_mqtt_node.py --port ${ESP32_PORT_MOTORS}

servos:
	python3 ./servo_mqtt_node.py --port ${ESP32_PORT_SERVOS}

sensor:
	python3 ./sensor_node.py --port $(ESP32_PORT_SENSORS)
