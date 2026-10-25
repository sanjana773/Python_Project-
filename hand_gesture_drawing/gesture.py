"""
gesture.py
----------
Turns the 21 hand landmarks into:
    1. which fingers are up   (works even if the hand is tilted)
    2. the finger count
    3. the gesture name
Also has two helpers:
    GestureStabilizer -> removes flickering
    HoldTimer         -> measures "hold open palm to clear"
"""

import math
import time

import config

# Gesture names (kept in one place to avoid spelling mistakes)
OPEN_PALM = "Open Palm"
CLOSED_FIST = "Closed Fist"
THUMBS_UP = "Thumbs Up"
PEACE_SIGN = "Peace Sign"
POINTING = "Pointing (Drawing)"
UNKNOWN = "Unknown"
NO_HAND = "No Hand"


def distance(landmarks, a, b):
    """Straight-line distance between landmark a and landmark b."""
    return math.hypot(landmarks[a].x - landmarks[b].x,
                      landmarks[a].y - landmarks[b].y)


def hand_size(landmarks):
    """Size of the hand (wrist to middle-finger base). Used as a ruler."""
    return distance(landmarks, 0, 9)


def get_fingers_up(landmarks):
    """
    Return 5 booleans: [thumb, index, middle, ring, pinky].
    True = that finger is raised.

    Method: a straight finger has its tip FAR from the wrist, a folded
    finger has its tip CLOSE to the wrist. Distances do not depend on the
    direction of the hand, so tilted or rotated hands work too.
    """
    fingers = []

    # Thumb: "out" when its tip is farther from the pinky base (point 17)
    # than its middle joint (point 3) is.
    fingers.append(distance(landmarks, 4, 17) > distance(landmarks, 3, 17))

    # Other four fingers: tip farther from the wrist than the middle joint
    for tip, pip in zip(config.FINGER_TIPS, config.FINGER_PIPS):
        tip_dist = distance(landmarks, 0, tip)
        pip_dist = distance(landmarks, 0, pip)
        fingers.append(tip_dist > pip_dist * config.FINGER_RATIO)

    return fingers


def count_fingers(fingers):
    """Number of raised fingers (0 to 5)."""
    return sum(fingers)


def _thumb_points_up(landmarks):
    """
    True if the thumb clearly points upward.
    The thumb must rise by at least 60% of the hand's own size, so it works
    at any distance from the camera.
    """
    rise = landmarks[2].y - landmarks[4].y          # positive = tip is higher
    in_order = landmarks[4].y < landmarks[3].y < landmarks[2].y
    return in_order and rise > 0.6 * hand_size(landmarks)


def recognize_gesture(fingers, landmarks):
    """Decide the gesture name from the finger states."""
    _thumb, index, middle, ring, pinky = fingers
    four_up = [index, middle, ring, pinky]

    if not any(four_up):                      # all four fingers folded
        return THUMBS_UP if _thumb_points_up(landmarks) else CLOSED_FIST

    if all(four_up):
        return OPEN_PALM

    if index and middle and not ring and not pinky:
        return PEACE_SIGN

    if index and not middle and not ring and not pinky:
        return POINTING

    return UNKNOWN


class GestureStabilizer:
    """
    Removes flickering. A new gesture is accepted only after it has been
    seen for several frames in a row. Until then the old gesture stays.
    """

    def __init__(self, frames_needed):
        self.frames_needed = frames_needed
        self.stable = NO_HAND      # the gesture we currently trust
        self.candidate = NO_HAND   # the gesture we are waiting to confirm
        self.count = 0

    def update(self, gesture):
        if gesture == self.stable:
            self.candidate, self.count = gesture, 0
        elif gesture == self.candidate:
            self.count += 1
            if self.count >= self.frames_needed:
                self.stable, self.count = gesture, 0
        else:
            self.candidate, self.count = gesture, 1
        return self.stable


class HoldTimer:
    """Measures how long a gesture is held continuously."""

    def __init__(self, seconds):
        self.seconds = seconds
        self.start = None

    def update(self, active):
        """
        Call once per frame. Returns progress from 0.0 to 1.0.
        Returns 1.0 when the hold time is complete (and resets).
        """
        if not active:
            self.start = None
            return 0.0

        if self.start is None:
            self.start = time.time()

        progress = min((time.time() - self.start) / self.seconds, 1.0)
        if progress >= 1.0:
            self.start = None
        return progress
