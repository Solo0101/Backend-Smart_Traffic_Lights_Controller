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
import matplotlib.pyplot as plt

trafficLightControlResponseList = [1, 0, 1, 0]
trafficLightControlStatus = 1


# Create your views here.

# HOME PAGE -------------------------
def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))


# -----------------------------------

# GET REQUEST -------------------------
@api_view(['GET'])
def get_traffic_light_control_response(request):
    return Response(data=trafficLightControlResponseList, status=status.HTTP_200_OK)


# POST REQUEST -------------------------
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
        framerate=15,
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
    roi_central = [(240, 410), (630, 370), (810, 490), (310, 570)]

    global trafficLightControlStatus
    vehicles_in_intersection = []
    frame_number = 0
    real_frame_number = 0
    analytic_list_waiting_score = []
    analytic_list_throughput_score = []
    while True:
        waiting_score = 0
        # status, frame = vid.read()
        frame = vid.read()
        # if not status:
        #     break
        frame = cv2.resize(frame, (1000, 700))
        real_frame_number += 1

        # rois for https://www.youtube.com/watch?v=sPe_XHhO5aw
        # roi2 = crop_image(frame, [(70, 300), (125, 185), (430, 285), (230, 375)])

        results = model.track(frame, persist=True, classes=custom_class_ids, conf=0.1, iou=0.1,
                              tracker="webcam/models/yolo/bytetrack.yaml")

        vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection, track_ids_list = roi_tracking(
            results,
            [roi1,
             roi2,
             roi3,
             roi4,
             roi_central], vehicles_in_intersection)

        waiting_score, throughput_score, traffic_volume_score, frame_number = control_traffic_lights(
            [vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection],
            waiting_score, frame_number)

        # # clipped_traffic_volume_score = 0
        # if traffic_volume_score%500 != 0:
        #     clipped_traffic_volume_score = traffic_volume_score%500
        # elif traffic_volume_score%500 == 0 and traffic_volume_score != 0:
        #     clipped_traffic_volume_score = 500
        # else:
        #     clipped_traffic_volume_score = 0

        # analytic_list_waiting_score.append((traffic_volume_score, waiting_score))
        # analytic_list_throughput_score.append((traffic_volume_score, throughput_score))
        #
        # if len(analytic_list_waiting_score) == 500:
        #     analytic_list_waiting_score.sort(key=lambda x: x[1])
        #     analytic_list_throughput_score.sort(key=lambda x: x[1])
        #     plt.xlabel("traffic volume score")
        #     plt.ylabel("waiting_score/throughput_score")
        #     plt.plot(*zip(*analytic_list_waiting_score), label="waiting_score")
        #     plt.plot(*zip(*analytic_list_throughput_score), label="throughput_score")
        #     plt.savefig('analytics500framesv2.0.png', bbox_inches='tight')
        #     plt.show()
        #
        # if len(analytic_list_waiting_score) == 1500:
        #     analytic_list_waiting_score.sort(key=lambda x: x[1])
        #     analytic_list_throughput_score.sort(key=lambda x: x[1])
        #     plt.xlabel("traffic volume score")
        #     plt.ylabel("waiting_score/throughput_score")
        #     plt.plot(*zip(*analytic_list_waiting_score), label = "waiting_score")
        #     plt.plot(*zip(*analytic_list_throughput_score), label = "throughput_score")
        #     plt.savefig('analytics1500framesv2.0.png', bbox_inches='tight')
        #     plt.show()
        #
        #
        #
        # if len(analytic_list_waiting_score) == 3000:
        #     analytic_list_waiting_score.sort(key=lambda x: x[1])
        #     analytic_list_throughput_score.sort(key=lambda x: x[1])
        #     plt.xlabel("traffic volume score")
        #     plt.ylabel("waiting_score/throughput_score")
        #     plt.plot(*zip(*analytic_list_waiting_score), label="waiting_score")
        #     plt.plot(*zip(*analytic_list_throughput_score), label="throughput_score")
        #     plt.savefig('analytics3000framesv2.0.png', bbox_inches='tight')
        #     plt.show()
        #
        #     break

        annotated_frame = results[0].plot()
        # print(len(vehicles_in_roi1), vehicles_in_roi1)
        # print(len(vehicles_in_roi2), vehicles_in_roi2)
        # print(len(vehicles_in_roi3), vehicles_in_roi3)
        # print(len(vehicles_in_roi4), vehicles_in_roi4)

        cv2.polylines(annotated_frame, [np.array(roi1)], True, (255, 0, 0, 125), 2)
        cv2.polylines(annotated_frame, [np.array(roi2)], True, (0, 255, 0, 125), 2)
        cv2.polylines(annotated_frame, [np.array(roi3)], True, (255, 0, 255, 125), 2)
        cv2.polylines(annotated_frame, [np.array(roi4)], True, (0, 0, 255, 125), 2)
        cv2.polylines(annotated_frame, [np.array(roi_central)], True, (0, 255, 255, 125), 2)

        for roi in [vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4]:
            for track in roi:
                cv2.circle(annotated_frame, (int(track[2][0]), int(track[2][1])), radius=5, color=(0, 0, 255),
                           thickness=-1)
        print('Frame:', real_frame_number)
        cv2.imwrite('currentframe.jpg', annotated_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('currentframe.jpg', 'rb').read() + b'\r\n')


