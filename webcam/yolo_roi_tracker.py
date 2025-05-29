import cv2
import numpy as np
import torch

from webcam import constants


def vehicle_counted(vehicle_id, vehicle_list):
    for item in vehicle_list:
        if item[1] == vehicle_id:
            return True
    return False


def draw_rois(annotated_frame, roi1, roi2, roi3, roi4, roi_central):
    cv2.polylines(annotated_frame, [np.array(roi1)], True, (255, 0, 0, 125), 2)
    cv2.polylines(annotated_frame, [np.array(roi2)], True, (0, 255, 0, 125), 2)
    cv2.polylines(annotated_frame, [np.array(roi3)], True, (255, 0, 255, 125), 2)
    cv2.polylines(annotated_frame, [np.array(roi4)], True, (0, 0, 255, 125), 2)
    cv2.polylines(annotated_frame, [np.array(roi_central)], True, (0, 255, 255, 125), 2)
    return annotated_frame


def update_vehicle_in_rois_list(roi1, roi2, roi3, roi4, roi_central, center_track_id_map, track_id, class_id, vehicles_in_roi1,
                                vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection):
    if cv2.pointPolygonTest(np.array(roi1), center_track_id_map[track_id], False) > 0:
        vehicles_in_roi1.append([constants.CLASS_NAMES[str(int(class_id))], int(track_id), center_track_id_map[track_id]])
    elif cv2.pointPolygonTest(np.array(roi2), center_track_id_map[track_id], False) > 0:
        vehicles_in_roi2.append([constants.CLASS_NAMES[str(int(class_id))], int(track_id), center_track_id_map[track_id]])
    elif cv2.pointPolygonTest(np.array(roi3), center_track_id_map[track_id], False) > 0:
        vehicles_in_roi3.append([constants.CLASS_NAMES[str(int(class_id))], int(track_id), center_track_id_map[track_id]])
    elif cv2.pointPolygonTest(np.array(roi4), center_track_id_map[track_id], False) > 0:
        vehicles_in_roi4.append([constants.CLASS_NAMES[str(int(class_id))], int(track_id), center_track_id_map[track_id]])
    elif cv2.pointPolygonTest(np.array(roi_central), center_track_id_map[track_id], False) > 0:
        vehicles_in_intersection.append([constants.CLASS_NAMES[str(int(class_id))], int(track_id), center_track_id_map[track_id]])

    return vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection


def roi_tracking(results, roi_list):
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
    vehicles_in_intersection = []

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
        for track_id, class_id in zip(center_track_id_map, class_ids):
            vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection = (
                update_vehicle_in_rois_list(
                    roi1,
                    roi2,
                    roi3,
                    roi4,
                    roi_central,
                    center_track_id_map,
                    track_id, class_id,
                    vehicles_in_roi1,
                    vehicles_in_roi2,
                    vehicles_in_roi3,
                    vehicles_in_roi4,
                    vehicles_in_intersection))
    else:
        track_ids_list = []
    return (vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4,
            vehicles_in_intersection, track_ids_list)
