import asyncio
import time

from django.http import HttpResponse
from django.template import loader
from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from webcam import utils
import webcam.api_variables
from webcam.utils import logger_background


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

    printed_yielding_message = False
    printed_no_frame_message = False

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
            if not printed_yielding_message:
                logger_background.debug(f"Stream: Yielding frame (length: {len(frame_bytes_to_send)})") # DEBUG
                printed_yielding_message = True
            printed_no_frame_message = False

        else:
            if not printed_no_frame_message:
                logger_background.debug("Stream: No frame ready in latest_processed_frame_bytes will sleep.") # DEBUG
                printed_no_frame_message = True
            printed_yielding_message = False
            pass  # Avoid printing too much if no frame is ready immediately

        await asyncio.sleep(1.0/20)  # Adjust FPS as needed (e.g., 20 FPS) for ASGI
        # time.sleep(1.0 / 20)  # Adjust FPS as needed (e.g., 20 FPS)



def video_feed(request):
    return StreamingHttpResponse(generate_frames_for_stream(), content_type='multipart/x-mixed-replace; boundary=frame')
