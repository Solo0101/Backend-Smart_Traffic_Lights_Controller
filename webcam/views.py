import json
import os

import torch
from django.http import HttpResponse
from django.template import loader
from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

import cv2
import numpy as np

from vidgear.gears import VideoGear

from ultralytics import YOLO

# Create your views here.

trafficLightControlResponseList = [0, 1, 0, 1]
trafficLightControlStatus = 1


# HOME PAGE -------------------------
def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))


# -----------------------------------

# GET REQUEST -------------------------
@api_view(['GET'])
def get_traffic_light_control_response(request):
    return Response(data=trafficLightControlResponseList, status=status.HTTP_200_OK)


@api_view(['POST'])
def post_traffic_light_control_status(request):
    global trafficLightControlStatus
    trafficLightControlStatus = request.data['trafficLightControlStatus']
    return Response(status=status.HTTP_202_ACCEPTED)


# -----------------------------------

# PARAMETERS FOR YOLO----------------

DETECTION_MODEL = 'yolo'

with open(
        os.path.join('webcam\models', DETECTION_MODEL, 'labels.json')
) as json_data:
    CLASS_NAMES = json.load(json_data)

model = YOLO("webcam/models/yolo/yolov8n.pt")
colors = np.random.uniform(0, 255, size=255)

CUSTOM_CLASS_NAMES = {'0': 'person', '1': 'bicycle', '2': 'car', '3': 'motorcycle', '5': 'bus', '7': 'truck'}


def check_wanted_classes(class_key):
    if class_key not in CUSTOM_CLASS_NAMES:
        return False
    return True


# DISPLAY CAMERA 1 ------------------

def stream_1():
    # For local machine webcam:
    # cam_id = 0
    # vid = VideoGear(source=cam_id).start()

    # For Raspberry Pi Video Connection:
    # vid = cv2.VideoCapture("tcp://raspberrypizero2w.local:8888")

    # For YouTube Streams/Videos:
    vid = VideoGear(
        source="https://www.youtube.com/watch?v=ByED80IKdIU ! application/x-rtp,media=video,payload=96,"
               "clock-rate=90000,encoding-name=H264, ! rtph264depay ! decodebin ! videoconvert ! video/x-raw, "
               "format=BGR ! appsink",
        stream_mode=True,
        resolution=(640, 448),
        framerate=30,
        logging=True,
        time_delay=1
    ).start()

    # vid = VideoGear(
    #     source="https://www.youtube.com/watch?v=Vz4f8Gy6P1Q,"
    #            "clock-rate=90000,encoding-name=H264, ! rtph264depay ! decodebin ! videoconvert ! video/x-raw, "
    #            "format=BGR ! appsink",
    #     stream_mode=True,
    #     # resolution=(1280, 720),
    #     resolution=(640, 480),
    #     framerate=30,
    #     logging=True,
    #     time_delay=1
    # ).start()

    # vid = VideoGear(
    #     source="https://www.youtube.com/watch?v=sPe_XHhO5aw,"
    #            "clock-rate=90000,encoding-name=H264, ! rtph264depay ! decodebin ! videoconvert ! video/x-raw, "
    #            "format=BGR ! appsink",
    #     stream_mode=True,
    #     # resolution=(1280, 720),
    #     resolution=(640, 480),
    #     framerate=30,
    #     logging=True,
    #     time_delay=1
    # ).start()

    # vid = VideoGear(
    #     source="webcam/intersection_test_video.mp4",
    #     resolution=(640, 480),
    #     framerate=30,
    #     logging=True,
    #     time_delay=1,
    # ).start()

    custom_class_ids = []

    for k in CUSTOM_CLASS_NAMES:
        if check_wanted_classes(k):
            custom_class_ids.append(int(k))

    # rois for livestream

    roi1 = [(0, 490), (190, 470), (240, 560), (0, 600)]
    roi2 = [(240, 395), (160, 210), (265, 200), (460, 370)]
    roi3 = [(680, 370), (1000, 340), (1000, 400), (790, 425)]
    roi4 = [(590, 560), (840, 530), (1000, 625), (1000, 700), (740, 700)]

    global trafficLightControlStatus

    while True:
        # status, frame = vid.read()
        frame = vid.read()
        # if not status:
        #     break
        frame = cv2.resize(frame, (1000, 700))

        # rois for https://www.youtube.com/watch?v=sPe_XHhO5aw
        # roi2 = crop_image(frame, [(70, 300), (125, 185), (430, 285), (230, 375)])

        results = model.track(frame, persist=True, classes=custom_class_ids, conf=0.1, iou=0.1,
                              tracker="webcam/models/yolo/bytetrack.yaml")

        vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, track_ids_list = roi_tracking(results,
                                                                                                              [roi1,
                                                                                                               roi2,
                                                                                                               roi3,
                                                                                                               roi4])
        print(trafficLightControlStatus)
        print(track_ids_list)

        control_traffic_lights([vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4])

        annotated_frame = results[0].plot()
        print(len(vehicles_in_roi1), vehicles_in_roi1)
        print(len(vehicles_in_roi2), vehicles_in_roi2)
        print(len(vehicles_in_roi3), vehicles_in_roi3)
        print(len(vehicles_in_roi4), vehicles_in_roi4)
        cv2.polylines(annotated_frame, [np.array(roi1)], True, (255, 0, 0, 125), 2)
        cv2.polylines(annotated_frame, [np.array(roi2)], True, (0, 255, 0, 125), 2)
        cv2.polylines(annotated_frame, [np.array(roi3)], True, (255, 0, 255, 125), 2)
        cv2.polylines(annotated_frame, [np.array(roi4)], True, (0, 0, 255, 125), 2)

        cv2.imwrite('currentframe.jpg', annotated_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('currentframe.jpg', 'rb').read() + b'\r\n')


