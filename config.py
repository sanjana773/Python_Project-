CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

MAX_HANDS = 1
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.7

BRUSH_COLOR = (0, 255, 255)
BRUSH_SIZE = 6
MAX_BRUSH_SIZE = 20
DEFAULT_MESSAGE = "Ready"

CLEAR_HOLD_SECONDS = 1.5

WINDOW_NAME = "SmartSign - Assistive Communication and Virtual Drawing"

FINGER_TIPS = [8, 12, 16, 20]
FINGER_PIPS = [6, 10, 14, 18]

MODEL_FILE = "hand_landmarker.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/"
             "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")

STABLE_FRAMES = 5
FINGER_RATIO = 1.1
DETECTION_WIDTH = 640

JUMP_LIMIT = 200
MAX_REJECTED = 3

SMOOTH_SLOW = 0.25
SMOOTH_FAST = 0.80
SPEED_SLOW = 5
SPEED_FAST = 40

GESTURE_MESSAGES = {
    "Open Palm": "Hello!",
    "Closed Fist": "No",
    "Thumbs Up": "Yes",
    "Peace Sign": "Thank You",
    "Pointing (Drawing)": "Drawing Mode",
    "Unknown": "Unknown Gesture",
    "No Hand": "No Hand",
}

DRAW_COLORS = [
    (0, 255, 255),
    (255, 0, 0),
    (0, 255, 0),
    (255, 255, 255),
    (0, 0, 255),
]

COMMUNICATION_BUTTONS = [
    ("Yes", (30, 120, 170, 40)),
    ("No", (30, 175, 170, 40)),
    ("Help", (30, 230, 170, 40)),
    ("Water", (30, 285, 170, 40)),
    ("Food", (30, 340, 170, 40)),
    ("Pain", (270, 120, 170, 40)),
    ("Emergency", (270, 175, 170, 40)),
    ("Thank You", (270, 230, 170, 40)),
    ("Clear Text", (270, 285, 170, 40)),
    ("Speak Current", (270, 340, 170, 40)),
]

BUTTON_LABELS = {label for label, _ in COMMUNICATION_BUTTONS}
