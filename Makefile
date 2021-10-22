build:
	pip install -r requirements.txt

run:
	python mqtt_node.py

camera:
	python3 ./detectnet-camera.py --camera=/dev/video0

brain:
	python3 ./brain.py