def video_feed_1(request):
    return StreamingHttpResponse(stream_1(), content_type='multipart/x-mixed-replace; boundary=frame')


def roi_tracking(results, roi_list):
    roi1 = roi_list[0]
    roi2 = roi_list[1]
    roi3 = roi_list[2]
    roi4 = roi_list[3]

    center_track_id_map = {}

    vehicles_in_roi1 = []
    vehicles_in_roi2 = []
    vehicles_in_roi3 = []
    vehicles_in_roi4 = []

    if torch.cuda.is_available():
        boxes = results[0].boxes.cuda().xywh
        class_ids = results[0].boxes.cls.cuda().tolist()
        track_ids = results[0].boxes.cuda().id
    else:
        boxes = results[0].boxes.cpu().xywh
        class_ids = results[0].boxes.cls.cpu().tolist()
        track_ids = results[0].boxes.cpu().id

    if track_ids is not None:
        track_ids_list = track_ids.tolist()
        for track_id, bbox in zip(track_ids_list, boxes.tolist()):
            center_point = (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)
            center_track_id_map.update({track_id: center_point})
        for k, class_id in zip(center_track_id_map, class_ids):
            if cv2.pointPolygonTest(np.array(roi1), center_track_id_map[k], False) > 0:
                vehicles_in_roi1.append([CLASS_NAMES[str(int(class_id))], int(k), center_track_id_map[k]])
            elif cv2.pointPolygonTest(np.array(roi2), center_track_id_map[k], False) > 0:
                vehicles_in_roi2.append([CLASS_NAMES[str(int(class_id))], int(k), center_track_id_map[k]])
            elif cv2.pointPolygonTest(np.array(roi3), center_track_id_map[k], False) > 0:
                vehicles_in_roi3.append([CLASS_NAMES[str(int(class_id))], int(k), center_track_id_map[k]])
            elif cv2.pointPolygonTest(np.array(roi4), center_track_id_map[k], False) > 0:
                vehicles_in_roi4.append([CLASS_NAMES[str(int(class_id))], int(k), center_track_id_map[k]])
    else:
        track_ids_list = []
    return vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, track_ids_list


WAITING_SCORE_PENALTY = {
    "car": 1,
    "bus": 5,
    "motorcycle": 1,
    "truck": 5,
}


def get_waiting_score(roi_list):
    waiting_score = 0

    for i in range(1, len(trafficLightControlResponseList)):
        if trafficLightControlResponseList[i] == 1:
            for vehicle in roi_list[i]:
                waiting_score = waiting_score + WAITING_SCORE_PENALTY[vehicle[0]]
    return waiting_score


def control_traffic_lights(roi_list):
    global trafficLightControlResponseList
    result = [0, 0, 0, 0]
    # TODO: Implement logic

    waiting_score = get_waiting_score(roi_list)

    # https://github.com/batman-nair/Traffic-Analyser/

    # wait for status update to be valid
    if not trafficLightControlStatus == 0:
        print("Endpoint worked!")

    trafficLightControlResponseList = result
