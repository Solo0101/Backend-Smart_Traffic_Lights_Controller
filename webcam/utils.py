"""Utilities for logging."""
import collections
import datetime
import os
import re
import threading

import cv2
import numpy as np
import logging
import time
import base64

import torch
from matplotlib import pyplot as plt
from ultralytics import YOLO
from vidgear.gears import VideoGear

from webcam import constants
# from webcam.intersection import AvgWaitingTimeDataPoint, AvgVehicleThroughputDataPoint

ALPHA = 0.5
FONT = cv2.FONT_HERSHEY_PLAIN
TEXT_SCALE = 1.0
TEXT_THICKNESS = 1
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
if os.getenv('LOG_LEVEL') == 'DEBUG':
    level = logging.DEBUG
elif os.getenv('LOG_LEVEL') == 'INFO':
    level = logging.INFO
elif os.getenv('LOG_LEVEL') == 'ERROR':
    level = logging.ERROR
else:
    level = logging.ERROR
logging.basicConfig(
    level=level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

folder_regex = re.compile('imgs/webcam|imgs/pi')

latest_processed_frame_bytes = collections.deque(maxlen=1)
frame_lock = threading.Lock()

logger_main = logging.getLogger('app_main_thread_logger')
logger_background = logging.getLogger('app_background_thread_logger')

class ThreadNameFilter(logging.Filter):
    def filter(self, record):
        record.threadName = threading.current_thread().name
        return True

def timeit(method):
    def timed(*args, **kw):
        global logger
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        logger = logging.getLogger(method.__name__)
        logger.debug('{} {:.3f} sec'.format(method.__name__, te - ts))
        return result

    return timed


def img_to_base64(img):
    """encode as a jpeg image and return it"""
    buffer = cv2.imencode('.jpg', img)[1].tobytes()
    jpg_as_text = base64.b64encode(buffer)
    base64_string = jpg_as_text.decode('utf-8')
    return base64_string


def draw_boxed_text(img, text, topleft, color):
    """Draw a translucent boxed text in white, overlayed on top of a
    colored patch surrounded by a black border. FONT, TEXT_SCALE,
    TEXT_THICKNESS and ALPHA values are constants (fixed) as defined
    on top.

    # Arguments
      img: the input image as a numpy array.
      text: the text to be drawn.
      topleft: XY coordinate of the topleft corner of the boxed text.
      color: color of the patch, i.e., background of the text.

    # Output
      img: note the original image is modified in place.
    """
    assert img.dtype == np.uint8
    img_h, img_w, _ = img.shape
    if topleft[0] >= img_w or topleft[1] >= img_h:
        return img
    margin = 3
    size = cv2.getTextSize(text, FONT, TEXT_SCALE, TEXT_THICKNESS)
    w = size[0][0] + margin * 2
    h = size[0][1] + margin * 2
    # the patch is used to draw boxed text
    patch = np.zeros((h, w, 3), dtype=np.uint8)
    patch[...] = color
    cv2.putText(patch, text, (margin + 1, h - margin - 2), FONT, TEXT_SCALE,
                WHITE, thickness=TEXT_THICKNESS, lineType=cv2.LINE_8)
    cv2.rectangle(patch, (0, 0), (w - 1, h - 1), BLACK, thickness=1)
    w = min(w, img_w - topleft[0])  # clip overlay at image boundary
    h = min(h, img_h - topleft[1])
    # Overlay the boxed text onto a region of interest (roi) in img
    roi = img[topleft[1]:topleft[1] + h, topleft[0]:topleft[0] + w, :]
    cv2.addWeighted(patch[0:h, 0:w, :], ALPHA, roi, 1 - ALPHA, 0, roi)
    return img


def reduce_year_month(accu, item):
    if folder_regex.match(item) is None:
        return accu
    year = item.split('/')[2][:4]
    if year not in accu:
        accu[year] = dict()
    month = item.split('/')[2][4:6]
    if month in accu[year]:
        accu[year][month] += 1
    else:
        accu[year][month] = 1
    return accu


def reduce_month(accu, item):
    if folder_regex.match(item) is None:
        return accu
    month = item.split('/')[2][4:6]
    if month in accu:
        accu[month] += 1
    else:
        accu[month] = 1
    return accu


def reduce_day(accu, item):
    if folder_regex.match(item) is None:
        return accu
    day = item.split('/')[2][6:8]
    if day in accu:
        accu[day] += 1
    else:
        accu[day] = 1
    return accu


def reduce_year(accu, item):
    if folder_regex.match(item) is None:
        return accu
    year = item.split('/')[2][:4]
    if year in accu:
        accu[year] += 1
    else:
        accu[year] = 1
    return accu


def reduce_hour(accu, item):
    if folder_regex.match(item) is None:
        return accu
    condition = item.split('/')[3][:2]
    if condition in accu:
        accu[condition] += 1
    else:
        accu[condition] = 1
    return accu


def reduce_object(accu, item):
    if folder_regex.match(item) is None:
        return accu
    condition = item.split('/')[3].split('_')[1].split('-')
    for val in condition:
        if val in accu:
            accu[val] += 1
        else:
            accu[val] = 1
    return accu


def reduce_tracking(accu, item):
    if folder_regex.match(item) is None:
        return accu
    condition = item.split('/')[3].split('_')[2].split('-')
    for val in condition:
        if val in accu:
            accu[val] += 1
        else:
            accu[val] = 1
    return accu


def gstreamer_pipeline(
        capture_width=1280,
        capture_height=720,
        display_width=640,
        display_height=360,
        framerate=120,
        flip_method=0,
):
    return (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink max-buffers=1 drop=True "
            % (
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )


def get_video_stream():
    # For YouTube Streams/Videos:
    if "https://www.youtube.com" in constants.VIDEO_SOURCE:
        vid = VideoGear(
            source=constants.VIDEO_SOURCE + " ! application/x-rtp,media=video,payload=96,"
                                            "clock-rate=90000,encoding-name=H264, ! rtph264depay ! decodebin ! "
                                            "videoconvert ! video/x-raw,"
                                            "format=BGR ! appsink",
            stream_mode=True,
            resolution=(640, 480),
            framerate=constants.FRAME_RATE,
            logging=True,
            time_delay=1
        ).start()
        # logger_main.info("Capturing video stream from YouTube")

    # For Raspberry Pi Video Connection:
    elif "tcp" in constants.VIDEO_SOURCE:
        vid = cv2.VideoCapture(constants.VIDEO_SOURCE)
        # logger_main.info("Capturing video stream from Raspberry Pi")


    # For local machine webcam:
    elif constants.VIDEO_SOURCE == 0:
        vid = VideoGear(source=constants.VIDEO_SOURCE).start()
        # logger_main.info("Capturing video stream from local webcam")

    # For locally saved video
    else:
        vid = VideoGear(
            source=constants.VIDEO_SOURCE,
            resolution=(640, 480),
            framerate=constants.FRAME_RATE,
            logging=True,
            time_delay=1,
        ).start()
        # logger_main.info("Capturing video stream from local video")
    return vid


def get_frame(vid):
    if "tcp" in constants.VIDEO_SOURCE:
        got_frame, frame = vid.read()
        if not got_frame:
            # logger_main.info("Cannot read frame from video stream. Closing video stream!")
            vid.release()
    else:
        frame = vid.read()
    return frame


def check_wanted_classes(class_key):
    if class_key not in constants.CUSTOM_CLASS_NAMES:
        return False
    return True


def plot_analytics(analytic_list_waiting_score, analytic_list_throughput_score, file_name):
    analytic_list_waiting_score.sort(key=lambda x: x[1])
    analytic_list_throughput_score.sort(key=lambda x: x[1])
    plt.xlabel("traffic volume score")
    plt.ylabel("waiting_score/throughput_score")
    plt.plot(*zip(*analytic_list_waiting_score), label="waiting_score")
    plt.plot(*zip(*analytic_list_throughput_score), label="throughput_score")
    plt.savefig(file_name, bbox_inches='tight')
    plt.show()

def debug_info_gpu_utilization():
    # --- Enhanced Early CUDA Diagnostics ---
    logger_background.info("--- Background Thread: Early CUDA Diagnostics START ---")

    # 1. Log PyTorch version
    logger_background.info(f"PyTorch version: {torch.__version__}")

    # 2. Log CUDA_VISIBLE_DEVICES
    cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES')
    logger_background.info(
        f"CUDA_VISIBLE_DEVICES in background thread: {cuda_visible_devices if cuda_visible_devices is not None else 'Not Set'}")

    # 3. Perform basic CUDA availability check and operations
    is_cuda_available_early = torch.cuda.is_available()
    logger_background.info(f"torch.cuda.is_available() at thread start: {is_cuda_available_early}")

def save_plot_analytics(traffic_volume_score, waiting_score, throughput_score, analytic_list_waiting_score,
                        analytic_list_throughput_score):
    analytic_list_waiting_score.append((traffic_volume_score, waiting_score))
    analytic_list_throughput_score.append((traffic_volume_score, throughput_score))

    if len(analytic_list_waiting_score) == 500:
        plot_analytics(analytic_list_waiting_score, analytic_list_throughput_score,
                       'webcam/images/analytics500frames.png')

    if len(analytic_list_waiting_score) == 1500:
        plot_analytics(analytic_list_waiting_score, analytic_list_throughput_score,
                       'webcam/images/analytics1500frames.png')

    if len(analytic_list_waiting_score) == 3000:
        plot_analytics(analytic_list_waiting_score, analytic_list_throughput_score,
                       'webcam/images/analytics3000frames.png')

def collect_statistics(waiting_score, last_toggle_time, toggle_number, current_loop_time, past_waiting_score, new_vehicles_in_intersection, start_loop_time):
    # avg_waiting_time = last_avg_waiting_time + (waiting_score - past_waiting_score + (time_since_last_toggle / avg_waiting_time/cycle)) / (past_waiting_score - 1)
    #
    #                                                avg_waiting_time/cycle = (current_loop_time / toggle_number)
    #                                                time_since_last_toggle / (current_loop_time / toggle_number) = (time_since_last_toggle * toggle_number) / current_loop_time
    #
    # avg_waiting_time = last_avg_waiting_time + (waiting_score - past_waiting_score + (time_since_last_toggle * toggle_number) / current_loop_time) / (past_waiting_score - 1)

    if not hasattr(collect_statistics, 'last_stat_save_time'):
        # Initialize to a time that ensures the first save happens,
        # or 0 if you want the first call to potentially save immediately.
        collect_statistics.last_stat_save_time = time.monotonic() - 5.0

    from webcam.intersection import AvgWaitingTimeDataPoint, AvgVehicleThroughputDataPoint

    avg_waiting_data_points = AvgWaitingTimeDataPoint.load_from_db(intersection_id=constants.INTERSECTION_ID)
    last_avg_waiting_time = 0  # Default value if no data points are found

    if avg_waiting_data_points:
        # Sort the list of DataPoint objects by their timestamp attribute
        avg_waiting_data_points.sort(key=lambda dp: dp.timestamp, reverse=True)
        if avg_waiting_data_points:  # Check again in case the list became empty after potential filtering (though not done here)
            last_avg_waiting_time = avg_waiting_data_points[0].value

    time_since_last_toggle = current_loop_time - last_toggle_time

    division_by_zero_correction = 0.000
    if past_waiting_score == 1:
        division_by_zero_correction -= 100

    if waiting_score > 0:
        waiting_score = 1

    saved_statistics_number = (current_loop_time - start_loop_time) / 5 + 1

    avg_waiting_time = (last_avg_waiting_time * saved_statistics_number + waiting_score * ((current_loop_time - start_loop_time) / toggle_number)) / (saved_statistics_number + 1)
    if avg_waiting_time < 0:
        avg_waiting_time = 0

    avg_vehicle_throughput = new_vehicles_in_intersection / (current_loop_time - start_loop_time)

    current_time = time.monotonic()

    if (current_time - collect_statistics.last_stat_save_time) >= 5.0:
        past_waiting_score = waiting_score
        new_avg_waiting_time_data_point = AvgWaitingTimeDataPoint(intersection_id=constants.INTERSECTION_ID, timestamp=datetime.datetime.now, value=avg_waiting_time)
        new_avg_waiting_time_data_point.save_to_db()

        new_avg_vehicle_throughput_data_point = AvgVehicleThroughputDataPoint(intersection_id=constants.INTERSECTION_ID, timestamp=datetime.datetime.now, value=avg_vehicle_throughput)
        new_avg_vehicle_throughput_data_point.save_to_db()

        collect_statistics.last_stat_save_time = current_time


    return past_waiting_score

def load_models(traffic_control_agent):
    if os.path.exists(constants.detection_model_path):
        detection_model = YOLO(constants.detection_model_path)
    else:
        error_msg = (f"Detection model path is invalid! "
                     f"{constants.detection_model_path} doesn't exist! Exiting...")
        logger_background.error(error_msg)
        raise FileNotFoundError(error_msg)

    if os.path.exists(constants.traffic_control_model_path):
        traffic_control_agent.model.load_state_dict(torch.load(constants.traffic_control_model_path, map_location=traffic_control_agent.device))
    else:
        error_msg = (f"Traffic control model path is invalid! "
                     f"{constants.traffic_control_model_path} doesn't exist! Exiting...")
        logger_background.error(error_msg)
        raise FileNotFoundError(error_msg)
    return detection_model, traffic_control_agent