def video_feed_1(request):
    return StreamingHttpResponse(stream_1(), content_type='multipart/x-mixed-replace; boundary=frame')


def vehicle_counted(vehicle_id, vehicle_list):
    for item in vehicle_list:
        if item[1] == vehicle_id:
            return True
    return False


def roi_tracking(results, roi_list, vehicles_in_intersection):
    roi1 = roi_list[0]
    roi2 = roi_list[1]
    roi3 = roi_list[2]
    roi4 = roi_list[3]
    roi_central = roi_list[4]

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
            center_point = (bbox[0], bbox[1])
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
            elif cv2.pointPolygonTest(np.array(roi_central), center_track_id_map[k], False) > 0:
                if not vehicle_counted(int(k), vehicles_in_intersection):
                    vehicles_in_intersection.append([CLASS_NAMES[str(int(class_id))], int(k), center_track_id_map[k]])
    else:
        track_ids_list = []
    return vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection, track_ids_list


def get_waiting_score(roi_list, waiting_score):
    for i in range(len(trafficLightControlResponseList)):
        if trafficLightControlResponseList[i] == 1:
            for vehicle in roi_list[i]:
                waiting_score += WAITING_SCORE_PENALTY[vehicle[0]]
    return waiting_score


def get_throughput_score(vehicles_in_intersection, frame_number):
    return (float(len(vehicles_in_intersection)) * FRAME_RATE) / float(frame_number)


def control_traffic_lights(roi_list, waiting_score, frame_number):
    global trafficLightControlResponseList

    throughput_score = 0
    traffic_volume_score = 0
    # wait for status update to be valid
    if not trafficLightControlStatus == 0:
        frame_number += 1
        throughput_score = get_throughput_score(roi_list[4], frame_number)
        waiting_score = get_waiting_score(roi_list, waiting_score)
        print('throughput_score:', throughput_score, '; waiting_score:', waiting_score, ';')
        if waiting_score != 0:
            traffic_volume_score = throughput_score / waiting_score
            print('traffic_volume_score: ', traffic_volume_score)
            if traffic_volume_score < TRAFFIC_TOGGLE_THRESHOLD:
                toggle_traffic_lights()
                frame_number = 0
        else:
            traffic_volume_score = 100
            print('traffic_volume_score: ', traffic_volume_score)

    return waiting_score, throughput_score, traffic_volume_score, frame_number


def toggle_traffic_lights():
    global trafficLightControlResponseList
    global trafficLightControlStatus
    trafficLightControlResponseList[0] = not trafficLightControlResponseList[0]
    trafficLightControlResponseList[1] = not trafficLightControlResponseList[1]
    trafficLightControlResponseList[2] = not trafficLightControlResponseList[2]
    trafficLightControlResponseList[3] = not trafficLightControlResponseList[3]
    # trafficLightControlStatus = 0
