"""
config.py
---------
All the settings of the project in ONE place.
Change a value here and the whole app updates.
"""

# ---------- Camera ----------
CAMERA_INDEX = 0        # 0 = default laptop webcam (try 1 if it fails)
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# ---------- Hand detection ----------
MAX_HANDS = 1
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.7

# ---------- Drawing ----------
BRUSH_COLOR = (0, 255, 255)   # BGR colour -> yellow
BRUSH_SIZE = 6

# ---------- Clearing ----------
CLEAR_HOLD_SECONDS = 1.5      # hold open palm this long to clear

# ---------- Window ----------
WINDOW_NAME = "Hand Gesture Recognition and Virtual Drawing"

# ---------- MediaPipe landmark numbers (21 points per hand) ----------
FINGER_TIPS = [8, 12, 16, 20]   # index, middle, ring, pinky fingertips
FINGER_PIPS = [6, 10, 14, 18]   # middle joint of the same fingers

# ---------- Hand model file (downloaded automatically on first run) ----------
MODEL_FILE = "hand_landmarker.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
             "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")

# ---------- Accuracy and performance tuning ----------
STABLE_FRAMES = 5        # a gesture must appear this many frames in a row
FINGER_RATIO = 1.1       # fingertip must be this much farther from wrist than middle joint
DETECTION_WIDTH = 640    # frame is shrunk to this width for faster detection

JUMP_LIMIT = 200         # pixels: bigger sudden jumps are treated as detection errors
MAX_REJECTED = 3         # after this many rejected jumps, accept the new position

SMOOTH_SLOW = 0.25       # strong smoothing when the finger moves slowly
SMOOTH_FAST = 0.80       # light smoothing when the finger moves fast
SPEED_SLOW = 5           # pixels per frame treated as "slow"
SPEED_FAST = 40          # pixels per frame treated as "fast"
