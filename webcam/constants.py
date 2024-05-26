# PARAMETERS FOR YOLO----------------
import json
import os

import numpy as np
from ultralytics import YOLO

DETECTION_MODEL = 'yolo'

with open(
        os.path.join('webcam\\models',
                     DETECTION_MODEL,
                     'labels.json')
) as json_data:
    CLASS_NAMES = json.load(json_data)

model = YOLO("webcam/models/yolo/yolov8n.pt")
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

FRAME_RATE = 15

TRAFFIC_TOGGLE_THRESHOLD = 10

ENABLE_ANALYTICS_PLOTTING = False

DISPLAY_ROIS = True
ENABLE_VEHICLES_IN_ROIS_LOGGING = False

VIDEO_SOURCE = "https://www.youtube.com/watch?v=ByED80IKdIU"
# VIDEO_SOURCE = "tcp://raspberrypizero2w.local:8888"

# VIDEO_SOURCE =  "https://www.youtube.com/watch?v=Vz4f8Gy6P1Q"
# VIDEO_SOURCE =  "https://www.youtube.com/watch?v=sPe_XHhO5aw"


# rois for livestream
ROI1 = [(0, 490), (190, 470), (240, 560), (0, 600)]
ROI2 = [(240, 395), (160, 210), (265, 200), (460, 370)]
ROI3 = [(680, 370), (1000, 340), (1000, 400), (790, 425)]
ROI4 = [(590, 560), (840, 530), (1000, 625), (1000, 700), (740, 700)]
ROI_CENTRAL = [(240, 410), (630, 370), (810, 490), (310, 570)]

# rois for Raspberry Pi stream
# TODO: Get the values for this
# roi1 = [(0, 490), (190, 470), (240, 560), (0, 600)]
# roi2 = [(240, 395), (160, 210), (265, 200), (460, 370)]
# roi3 = [(680, 370), (1000, 340), (1000, 400), (790, 425)]
# roi4 = [(590, 560), (840, 530), (1000, 625), (1000, 700), (740, 700)]
# roi_central = [(240, 410), (630, 370), (810, 490), (310, 570)]
