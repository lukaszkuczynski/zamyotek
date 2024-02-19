# TTbot (Track & Tell bot)
TTbot is a Jetson-powered object detection robot, linked with cloud AI systems and created in a decoupled manner. The idea of decoupling came from ROS that I haven't used as I wanted to have a purely Python solution.

## Demo
It moves, follows me and recognizes objects (somehow, we're still working to make it more reliable). Click the image below to see YT video...

[![IMAGE ALT TEXT](./pics/zamyotek_explores.png)](http://www.youtube.com/watch?v=LvrNewLIw1k "TTbot 1st photoshoot")


## Initial idea and change
The initial idea of the project was to follow objects and grab them with “arms” controlled by servo mechanisms. However, the custom trained Tensorflow detection algorithm based on SSD Mobilenet has rather low performance with small sized objects. Thus, the idea was altered, and now TTbot follows “big objects” (f.e. humans) and if presented with some object just ahead of him, he will speak what he sees.

## General idea
TTbot consists of *nodes* which are independently doing their job. They are publishing and subscribing to topics which are in the area of their responsibility. F.e. the node for sensor is sending distance measurements to `/sensor/distance` and *brain* node is listening to that and interpreting information to send commands to `/cmd/motor_move` where *motor* node is listening.
The main loop is reading data from the camera and sending coordinates of detected objects to a MQTT queue. Some of these nodes are displayed in the diagram below.

![communication nodes](pics/zamyotek_nodes.drawio.png)

## Hardware
The main *brain* of the robot is Jetson Nano SBC. It runs Ubuntu on board so it is easily extendable and one can install needed Linux packages easily. It means I can run Python nodes too. Jetson Nano is capable of connecting electronics on 40 PIN header, [check out docs](https://developer.nvidia.com/embedded/learn/jetson-nano-2gb-devkit-user-guide#id-.JetsonNano2GBDeveloperKitUserGuidevbatuu_v1.0-40-PinHeader(J6)). You can also connect additional accessories to it via USB ports. Microcontrollers are OK to connect any sensors compatible to the Voltage level. And in case of problems I feel much more comfortable to burn the microcontroller than Jetson Nano.  Thus in this project there are several ESPs which are connected via USB cable and transmit data via it. They take both input voltage and data via the same USB cable.
Major parts used in the project are shown in the diagram, however the connections are not displayed. This is just to give the general overview of the project.

![communication nodes](pics/zamyotek_fritzing_bb.png)

## Machine Learning
Jetson Nano comes with many pretrained models which work very efficiently. However the author of this project wanted to train his custom model. Unfortunately SSD Mobilenet v2 has pretty low performance on small objects. So the initial idea was changed as explained in the first sections and now the default algorithms as part of Jetson Pack are used. It gives pretty good performance when TensorRT in real time with 30 FPS. Image recognition of objects put just ahead of it are done with AWS and OpenAI.

## Cloud integration
To offload some ML calculations there were AWS services used to:
- recognize objects
- create speech fragments

Whenever an object is put in front of the robot, the photo is taken and according to the `TELLME` scenario it is sent to OpenAI service. Then the picture (so what TTbot sees) is interpreted with OpenAI Vision system. When the result is created it is put on speech synthesis topic. Speec synthesis is done with AWS Polly service.

## Brain modes
The main software element of the robot is working in the following modes:
 - `FOLLOW`
 - `TELLME`

In the `FOLLOW` mode TTbot is just the trying to detect and move in the direction of object classes. The `TELLME` scenario is executed when objects are detected by distance sensor.

In the `TELLME` scenario TTbot is trying to tell you what he sees. As for now Internet communication is required because it uses AI cloud services. In this scenario it moves camera down, takes a photo and sends to the recognition system. Then, if any “speaking node” is running it receives the command to play sound.
