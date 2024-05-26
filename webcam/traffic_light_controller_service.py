from webcam import api_variables, constants


def get_waiting_score(roi_list, waiting_score):
    for i in range(len(api_variables.trafficLightControlResponseList)):
        if api_variables.trafficLightControlResponseList[i] == 1:
            for vehicle in roi_list[i]:
                waiting_score += constants.WAITING_SCORE_PENALTY[vehicle[0]]
    return waiting_score


def get_throughput_score(vehicles_in_intersection, frame_number):
    return (float(len(vehicles_in_intersection)) * constants.FRAME_RATE) / float(frame_number)


def control_traffic_lights(roi_list, waiting_score, frame_number):
    throughput_score = 0
    traffic_volume_score = 0
    # wait for status update to be valid
    if not api_variables.trafficLightControlStatus == 0:
        frame_number += 1
        throughput_score = get_throughput_score(roi_list[4], frame_number)
        waiting_score = get_waiting_score(roi_list, waiting_score)
        if waiting_score != 0:
            traffic_volume_score = throughput_score / waiting_score
            if traffic_volume_score < constants.TRAFFIC_TOGGLE_THRESHOLD:
                toggle_traffic_lights()
                frame_number = 0
                throughput_score = 0
        else:
            traffic_volume_score = 100

        print('throughput_score:', throughput_score, '; waiting_score:', waiting_score, ';')
        print('traffic_volume_score: ', traffic_volume_score)

    return waiting_score, throughput_score, traffic_volume_score, frame_number


def toggle_traffic_lights():
    api_variables.trafficLightControlResponseList[0] = not api_variables.trafficLightControlResponseList[0]
    api_variables.trafficLightControlResponseList[1] = not api_variables.trafficLightControlResponseList[1]
    api_variables.trafficLightControlResponseList[2] = not api_variables.trafficLightControlResponseList[2]
    api_variables.trafficLightControlResponseList[3] = not api_variables.trafficLightControlResponseList[3]
    api_variables.trafficLightControlStatus = 0
