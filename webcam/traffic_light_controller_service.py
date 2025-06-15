import time

import cv2
import numpy as np

from webcam import constants
from webcam.constants import CURRENT_STATE_DICT
from webcam.utils import logger_background
from webcam.websocket_connection_manager import send_pi_request, pi_connection_manager

def get_delta_new_cars_in_intersection_list(old_in_intersection_list, current_in_intersection_list):
    new_cars_in_intersection_list = []
    for vehicle in current_in_intersection_list:
        if vehicle[1] not in old_in_intersection_list:
            new_cars_in_intersection_list.append(vehicle)
    return new_cars_in_intersection_list

def get_action_direction(current_pi_update):
    action_direction = ""
    match current_pi_update["STATE"]:
        case "NORTH_SOUTH_GREEN":
            action_direction = "NS"
        case "NORTH_SOUTH_YELLOW":
            action_direction = "NS"
        case "EAST_WEST_GREEN":
            action_direction = "EW"
        case "EAST_WEST_YELLOW":
            action_direction = "EW"
        case _:
            pass
    return action_direction

def get_waiting(roi_list, current_state, waiting_list):
    waiting_score=0
    if current_state == "ALL_YELLOW" or current_state == "ALL_OFF":
        for i in range(0, len(waiting_list), 1):
            waiting_list[i] = 0
    elif current_state == "NORTH_SOUTH_GREEN" or current_state == "NORTH_SOUTH_YELLOW":
        for i in range(0, len(roi_list)-1, 2):
            waiting_list[i * 2] = -(len(roi_list[i]) // -2)
            waiting_list[i * 2 + 1] = len(roi_list[i]) / 2
            waiting_list[i * 2 + 2] = 0
            waiting_list[i * 2 + 3] = 0
            for vehicle in roi_list[i]:
                waiting_score += constants.WAITING_SCORE_PENALTY[vehicle[0]]
    elif current_state == "EAST_WEST_GREEN" or current_state == "EAST_WEST_YELLOW":
        for i in range(1, len(roi_list)-1, 2):
            waiting_list[(i - 1) * 2] = 0
            waiting_list[(i - 1) * 2 + 1] = 0
            waiting_list[(i - 1) * 2 + 2] = -(len(roi_list[i]) // -2)
            waiting_list[(i - 1) * 2 + 2] = len(roi_list[i]) / 2
            for vehicle in roi_list[i]:
                waiting_score += constants.WAITING_SCORE_PENALTY[vehicle[0]]
    return waiting_score, waiting_list


def get_throughput_score(vehicles_in_intersection, frame_number):
    return (float(len(vehicles_in_intersection)) * constants.FRAME_RATE) / float(frame_number)

def toggle_traffic_lights(current_state):
    if current_state == "NORTH_SOUTH_GREEN":
        direction="NS"
    elif current_state == "EAST_WEST_GREEN":
        direction="EW"
    else: return

    send_pi_request(message_payload={
        "action": "Jump",
        "direction": f"{direction}Y"
    })

def edge_cases_optimizations_controller(roi_list, current_loop_time, last_smart_edge_cases_control_time):

    if (current_loop_time - last_smart_edge_cases_control_time) <= constants.EDGE_CASES_OPTIMIZATIONS_COOLDOWN: # Execute every 15 seconds
        return last_smart_edge_cases_control_time

    current_pi_update = pi_connection_manager.get_pi_request_data()
    waiting_score, _ = get_waiting(roi_list, current_pi_update["STATE"], [0, 0, 0, 0, 0, 0, 0, 0])

    if "YELLOW" in current_pi_update["STATE"]:
        return last_smart_edge_cases_control_time

    empty_rois = 0
    entry_number = 0
    for roi in roi_list:
        from webcam.models import IntersectionEntryModel
        IntersectionEntryModel.objects.filter(intersection_id=constants.INTERSECTION_ID, entry_number=entry_number).update(traffic_score=len(roi))

        if len(roi) == 0:
            empty_rois += 1
        entry_number += 1

    if empty_rois < 2:
        return last_smart_edge_cases_control_time

    potential_traffic_throughput_score = 0

    for i in range(int(current_pi_update["STATE"] == "NORTH_SOUTH_GREEN"), len(roi_list)-1, 2):
        for vehicle in roi_list[i]:
            potential_traffic_throughput_score += constants.WAITING_SCORE_PENALTY[vehicle[0]]

    if potential_traffic_throughput_score < waiting_score:
        toggle_traffic_lights(current_pi_update["STATE"])
        time.sleep(1.1)
        last_smart_edge_cases_control_time = current_loop_time

    return last_smart_edge_cases_control_time

def smart_control_traffic_lights(traffic_control_agent, roi_list, old_in_intersection_list, current_state, waiting_score, current_loop_time, last_smart_edge_cases_control_time, last_smart_control_time, waiting_list, toggle_actions_number):
    current_pi_update = pi_connection_manager.get_pi_request_data()
    waiting_score, waiting_list = get_waiting(roi_list, current_pi_update["STATE"], waiting_list)
    if (current_loop_time - last_smart_control_time) >= constants.SMART_CONTROL_INTERVAL and current_pi_update["STATE"] not in ["ALL_OFF", "ALL_YELLOW", "ALL_RED"]: # Execute every 1 second
        print(current_pi_update["STATE"])

        last_smart_edge_cases_control_time = edge_cases_optimizations_controller(roi_list, current_loop_time, last_smart_edge_cases_control_time) # If action taken has a cooldown of 15 seconds


        state_array = np.array(
            [-(len(roi_list[0]) // -2), len(roi_list[0]) / 2,
             -(len(roi_list[1]) // -2), len(roi_list[1]) / 2,
             -(len(roi_list[2]) // -2), len(roi_list[2]) / 2,
             -(len(roi_list[3]) // -2), len(roi_list[3]) / 2,
             len(get_delta_new_cars_in_intersection_list(old_in_intersection_list, roi_list[4])),
             waiting_score,
             CURRENT_STATE_DICT[current_state],
             int(current_loop_time),
             waiting_list[0], waiting_list[1], waiting_list[2], waiting_list[3],
             waiting_list[4], waiting_list[5], waiting_list[6], waiting_list[7]
             ])

        action = traffic_control_agent.act(state_array)

        next_state_array = state_array

        next_state_array[11] = CURRENT_STATE_DICT[current_pi_update["STATE"]]

        reward = state_array[8] - state_array[9]

        # Store experience
        traffic_control_agent.remember(state_array, action, reward, next_state_array)

        # Train the agent on the batched info
        traffic_control_agent.train()

        logger_background.info("Chosen action: %s", action)
        print("Chosen action:", action)

        action_direction = get_action_direction(current_pi_update)

        if current_state != current_pi_update["STATE"] and current_state in ["NORTH_SOUTH_GREEN", "EAST_WEST_GREEN"]:
            last_smart_edge_cases_control_time = current_loop_time
            toggle_actions_number += 1
            match action:
                case 0:
                    send_pi_request(message_payload={
                        "action": "Debug: Do Nothing",
                        "direction": ""
                    })
                case 1:
                    if current_pi_update[f"{action_direction}G"] < 60: # (max 60s)
                        send_pi_request(message_payload={
                            "action": "Increase",
                            "direction": f"{action_direction}"
                        })
                case 2:
                    if current_pi_update[f"{action_direction}G"] > 10: # (min 10s)
                        send_pi_request(message_payload={
                            "action": "Decrease",
                            "direction": f"{action_direction}"
                        })

        old_in_intersection_list = roi_list[4]
        last_smart_control_time = current_loop_time
        current_state = current_pi_update["STATE"]

    return last_smart_edge_cases_control_time, last_smart_control_time, old_in_intersection_list, current_state, waiting_score, waiting_list, toggle_actions_number, len(get_delta_new_cars_in_intersection_list(old_in_intersection_list, roi_list[4]))

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
            if i < 4 and i % 2 == int(pi_connection_manager.get_pi_request_data()["STATE"] == "EAST_WEST_GREEN"):
                cv2.circle(annotated_frame, (int(track[2][0]), int(track[2][1])), radius=5, color=(0, 0, 255),
                        thickness=-1)
            elif i < 4 and i % 2 == int(pi_connection_manager.get_pi_request_data()["STATE"] == "NORTH_SOUTH_GREEN"):
                cv2.circle(annotated_frame, (int(track[2][0]), int(track[2][1])), radius=5, color=(0, 255, 0),
                           thickness=-1)
            if i == 4:
                cv2.circle(annotated_frame, (int(track[2][0]), int(track[2][1])), radius=5, color=(255, 0, 0),
                        thickness=-1)