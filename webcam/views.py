import asyncio

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from django.http.response import StreamingHttpResponse
from rest_framework.response import Response

from webcam import utils
from webcam.intersection import Intersection, AvgWaitingTimeDataPoint, AvgVehicleThroughputDataPoint, IntersectionEntry
from webcam.models import IntersectionModel, UserProfileModel, AvgWaitingTimeDataPointModel, \
    AvgVehicleThroughputDataPointModel
from webcam.traffic_light_controller_service import toggle_traffic_lights
from webcam.utils import logger_main
from webcam.websocket_connection_manager import send_pi_request, pi_connection_manager

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
from webcam.serializers import RegisterSerializer, UserDetailSerializer


# HOME PAGE -------------------------
def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))

# -----------------------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # Allow any user (even unauthenticated) to access this view
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    An endpoint to get data for the currently authenticated user.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserDetailSerializer
    #
    # def get_object(self):
    #     return self.request.user

    def get_object(self):
        # Get the username from the URL's keyword arguments
        username = self.kwargs.get('username')
        try:
            obj = get_object_or_404(self.get_queryset(), username__iexact=username)
            obj.profile = get_object_or_404(UserProfileModel, user_id=obj.id)
            return obj
        except Exception as e:
            logger_main.exception(e)
            return None

#? REST API ENDPOINTS

