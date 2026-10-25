import math
import time

import cv2
import numpy as np

import config


class DrawingCanvas:
    def __init__(self, frame_shape):
        self.canvas = np.zeros(frame_shape, dtype=np.uint8)
        self.prev_point = None
        self.rejected = 0
        self.brush_color = config.BRUSH_COLOR
        self.brush_size = config.BRUSH_SIZE
        self.eraser_mode = False
        self.last_color = self.brush_color
        self.undo_stack = []
        self.redo_stack = []

    def _push_undo(self):
        self.undo_stack.append(self.canvas.copy())
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def set_color(self, color):
        self.last_color = color
        if not self.eraser_mode:
            self.brush_color = color

    def set_size(self, size):
        self.brush_size = max(1, min(size, config.MAX_BRUSH_SIZE))

    def set_eraser(self, enabled):
        self.eraser_mode = enabled
        self.brush_color = (0, 0, 0) if enabled else self.last_color

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.canvas.copy())
        self.canvas = self.undo_stack.pop().copy()

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.canvas.copy())
        self.canvas = self.redo_stack.pop().copy()

    def draw(self, x, y):
        if self.prev_point is None:
            self.prev_point = (x, y)
            return x, y

        px, py = self.prev_point
        move = math.hypot(x - px, y - py)

        if move > config.JUMP_LIMIT:
            self.rejected += 1
            if self.rejected <= config.MAX_REJECTED:
                return self.prev_point
            self.rejected = 0
            self.prev_point = (x, y)
            return x, y
        self.rejected = 0

        speed = (move - config.SPEED_SLOW) / (config.SPEED_FAST - config.SPEED_SLOW)
        speed = max(0.0, min(speed, 1.0))
        alpha = config.SMOOTH_SLOW + (config.SMOOTH_FAST - config.SMOOTH_SLOW) * speed

        x = int(px + (x - px) * alpha)
        y = int(py + (y - py) * alpha)

        if not self.undo_stack or not np.array_equal(self.undo_stack[-1], self.canvas):
            self._push_undo()

        cv2.line(self.canvas, self.prev_point, (x, y),
                 self.brush_color, self.brush_size)
        self.prev_point = (x, y)
        return x, y

    def lift_pen(self):
        self.prev_point = None
        self.rejected = 0

    def clear(self):
        self._push_undo()
        self.canvas[:] = 0
        self.lift_pen()

    def overlay_on(self, frame):
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        frame[mask > 0] = self.canvas[mask > 0]
        return frame

    def save(self):
        timestamp = int(time.time())
        filename = f"drawing_{timestamp}.png"
        ok = cv2.imwrite(filename, self.canvas)
        if not ok:
            raise IOError(f"Failed to save drawing to {filename}")
        return filename
