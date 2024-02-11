#!/usr/bin/python3
#
# Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import argparse
import os
import shutil
import sys
from datetime import datetime

import jetson.inference
import jetson.utils
import yaml

from aws_listener_node import CONFIG_PATH
from label_identifier import LabelIdentifier
from mqtt_node import MqttNode

# parse the command line
parser = argparse.ArgumentParser(
    description="Locate objects in a live camera stream using an object detection DNN.",
    formatter_class=argparse.RawTextHelpFormatter,
    epilog=jetson.inference.detectNet.Usage()
    + jetson.utils.videoSource.Usage()
    + jetson.utils.videoOutput.Usage()
    + jetson.utils.logUsage(),
)

parser.add_argument(
    "input_URI", type=str, default="", nargs="?", help="URI of the input stream"
)
parser.add_argument(
    "output_URI", type=str, default="", nargs="?", help="URI of the output stream"
)
parser.add_argument(
    "--network",
    type=str,
    default="ssd-mobilenet-v2",
    help="pre-trained model to load (see below for options)",
)
parser.add_argument(
    "--overlay",
    type=str,
    default="box,labels,conf",
    help="detection overlay flags (e.g. --overlay=box,labels,conf)\nvalid combinations are:  'box', 'labels', 'conf', 'none'",
)
parser.add_argument(
    "--threshold", type=float, default=0.5, help="minimum detection threshold to use"
)
parser.add_argument("--saved_pictures_folder", help="Folder to save taken pictures")
parser.add_argument("--async_flag_filepath", help="Where to store file for async phographer")

is_headless = ["--headless"] if sys.argv[0].find("console.py") != -1 else [""]

CAMERA_RELOAD_FILE = "camera_change_settings"
CONFIG_PATH = "config.yaml"
TOPIC_NOTIFY_PHOTO_TAKEN = "/notify/photo"

try:
    opt = parser.parse_known_args()[0]
except:
    parser.print_help()
    sys.exit(0)

# create video output object
output = jetson.utils.videoOutput(opt.output_URI, argv=sys.argv + is_headless)

# load the object detection network
net = jetson.inference.detectNet(opt.network, sys.argv, opt.threshold)

# create video sources
input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)

import json


class CameraNode(MqttNode):
    def __init__(self, args):
        filename = "/usr/local/bin/networks/SSD-Mobilenet-v2/ssd_coco_labels.txt"
        self.identifier = LabelIdentifier(filename)
        super().__init__("camera", "camera_out", "")
        self.pics_folder = args.saved_pictures_folder
        self.async_flag_filepath = args.async_flag_filepath
        self.reload_settings()

    def on_new_picture(self, img):
        if os.path.exists(self.async_flag_filepath):
            self.logger.info("New picture event.")
            os.remove(self.async_flag_filepath)
            now = datetime.now()  # current date and time
            date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
            filename_pic = f"{date_time}.jpg"
            full_pic_path = os.path.join(self.pics_folder, filename_pic)
            jetson.utils.saveImage(full_pic_path, img)
            photo_msg = full_pic_path
            self.logger.debug("sending")
            self.send_to(photo_msg, TOPIC_NOTIFY_PHOTO_TAKEN)

    def send_center(self, center_boundaries):
        if os.path.exists(CAMERA_RELOAD_FILE):
            os.remove(CAMERA_RELOAD_FILE)
            self.reload_settings()
        if center_boundaries["class_id"] in self.classes_to_check:
            label = self.identifier.label_for_number(int(center_boundaries["class_id"]))
            center_boundaries["class_label"] = label
            self.logger.info("Sending rect for %s", label)
            self.send(center_boundaries)
        else:
            self.logger.debug(
                "Other objects detected, class %s",
                self.identifier.label_for_number(int(center_boundaries["class_id"])),
            )

    def reload_settings(self):
        self.logger.info("Re-loading settings")
        with open(CONFIG_PATH, "r") as stream:
            config = yaml.safe_load(stream)
            search_classes = config["camera"]["classes_search"]
            return_classes = config["camera"]["classes_return"]
            classes = search_classes
            classes.extend(return_classes)
            self.logger.info("Camera will search for following labels = %s" % classes)
            label_ints = [
                self.identifier.number_for_label(class_text) for class_text in classes
            ]
            self.logger.info("It reflect the following class IDs = %s" % label_ints)
            self.classes_to_check = label_ints


# class id to report
# 1 - person, 37 - sportsball
# 88 teddy bear
# 64 plant
camera_node = CameraNode(opt)

# process frames until the user exits
while True:
    # capture the next image
    img = input.Capture()
    if img is None:
        continue
    camera_node.on_new_picture(img)
    # detect objects in the image (with overlay)
    detections = net.Detect(img, overlay=opt.overlay)

    # print the detections
    if len(detections) == 0:
        camera_node.logger.debug(
            "detected {:d} objects in image".format(len(detections))
        )
    else:
        camera_node.logger.info(
            "detected {:d} objects in image".format(len(detections))
        )

    for detection in detections:
        camera_node.logger.debug(detection)
        camera_node.send_center(
            {
                "class_id": detection.ClassID,
                "center": detection.Center,
                "confidence": detection.Confidence,
                "width": detection.Width,
                "topic": "camera_out",
            }
        )

    # render the image
    output.Render(img)

    # update the title bar
    output.SetStatus(
        "{:s} | Network {:.0f} FPS".format(opt.network, net.GetNetworkFPS())
    )

    # print out performance info
    # net.PrintProfilerTimes()

    # exit on input/output EOS
    if not input.IsStreaming() or not output.IsStreaming():
        break