#! GET REQUESTS -------------------------
@api_view(['GET'])
def get_statistics(request, intersection_id):
    try:
        avg_waiting_time_data = AvgWaitingTimeDataPoint.load_from_db(intersection_id)
        avg_vehicle_throughput_data = AvgVehicleThroughputDataPoint.load_from_db(intersection_id)
        entries = IntersectionEntry.load_from_db(intersection_id)

        entries.sort(key=lambda entry: entry.entry_number)

        data = {
            "avgWaitingTimeData": avg_waiting_time_data[0].to_json() if len(avg_waiting_time_data) != 0 else {},
            "avgVehicleThroughputData": avg_vehicle_throughput_data[0].to_json() if len(avg_vehicle_throughput_data) != 0 else {},
            "entriesTrafficScores": {f"entry{entry.entry_number}": entry.to_json()["trafficScore"] if entry else 0 for entry in entries},
            "intersectionConnectionStatus": pi_connection_manager.is_connected()
        }

        return Response(data, status=status.HTTP_200_OK)
    except IntersectionModel.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger_main.exception(f"Error retrieving statistics: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while retrieving intersection."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_current_intersection_status(request):
    current_pi_update = pi_connection_manager.get_pi_request_data()
    return Response(
        {
            "connected": pi_connection_manager.is_connected(),
            "state": current_pi_update.to_json()
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_intersection(request, intersection_id):
    try:
        intersection_obj = Intersection.load_from_db(intersection_id)
        if intersection_obj:
            return Response(intersection_obj.to_json(), status=status.HTTP_200_OK)
        return Response({"error": "Intersection not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger_main.exception(f"Error retrieving intersection: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while retrieving intersection."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_all_intersections(request):
    """
    Retrieves all Intersection objects from the database.
    """
    try:
        intersection_models = IntersectionModel.objects.all()

        all_intersections_data = []
        for model_instance in intersection_models:
            intersection_obj = Intersection.load_from_db(model_instance.id)
            if intersection_obj:
                all_intersections_data.append(intersection_obj.to_json())

        return Response(all_intersections_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger_main.exception(f"Error retrieving all intersections: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while retrieving intersections."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#! POST REQUESTS -------------------------
@api_view(['POST'])
def post_reset_intersection_statistics(request, intersection_id):
    try:
        AvgWaitingTimeDataPointModel.objects.filter(intersection_id=intersection_id).delete()
        AvgVehicleThroughputDataPointModel.objects.filter(intersection_id=intersection_id).delete()
        return Response(status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger_main.exception(f"Error resetting intersection statistics: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while resetting intersection statistics."}
                        , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def post_traffic_light_toggle(request):
    try:
        current_pi_update = pi_connection_manager.get_pi_request_data()
        toggle_traffic_lights(current_pi_update["STATE"])
        return Response(status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger_main.exception(f"Error toggling traffic lights: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while toggling traffic lights."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def post_traffic_light_all_red(request):
    try:
        current_pi_update = pi_connection_manager.get_pi_request_data()
        message_payload = {
            "action": "Resume" if current_pi_update["STATE"] == 'AllRed' else "AllRed",
            "direction": ""
        }
        send_pi_request(message_payload)
        return Response(status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger_main.exception(f"Error setting all lights to red: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while setting all lights to red."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def post_traffic_light_hazard_mode(request):
    try:
        current_pi_update = pi_connection_manager.get_pi_request_data()
        message_payload = {
            "action": "Resume" if current_pi_update["STATE"] == 'ALL_YELLOW' else "HazardMode",
            "direction": ""
        }
        send_pi_request(message_payload)
        return Response(status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger_main.exception(f"Error setting hazard mode: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while setting hazard mode."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def post_traffic_lights_off(request):
    try:
        current_pi_update = pi_connection_manager.get_pi_request_data()
        message_payload = {
            "action": "Resume" if current_pi_update["STATE"] == 'ALL_OFF' else "AllOff",
            "direction": ""
        }
        send_pi_request(message_payload)
        return Response(status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger_main.exception(f"Error turning off traffic lights: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while turning off traffic lights."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def post_traffic_light_resume(request):
    try:
        send_pi_request(message_payload={
            "action": "Resume",
            "direction": ""
        })
        return Response(status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger_main.exception(f"Error resuming traffic lights: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while resuming traffic lights."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def post_traffic_light_toggle_smart_algorithm(request, intersection_id):
    try:
        if IntersectionModel.objects.filter(id=intersection_id).exists():
            intersection_obj = Intersection.load_from_db(intersection_id)
            intersection_obj.is_smart_algorithm_enabled = not intersection_obj.is_smart_algorithm_enabled
            intersection_obj.save_to_db()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger_main.exception(f"Error toggling smart algorithm for intersection {intersection_id}: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred while toggling smart algorithm."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_intersection(request):
    try:
        intersection_obj = Intersection.from_json(request.data)
        intersection_model_instance = intersection_obj.save_to_db()
        return Response(
            {"message": "Intersection processed successfully.", "id": intersection_model_instance.id},
            status=status.HTTP_201_CREATED
        )
    except ValueError as ve:
        return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Log the full error for debugging
        logger_main.error(f"Error in create_intersection: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#! PUT REQUESTS (for updates) -------------------------
@api_view(['PUT'])
def update_intersection(request, intersection_id):
    try:
        # Check if the intersection exists
        if not IntersectionModel.objects.filter(id=intersection_id).exists():
            return Response({"error": f"Intersection with id '{intersection_id}' not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the 'id' in the request body matches the URL, or is not present (to avoid confusion)
        request_data_id = request.data.get('id')
        if request_data_id and request_data_id != intersection_id:
            return Response({"error": f"Intersection ID in URL ('{intersection_id}') does not match ID in request body ('{request_data_id}')."},
                            status=status.HTTP_400_BAD_REQUEST)

        # If 'id' is not in request.data, add it from the URL to ensure from_json works as expected
        if 'id' not in request.data:
            request.data['id'] = intersection_id

        intersection_obj = Intersection.from_json(request.data)

        intersection_model_instance = intersection_obj.save_to_db()

        return Response(
            {"message": "Intersection updated successfully.", "id": intersection_model_instance.id},
            status=status.HTTP_200_OK
        )
    except ValueError as ve:
        return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger_main.error(f"Error in update_intersection: {e}", exc_info=True)
        return Response({"error": "An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#! DELETE REQUESTS ------------------------------------

@api_view(['DELETE'])
def delete_intersection(request, intersection_id):
    if Intersection.delete_from_db(intersection_id):
        return Response({"message": "Intersection deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    return Response({"error": "Failed to delete intersection or not found"}, status=status.HTTP_404_NOT_FOUND)

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
                logger_main.debug(f"Stream: Yielding frame (length: {len(frame_bytes_to_send)})") # DEBUG
                printed_yielding_message = True
            printed_no_frame_message = False

        else:
            if not printed_no_frame_message:
                logger_main.debug("Stream: No frame ready in latest_processed_frame_bytes will sleep.") # DEBUG
                printed_no_frame_message = True
            printed_yielding_message = False
            pass  # Avoid printing too much if no frame is ready immediately

        await asyncio.sleep(1.0/20)  # Adjust FPS as needed (e.g., 20 FPS) for ASGI
        # time.sleep(1.0 / 20)  # Adjust FPS as needed (e.g., 20 FPS)



def video_feed(request):
    return StreamingHttpResponse(generate_frames_for_stream(), content_type='multipart/x-mixed-replace; boundary=frame')
