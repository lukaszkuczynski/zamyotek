build:
	pip install -r requirements.txt


camera:
	python3 ./detectnet-camera.py --camera=/dev/video0 --network=ssd-inception-v2

brain:
	python3 ./brain.py

ESP32_PORT != dmesg | grep tty | grep attached | tail -n 1 | sed -En "s/.*(tty.*)/\1/p"

motor:
	python3 ./motor_mqtt_node.py --port ${ESP32_PORT}
