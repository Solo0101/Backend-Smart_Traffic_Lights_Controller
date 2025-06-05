import asyncio

from django.http import HttpResponse
from django.template import loader
from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from webcam import utils
from webcam.traffic_light_controller_service import toggle_traffic_lights
from webcam.utils import logger_background
from webcam.websocket_connection_manager import send_pi_request, pi_connection_manager


# HOME PAGE -------------------------
def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))

# -----------------------------------

#? REST API ENDPOINTS
#TODO: Create Intersection class to handle statistics and smart algorithm toggle endpoint +  for housekeeping purposes
#TODO: Create more response options and codes if needed

#! GET REQUESTS -------------------------
@api_view(['GET'])
def get_statistics(request):
    #TODO: Implement
    pass

def get_current_intersection_status(request):
    current_pi_update = pi_connection_manager.get_pi_request_data()
    return Response(current_pi_update.to_json(), status=status.HTTP_200_OK)

#! POST REQUESTS -------------------------
@api_view(['POST'])
def post_traffic_light_toggle(request):
    current_pi_update = pi_connection_manager.get_pi_request_data()
    toggle_traffic_lights(current_pi_update["STATE"])
    return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
def post_traffic_light_all_red(request):
    send_pi_request(message_payload={
        "action": "AllRed",
        "direction": ""
    })
    return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
def post_traffic_light_hazard_mode(request):
    send_pi_request(message_payload={
        "action": "HazardMode",
        "direction": ""
    })
    return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
def post_traffic_lights_off(request):
    send_pi_request(message_payload={
        "action": "AllOff",
        "direction": ""
    })
    return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
def post_traffic_light_resume(request):
    send_pi_request(message_payload={
        "action": "Resume",
        "direction": ""
    })
    return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
def post_traffic_light_toggle_smart_algorithm(request):
    # intersectionManager.toggle_smart_intersection_algorithm()
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
                print("Stream: Acquired frame from background processing thread.") # DEBUG

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
