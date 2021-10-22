build:
	pip install -r requirements.txt

run:
	python mqtt_node.py

camera:
	python ./detectnet-camera.py --camera=/dev/video0
