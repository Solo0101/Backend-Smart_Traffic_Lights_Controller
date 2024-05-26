from django.http import HttpResponse
from django.template import loader
from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

import cv2

from webcam import constants
from webcam.traffic_light_controller_service import control_traffic_lights
from webcam.constants import model
from webcam.yolo_roi_tracker import roi_tracking, draw_rois
from webcam.utils import check_wanted_classes, save_plot_analytics, get_video_stream, get_frame
import webcam.api_variables


# HOME PAGE -------------------------
def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))


# -----------------------------------

# REST API ENDPOINTS

# GET REQUEST -------------------------
@api_view(['GET'])
def get_traffic_light_control_response(request):
    return Response(data=webcam.api_variables.trafficLightControlResponseList, status=status.HTTP_200_OK)


# POST REQUEST -------------------------
@api_view(['POST'])
def post_traffic_light_control_status(request):
    webcam.api_variables.trafficLightControlStatus = request.data['trafficLightControlStatus']
    return Response(status=status.HTTP_202_ACCEPTED)


# -----------------------------------

# DISPLAY CAMERA  ------------------

def stream():
    custom_class_ids = []

    for k in constants.CUSTOM_CLASS_NAMES:
        if check_wanted_classes(k):
            custom_class_ids.append(int(k))

    # getting rois
    roi1 = constants.ROI1
    roi2 = constants.ROI2
    roi3 = constants.ROI3
    roi4 = constants.ROI4
    roi_central = constants.ROI_CENTRAL

    vehicles_in_intersection = []
    frame_number = 0
    real_frame_number = 0
    analytic_list_waiting_score = []
    analytic_list_throughput_score = []

    vid = get_video_stream()

    while True:
        waiting_score = 0

        # Acquiring the frame from the video stream and resizing it
        frame = get_frame(vid)
        frame = cv2.resize(frame, (1000, 700))
        real_frame_number += 1
        print('Frame:', real_frame_number)

        # Get the result from the image object tracking
        results = model.track(frame, persist=True, classes=custom_class_ids, conf=0.1, iou=0.1,
                              tracker="webcam/models/yolo/bytetrack.yaml")

        # Process the obtained results
        (vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection,
         track_ids_list) = roi_tracking(
            results,
            [roi1,
             roi2,
             roi3,
             roi4,
             roi_central], vehicles_in_intersection)

        waiting_score, throughput_score, traffic_volume_score, frame_number = control_traffic_lights(
            [vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection],
            waiting_score, frame_number)

        # Display resulted object tracking bounding boxes
        annotated_frame = results[0].plot()

        # Logging list of vehicles in rois
        # if constants.ENABLE_VEHICLES_IN_ROIS_LOGGING:
        #     print(len(vehicles_in_roi1), vehicles_in_roi1)
        #     print(len(vehicles_in_roi2), vehicles_in_roi2)
        #     print(len(vehicles_in_roi3), vehicles_in_roi3)
        #     print(len(vehicles_in_roi4), vehicles_in_roi4)

        # Display auxiliary information
        if constants.ENABLE_ANALYTICS_PLOTTING:
            save_plot_analytics(traffic_volume_score, waiting_score, throughput_score, analytic_list_waiting_score,
                                analytic_list_throughput_score)

        if constants.DISPLAY_ROIS:
            annotated_frame = draw_rois(annotated_frame, roi1, roi2, roi3, roi4, roi_central)

        # Draw center points of vehicles that are on rois before entering the intersection
        for roi in [vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4]:
            for track in roi:
                cv2.circle(annotated_frame, (int(track[2][0]), int(track[2][1])), radius=5, color=(0, 0, 255),
                           thickness=-1)

        # Display processed frame
        cv2.imwrite('webcam/images/currentframe.jpg', annotated_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('webcam/images/currentframe.jpg', 'rb').read() + b'\r\n')


def video_feed(request):
    return StreamingHttpResponse(stream(), content_type='multipart/x-mixed-replace; boundary=frame')
