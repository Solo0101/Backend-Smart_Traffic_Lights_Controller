import asyncio
import time

from django.http import HttpResponse
from django.template import loader
from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from webcam.utils import latest_processed_frame_bytes, frame_lock

import cv2

from webcam import constants, utils
from webcam.traffic_light_controller_service import control_traffic_lights, debugging_print_vehicles_in_rois, draw_debugging_dot_to_calculated_tracked_car
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

# MODIFIED DISPLAY CAMERA  ------------------
async def generate_frames_for_stream():
    """
    Generator function to yield the latest processed frame.
    """
    # while True:
    #     with utils.frame_lock:
    #         yield (b'--frame\r\n'
    #          b'Content-Type: image/jpeg\r\n\r\n' + open('webcam/images/currentframe.jpg', 'rb').read() + b'\r\n')

    while True:
        frame_bytes_to_send = None
        with utils.frame_lock:  # Use the lock imported from utils
            if utils.latest_processed_frame_bytes:  # Use the variable imported from utils
                frame_bytes_to_send = utils.latest_processed_frame_bytes[0]
                utils.latest_processed_frame_bytes.pop()  # Remove the processed frame from the list
                # print("Stream: Acquired frame from latest_processed_frame_bytes.") # DEBUG

        if frame_bytes_to_send is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + bytearray(frame_bytes_to_send) + b'\r\n')
            print(f"Stream: Yielding frame (length: {len(frame_bytes_to_send)})") # DEBUG

        else:
            print("Stream: No frame ready in latest_processed_frame_bytes will sleep.") # DEBUG
            pass  # Avoid printing too much if no frame is ready immediately

        await asyncio.sleep(1.0/20)  # Adjust FPS as needed (e.g., 20 FPS) for ASGI
        # time.sleep(1.0 / 20)  # Adjust FPS as needed (e.g., 20 FPS)
        # time.sleep(2)  # Adjust FPS as needed (e.g., 20 FPS)



def video_feed(request):
    return StreamingHttpResponse(generate_frames_for_stream(), content_type='multipart/x-mixed-replace; boundary=frame')
