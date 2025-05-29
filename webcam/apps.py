import logging
import os
import threading
import time

from django.apps import AppConfig

import cv2

from webcam import constants
from webcam.traffic_light_controller_service import control_traffic_lights, debugging_print_vehicles_in_rois, draw_debugging_dot_to_calculated_tracked_car
from webcam.constants import model
from webcam.yolo_roi_tracker import roi_tracking, draw_rois
from webcam.utils import check_wanted_classes, save_plot_analytics, get_video_stream, get_frame, frame_lock, \
    latest_processed_frame_bytes, logger_main, logger_background


def background_processing_loop():

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
        try:
            waiting_score = 0

            # Acquiring the frame from the video stream and resizing it
            frame = get_frame(vid)
            if frame is None:
                continue
            frame = cv2.resize(frame, (1000, 700))
            real_frame_number += 1
            logger_background.debug('Frame: %s', str(real_frame_number))

            # Get the result from the image object tracking
            results = model.track(frame, persist=True, classes=custom_class_ids, conf=0.1, iou=0.1,
                                  tracker="webcam/models/yolo/bytetrack.yaml")

            # The Process got results
            (vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection,
             track_ids_list) = roi_tracking(
                results,
                [roi1,
                 roi2,
                 roi3,
                 roi4,
                 roi_central])

            # Hardcoded traffic controller
            [vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4,
             vehicles_in_intersection], waiting_score, throughput_score, traffic_volume_score, frame_number = control_traffic_lights(
                [vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection],
                waiting_score, real_frame_number, frame_number)

            # Smart traffic controller
            # TODO: Implement method

            # Display resulted an object tracking bounding boxes
            annotated_frame = results[0].plot()

            # Logging list of vehicles in rois
            debugging_print_vehicles_in_rois(
                [vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection])

            # Display auxiliary information
            if constants.ENABLE_ANALYTICS_PLOTTING:
                save_plot_analytics(traffic_volume_score, waiting_score, throughput_score, analytic_list_waiting_score,
                                    analytic_list_throughput_score)

            if constants.DISPLAY_ROIS:
                annotated_frame = draw_rois(annotated_frame, roi1, roi2, roi3, roi4, roi_central)

            # Draw center points of vehicles that are on rois before entering the intersection
            draw_debugging_dot_to_calculated_tracked_car(
                [vehicles_in_roi1, vehicles_in_roi2, vehicles_in_roi3, vehicles_in_roi4, vehicles_in_intersection],
                annotated_frame)

            # Display processed frame
            with frame_lock:
                _, annotated_frame_bytes = cv2.imencode(".jpg", annotated_frame)
                latest_processed_frame_bytes.append(annotated_frame_bytes)
                # latest_processed_frame_bytes.append(annotated_frame)
            cv2.imwrite('webcam/images/currentframe.jpg', annotated_frame)



        except Exception as e:
            logger_background.debug(f"Error in background_processing_loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)  # Wait before retrying after an error


class WebcamConfig(AppConfig):
    name = 'webcam'

    def ready(self):
        # This check prevents the thread from starting multiple times during development
        # when the reloader is active.
        if os.environ.get('RUN_MAIN') or os.environ.get('WERKZEUG_RUN_MAIN'):
            main_thread = threading.current_thread()
            main_thread.name = str("MainThread")
            logger_main.debug("Starting background image processing thread...")
            processing_thread = threading.Thread(target=background_processing_loop, daemon=True, name="BackgroundThread")
            processing_thread.start()
            logger_main.debug("Background image processing thread started.")
