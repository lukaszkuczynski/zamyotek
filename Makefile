sensor_node_pid := $(shell ps -aux | grep sensor_node | grep -v grep | cut -f3 -d' ')
camera_node_pid := $(shell ps -aux | grep camera.py | grep -v grep | cut -f3 -d' ')
brain_node_pid := $(shell ps -aux | grep brain.py | grep -v grep | cut -f3 -d' ')
motor_node_pid := $(shell ps -aux | grep motor_mqtt_node.py | grep -v grep | cut -f3 -d' ')
servo_node_pid := $(shell ps -aux | grep servo_mqtt_node.py | grep -v grep | cut -f3 -d' ')
rekognition_node_pid  := $(shell ps -aux | grep rekognition_node.py | grep -v grep | cut -f3 -d' ')
async_photographer_node_pid  := $(shell ps -aux | grep async_photographer_node.py | grep -v grep | cut -f3 -d' ')

down:
	kill -2 $(sensor_node_pid) $(camera_node_pid) $(brain_node_pid) $(motor_node_pid) $(servo_node_pid) $(rekognition_node_pid) $(async_photographer_node_pid)

nobrainup: 
	make -j 6 motor servos sensor camera recognition photographer

nocamerabrainup: 
	make -j 6 motor servos sensor recognition photographer

up: 
	make -j 7 brain motor servos sensor camera recognition photographer

build:
	pip install -r requirements.txt

MODEL_NAME=ssd-mobilenet-v2
#MODEL_NAME=ssd-inception-v2
camera:
	echo $(MODEL_NAME)
	python3 ./detectnet-camera.py  --input-width=640 --input-height=480 --network=$(MODEL_NAME) --saved_pictures_folder=/home/lukjestson/Pictures/zamyotek


brain:
	python3 ./brain.py

ESP32_PORT_SENSORS != dmesg | grep tty | grep attached | grep "usb 1-3.2.1" | tail -n 1 | sed -En "s/.*(tty.*)/\1/p"
ESP32_PORT_MOTORS != dmesg | grep tty | grep attached | grep "usb 1-3.2.2" | tail -n 1 | sed -En "s/.*(tty.*)/\1/p"
ESP32_PORT_SERVOS != dmesg | grep tty | grep attached | grep "usb 1-3.2.3" | tail -n 1 | sed -En "s/.*(tty.*)/\1/p"


motor:
	python3 ./motor_mqtt_node.py --port ${ESP32_PORT_MOTORS}

servos:
	python3 ./servo_mqtt_node.py --port ${ESP32_PORT_SERVOS}

sensor:
	#echo $$PPID > sensor.pid
	python3 ./sensor_node.py --port $(ESP32_PORT_SENSORS) 

aws_listener:
	python3 ./aws_listener_node.py


rsync:
	rsync -av /home/luk/othprj/zamyotek/ jetson:/home/lukjestson/prj/zamyotek/ \
		--exclude site-packages \
		--exclude venv \
		--exclude .git \
		--exclude __pycache__ \
		--exclude .vscode \
		--exclude logs \
		--exclude node_modules

reactapp:
	cd react-mqtt-test && HOST=0.0.0.0 PORT=3000 ./node_modules/.bin/react-scripts start

recognition:
	. venv/bin/activate && python3 rekognition_node.py

photographer:
	python3 async_photographer_node.py

cleanandpull:
	git clean -fd
	git reset --hard
	git pull

download_images:
	rsync -av jetson:/home/lukjestson/Pictures/zamyotek ~/Pictures/zamyotek

dmesg:
	dmesg | grep tty | grep attached 