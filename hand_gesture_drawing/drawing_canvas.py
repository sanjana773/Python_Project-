"""
drawing_canvas.py
-----------------
The virtual drawing board. It is a black image (NumPy array) the same
size as the video. We draw on it, then lay it over the camera frame.

Smart pen features:
    - Adaptive smoothing: slow movement = very smooth, fast movement = no lag
    - Jump filter: ignores sudden wrong jumps caused by bad detections
"""

import math
import time

import cv2
import numpy as np

import config


class DrawingCanvas:
    def __init__(self, frame_shape):
        self.canvas = np.zeros(frame_shape, dtype=np.uint8)
        self.prev_point = None     # last pen position
        self.rejected = 0          # how many jumps in a row we ignored

    def draw(self, x, y):
        """Move the pen to (x, y) and draw a line. Returns the pen position."""
        if self.prev_point is None:           # pen just touched the paper
            self.prev_point = (x, y)
            return x, y

        px, py = self.prev_point
        move = math.hypot(x - px, y - py)

        # Jump filter: a huge sudden jump is probably a detection error
        if move > config.JUMP_LIMIT:
            self.rejected += 1
            if self.rejected <= config.MAX_REJECTED:
                return self.prev_point        # ignore this frame
            # The finger really moved far: start a new line from here
            self.rejected = 0
            self.prev_point = (x, y)
            return x, y
        self.rejected = 0

        # Adaptive smoothing: slow -> strong smoothing, fast -> light smoothing
        speed = (move - config.SPEED_SLOW) / (config.SPEED_FAST - config.SPEED_SLOW)
        speed = max(0.0, min(speed, 1.0))     # keep between 0 and 1
        alpha = config.SMOOTH_SLOW + (config.SMOOTH_FAST - config.SMOOTH_SLOW) * speed

        x = int(px + (x - px) * alpha)
        y = int(py + (y - py) * alpha)

        cv2.line(self.canvas, self.prev_point, (x, y),
                 config.BRUSH_COLOR, config.BRUSH_SIZE)
        self.prev_point = (x, y)
        return x, y

    def lift_pen(self):
        """Stop connecting lines (like lifting a pen from paper)."""
        self.prev_point = None
        self.rejected = 0

    def clear(self):
        """Erase everything."""
        self.canvas[:] = 0
        self.lift_pen()

    def overlay_on(self, frame):
        """Copy the drawing on top of the camera frame."""
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        frame[mask > 0] = self.canvas[mask > 0]
        return frame

    def save(self):
        """Save the drawing as a PNG file and return the file name."""
        filename = f"drawing_{int(time.time())}.png"
        cv2.imwrite(filename, self.canvas)
        return filename
