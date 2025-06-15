# PARAMETERS FOR YOLO----------------
import json
import os

import numpy as np

INTERSECTION_CONTROLLER_MODEL = 'smart-intersection-inference'
CONTROLLER_MODEL_FILE = 'square_J0_-22810.pth'
DETECTION_MODEL = 'yolo'
DETECTION_MODEL_FILE = 'yolo12x.pt'

PI_COMMUNICATION_GROUP = "pi_comms_group"
MOBILE_APP_COMMUNICATION_GROUP = "mobile_app_group"

with open(
        os.path.join('webcam',
                     'models',
                     DETECTION_MODEL,
                     'labels.json')
) as json_data:
    CLASS_NAMES = json.load(json_data)

detection_model_path = os.path.join('webcam',
                                    'models',
                                    DETECTION_MODEL,
                                    DETECTION_MODEL_FILE)

traffic_control_model_path = os.path.join('webcam',
                                          'models',
                                          INTERSECTION_CONTROLLER_MODEL,
                                          CONTROLLER_MODEL_FILE)

colors = np.random.uniform(0, 255, size=255)

CUSTOM_CLASS_NAMES = {
    # '0': 'person',
    '1': 'bicycle',
    '2': 'car',
    '3': 'motorcycle',
    '5': 'bus',
    '7': 'truck'
}

WAITING_SCORE_PENALTY = {
    # 'person': 0,
    'bicycle': 3,
    'car': 1,
    'motorcycle': 1,
    'bus': 5,
    'truck': 5
}

CURRENT_STATE_DICT = {
    "NORTH_SOUTH_GREEN": 0,
    "NORTH_SOUTH_YELLOW": 1,
    "EAST_WEST_GREEN": 2,
    "EAST_WEST_YELLOW": 3,
    "ALL_OFF:": 4,
    "ALL_YELLOW": 5
}

FRAME_RATE = 15

TRAFFIC_TOGGLE_THRESHOLD = 10

ENABLE_ANALYTICS_PLOTTING = False

DISPLAY_ROIS = True
ENABLE_VEHICLES_IN_ROIS_LOGGING = True

SMART_CONTROL_INTERVAL = 1.0 # 1 second
EDGE_CASES_OPTIMIZATIONS_COOLDOWN = 15.0 # 15 seconds

# VIDEO_SOURCE = "https://www.youtube.com/watch?v=ByED80IKdIU"
# VIDEO_SOURCE = "https://www.youtube.com/watch?v=NAk9Ku-n0Sk"


# libcamera-vid --mode 1920:1080:12:P --codec h264 --awb indoor --contrast 1.5 --saturation 1.5  -b 1000000 --autofocus-mode continuous  --framerate 15 -t 0 --inline --listen -o tcp://0.0.0.0:8888
# libcamera-vid --mode 2592:1944:12:P --codec mjpeg --awb indoor --contrast 1.5 --saturation 1.5  -b 1000000 --autofocus-mode continuous  --framerate 15 -t 0 --inline --listen -o tcp://0.0.0.0:8888

# libcamera-vid --mode 2592:1944:12:P --codec mjpeg --awb indoor --contrast 1.5 --saturation 1.5 -b 5000000 --flush 1 --sharpness 1.5 --denoise cdn_hq --autofocus-mode continuous --framerate 15 -t 0 --inline --listen -o tcp://0.0.0.0:8888


# TODO: Move these into .env file
# VIDEO_SOURCE = "tcp://raspberrypizero2w.local:8888"
# VIDEO_SOURCE = "tcp://raspberrypizero2w-tcp.at.remote.it:8888"
# VIDEO_SOURCE = "tcp://eu1.pitunnel.net:60605"
VIDEO_SOURCE = "tcp://127.0.0.1:8888"
# VIDEO_SOURCE = "tcp://192.168.1.9:8888"

INTERSECTION_ID = "89b04f61-90a6-4aba-8941-eef047cd3eb0"

# VIDEO_SOURCE = "https://www.youtube.com/watch?v=Vz4f8Gy6P1Q"
# VIDEO_SOURCE = "https://www.youtube.com/watch?v=sPe_XHhO5aw"


# rois for livestream
# ROI1 = [(0, 490), (190, 470), (240, 560), (0, 600)]
# ROI2 = [(240, 395), (160, 210), (265, 200), (460, 370)]
# ROI3 = [(680, 370), (1000, 340), (1000, 400), (790, 425)]
# ROI4 = [(590, 560), (840, 530), (1000, 625), (1000, 700), (740, 700)]
# ROI_CENTRAL = [(240, 410), (630, 370), (810, 490), (310, 570)]

# rois for Raspberry Pi stream
ROI1 = [(220, 700), (130, 590), (345, 435), (450, 540)]  # West
ROI2 = [(180, 195), (245, 165), (370, 250), (275, 300)]  # North
ROI3 = [(700, 100), (750, 130), (680, 175), (625, 140)]  # East
ROI4 = [(930, 420), (950, 370), (800, 265), (765, 310)]  # South
ROI_CENTRAL = [(490, 475), (320, 330), (600, 160), (750, 240)]
