"""
Real-Time Hand Gesture Recognition and Virtual Drawing System
-------------------------------------------------------------
MCA Semester 1 Project

RUN THIS FILE TO START THE APP:   python main.py

Project files:
    main.py            -> starts the app and runs the main loop (this file)
    config.py          -> all settings
    hand_tracker.py    -> MediaPipe hand detection
    gesture.py         -> finger counting and gesture recognition
    drawing_canvas.py  -> the virtual drawing board
    ui.py              -> on-screen information panel

Controls:
    Point with ONLY index finger -> DRAW
    Peace sign                   -> PEN UP (move without drawing)
    Open palm held ~1.5 seconds  -> CLEAR drawing
    Keyboard: c = clear | s = save | q = quit
"""

import cv2

import config
import gesture
import ui
from drawing_canvas import DrawingCanvas
from hand_tracker import HandTracker


def main():
    # 1. Open the webcam
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        print("ERROR: Could not open the webcam. Close other apps using it "
              "or change CAMERA_INDEX in config.py.")
        return

    tracker = HandTracker()
    stabilizer = gesture.GestureStabilizer(config.STABLE_FRAMES)
    clear_timer = gesture.HoldTimer(config.CLEAR_HOLD_SECONDS)
    canvas = None   # created after we know the frame size

    print("Project started. Press 'q' in the video window to quit.")

    while True:
        success, frame = cap.read()
        if not success:
            print("ERROR: Could not read from the webcam.")
            break

        frame = cv2.flip(frame, 1)          # mirror view
        if canvas is None:
            canvas = DrawingCanvas(frame.shape)

        # 2. Detect the hand
        landmarks = tracker.find_hand(frame)

        # 3. Fingers and gesture (stabilised to avoid flickering)
        finger_count = 0
        if landmarks is not None:
            fingers = gesture.get_fingers_up(landmarks)
            finger_count = gesture.count_fingers(fingers)
            raw_gesture = gesture.recognize_gesture(fingers, landmarks)
        else:
            raw_gesture = gesture.NO_HAND
        gesture_name = stabilizer.update(raw_gesture)

        # 4. Act on the stable gesture
        mode_text = "Mode: Waiting"
        if landmarks is not None and gesture_name == gesture.POINTING:
            h, w, _ = frame.shape
            x, y = int(landmarks[8].x * w), int(landmarks[8].y * h)
            x, y = canvas.draw(x, y)
            cv2.circle(frame, (x, y), 10, config.BRUSH_COLOR, -1)
            mode_text = "Mode: DRAWING"
        else:
            canvas.lift_pen()
            if landmarks is not None:
                mode_text = "Mode: PEN UP"

        # Hold open palm to clear
        clear_progress = clear_timer.update(gesture_name == gesture.OPEN_PALM)
        if clear_progress >= 1.0:
            canvas.clear()
        elif clear_progress > 0:
            ui.draw_clear_progress(frame, clear_progress)

        # 5. Show everything
        frame = canvas.overlay_on(frame)
        ui.draw_header(frame, gesture_name, finger_count, mode_text)
        cv2.imshow(config.WINDOW_NAME, frame)

        # 6. Keyboard controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("c"):
            canvas.clear()
        elif key == ord("s"):
            print(f"Drawing saved as {canvas.save()}")

    # 7. Clean up
    tracker.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
