"""
hand_tracker.py
---------------
Wraps MediaPipe (Tasks API) so the rest of the project never has to deal
with it. MediaPipe finds the hand and gives us 21 landmark points.

On the first run, the small pre-trained hand model file
(hand_landmarker.task, ~8 MB) is downloaded automatically.
"""

import os
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

import config

# Pairs of landmark numbers that are joined by a line (the hand skeleton)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),            # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),            # index
    (5, 9), (9, 10), (10, 11), (11, 12),       # middle
    (9, 13), (13, 14), (14, 15), (15, 16),     # ring
    (13, 17), (17, 18), (18, 19), (19, 20),    # pinky
    (0, 17),                                   # palm edge
]


def _model_path():
    """Return the model file path, downloading it if it is missing."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        config.MODEL_FILE)
    if not os.path.exists(path):
        print("Downloading hand model (one time only)...")
        try:
            urllib.request.urlretrieve(config.MODEL_URL, path)
        except Exception as error:
            raise SystemExit(
                f"Could not download the model: {error}\n"
                f"Download it manually from:\n{config.MODEL_URL}\n"
                f"and save it as '{config.MODEL_FILE}' in the project folder.")
        print("Model downloaded.")
    return path


class HandTracker:
    """Detects one hand in a camera frame."""

    def __init__(self):
        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=_model_path()),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=config.MAX_HANDS,
            min_hand_detection_confidence=config.DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.DETECTION_CONFIDENCE,
            min_tracking_confidence=config.TRACKING_CONFIDENCE,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.last_timestamp = 0

    def find_hand(self, frame, draw=True):
        """
        Look for a hand in the frame.
        Returns the list of 21 landmarks (each has .x and .y between 0 and 1),
        or None when no hand is visible.
        """
        # Shrink the frame for faster detection (landmarks are 0-1 values,
        # so they still match the full-size frame)
        h, w, _ = frame.shape
        small_h = int(h * config.DETECTION_WIDTH / w)
        small = cv2.resize(frame, (config.DETECTION_WIDTH, small_h))

        # MediaPipe needs RGB, OpenCV gives BGR
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # Video mode needs an always-increasing timestamp in milliseconds
        timestamp = int(time.monotonic() * 1000)
        if timestamp <= self.last_timestamp:
            timestamp = self.last_timestamp + 1
        self.last_timestamp = timestamp

        result = self.landmarker.detect_for_video(image, timestamp)

        if not result.hand_landmarks:
            return None

        landmarks = result.hand_landmarks[0]
        if draw:
            self._draw_skeleton(frame, landmarks)
        return landmarks

    @staticmethod
    def _draw_skeleton(frame, landmarks):
        """Draw lines and dots on the hand."""
        h, w, _ = frame.shape
        points = [(int(p.x * w), int(p.y * h)) for p in landmarks]
        for start, end in HAND_CONNECTIONS:
            cv2.line(frame, points[start], points[end], (255, 255, 255), 2)
        for point in points:
            cv2.circle(frame, point, 5, (0, 200, 0), -1)

    def close(self):
        self.landmarker.close()
