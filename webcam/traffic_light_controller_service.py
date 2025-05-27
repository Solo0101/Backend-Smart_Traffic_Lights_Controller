import cv2

from webcam import api_variables, constants
from webcam.utils import logger_background


def get_waiting_score(roi_list, waiting_score):
    for i in range(len(api_variables.trafficLightControlResponseList)):
        if api_variables.trafficLightControlResponseList[i] == 1:
            for vehicle in roi_list[i]:
                waiting_score += constants.WAITING_SCORE_PENALTY[vehicle[0]]
    return waiting_score


def get_throughput_score(vehicles_in_intersection, frame_number):
    return (float(len(vehicles_in_intersection)) * constants.FRAME_RATE) / float(frame_number)


def control_traffic_lights(roi_list, waiting_score, real_frame_number, frame_number):
    throughput_score = 0
    traffic_volume_score = 0
    # wait for a status update to be valid
    if not api_variables.trafficLightControlStatus == 0:
        frame_number += 1
        throughput_score = get_throughput_score(roi_list[4], frame_number)
        waiting_score = get_waiting_score(roi_list, waiting_score)
        if waiting_score != 0:
            traffic_volume_score = throughput_score / waiting_score
            if traffic_volume_score < constants.TRAFFIC_TOGGLE_THRESHOLD and real_frame_number % 150 == 0: #TODO Refactor with constant to put a name for total time in which it can not toggle after another toggle
                toggle_traffic_lights()
                logger_background.debug("TRAFFIC LIGHTS TOGGLED! \n")
                frame_number = 0
                throughput_score = 0
                waiting_score = 0
                traffic_volume_score = 0
                roi_list[4] = []
        else:
            traffic_volume_score = 100

    logger_background.debug('throughput_score: %s; waiting_score: %s; \ntraffic_volume_score: %s', str(throughput_score), str(waiting_score), str(traffic_volume_score))

    return roi_list, waiting_score, throughput_score, traffic_volume_score, frame_number


def toggle_traffic_lights():
    api_variables.trafficLightControlResponseList[0] = not api_variables.trafficLightControlResponseList[0]
    api_variables.trafficLightControlResponseList[1] = not api_variables.trafficLightControlResponseList[1]
    api_variables.trafficLightControlResponseList[2] = not api_variables.trafficLightControlResponseList[2]
    api_variables.trafficLightControlResponseList[3] = not api_variables.trafficLightControlResponseList[3]
    api_variables.trafficLightControlStatus = 1

def debugging_print_vehicles_in_rois(roi_list):
    if constants.ENABLE_VEHICLES_IN_ROIS_LOGGING:
        debug_string = ("\n" + str(len(roi_list[0])) + " " + str(roi_list[0]) +
                        "\n" + str(len(roi_list[1])) + " " + str(roi_list[1]) +
                        "\n" + str(len(roi_list[2])) + " " + str(roi_list[2]) +
                        "\n" + str(len(roi_list[3])) + " " + str(roi_list[3]) +
                        "\n" + str(len(roi_list[4])) + " " + str(roi_list[4]) + "\n")
        logger_background.debug(debug_string)

def draw_debugging_dot_to_calculated_tracked_car(roi_list, annotated_frame):
    for i in range(len(roi_list)):
        for track in roi_list[i]:
            if i < 4 and api_variables.trafficLightControlResponseList[i] == 0:
                cv2.circle(annotated_frame, (int(track[2][0]), int(track[2][1])), radius=5, color=(0, 0, 255),
                        thickness=-1)
            elif i < 4 and api_variables.trafficLightControlResponseList[i] == 1:
                cv2.circle(annotated_frame, (int(track[2][0]), int(track[2][1])), radius=5, color=(0, 255, 0),
                           thickness=-1)
            if i == 4:
                cv2.circle(annotated_frame, (int(track[2][0]), int(track[2][1])), radius=5, color=(255, 0, 0),
                        thickness=-1)