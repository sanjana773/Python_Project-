import queue
import threading
import time

import cv2
import pyttsx3

import config
import gesture
import history
import ui
from drawing_canvas import DrawingCanvas
from hand_tracker import HandTracker


class SentenceBuilder:
    def __init__(self):
        self.parts = []

    def add(self, phrase):
        phrase = str(phrase).strip()
        if not phrase:
            return self.current_text()
        if not self.parts or self.parts[-1] != phrase:
            self.parts.append(phrase)
        return self.current_text()

    def current_text(self):
        return " ".join(self.parts)

    def clear(self):
        self.parts.clear()
        return ""


class SpeechManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._engine = None
        self._last_text = None
        self._last_time = 0.0
        self._ready = False
        self._queue = queue.Queue()
        self._thread = None

    def init(self):
        try:
            self._engine = pyttsx3.init()
            self._ready = True
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()
        except Exception as exc:
            print(f"Text-to-speech engine could not initialize: {exc}")
            self._ready = False

    def _worker(self):
        while True:
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                break
            text = str(item).strip()
            if not text:
                self._queue.task_done()
                continue
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as exc:
                print(f"Speech output unavailable: {exc}")
            finally:
                self._queue.task_done()

    def speak(self, text, *, cooldown=1.5):
        if not self._ready or not text:
            return
        text = str(text).strip()
        if not text:
            return
        now = time.time()
        with self._lock:
            if self._last_text == text and (now - self._last_time) < cooldown:
                return
            self._last_text = text
            self._last_time = now
        self._queue.put(text)

    def speak_now(self, text):
        if not self._ready or not text:
            return
        self._queue.put(str(text).strip())

    def shutdown(self):
        if self._ready and self._thread is not None:
            self._queue.put(None)
            self._thread.join(timeout=5)
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                pass


def on_mouse(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        params["click"] = (x, y)


def resolve_communication_click(x_click, y_click, frame_width, buttons):
    for label, rect in buttons:
        x, y, w, h = rect
        adjusted_x = x if x >= frame_width - 500 else x + max(0, frame_width - 500)
        if adjusted_x <= x_click <= adjusted_x + w and y <= y_click <= y + h:
            return label
    return None


def main():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        print("ERROR: Could not open the webcam. Close other apps using it or change CAMERA_INDEX in config.py.")
        return

    tracker = HandTracker()
    stabilizer = gesture.GestureStabilizer(config.STABLE_FRAMES)
    clear_timer = gesture.HoldTimer(config.CLEAR_HOLD_SECONDS)
    canvas = None
    sentence_builder = SentenceBuilder()
    speech = SpeechManager()
    speech.init()
    last_emitted_gesture = None
    message_text = config.DEFAULT_MESSAGE
    current_sentence = ""
    interaction_state = {"click": None}
    last_hand_present = False

    cv2.namedWindow(config.WINDOW_NAME)
    cv2.setMouseCallback(config.WINDOW_NAME, on_mouse, interaction_state)

    print("Project started. Press 'q' in the video window to quit.")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("ERROR: Could not read from the webcam.")
                break

            frame = cv2.flip(frame, 1)
            if canvas is None:
                canvas = DrawingCanvas(frame.shape)
                canvas.set_color(config.DRAW_COLORS[0])
                canvas.undo_stack.clear()
                canvas.redo_stack.clear()

            landmarks = tracker.find_hand(frame)

            finger_count = 0
            if landmarks is not None:
                fingers = gesture.get_fingers_up(landmarks)
                finger_count = gesture.count_fingers(fingers)
                raw_gesture = gesture.recognize_gesture(fingers, landmarks)
            else:
                raw_gesture = gesture.NO_HAND
            gesture_name = stabilizer.update(raw_gesture)

            mode_text = "Mode: READY"
            if landmarks is not None and gesture_name == gesture.POINTING:
                h, w, _ = frame.shape
                x, y = int(landmarks[8].x * w), int(landmarks[8].y * h)
                x, y = canvas.draw(x, y)
                cv2.circle(frame, (x, y), 10, canvas.brush_color, -1)
                mode_text = "Mode: DRAWING"
            else:
                canvas.lift_pen()
                if landmarks is not None:
                    mode_text = "Mode: COMMUNICATION"

            if landmarks is not None and gesture_name not in (gesture.NO_HAND, gesture.UNKNOWN, gesture.POINTING):
                phrase = gesture.get_message_for_gesture(gesture_name)
                if phrase and gesture_name != last_emitted_gesture:
                    last_emitted_gesture = gesture_name
                    sentence_builder.add(phrase)
                    current_sentence = sentence_builder.current_text()
                    message_text = phrase
                    speech.speak(phrase)
                    history.add_message(phrase, "gesture")
            elif gesture_name == gesture.NO_HAND:
                last_emitted_gesture = None
                if not current_sentence:
                    message_text = config.DEFAULT_MESSAGE
            elif gesture_name == gesture.UNKNOWN:
                message_text = "Unknown Gesture"
            else:
                message_text = config.DEFAULT_MESSAGE if not current_sentence else current_sentence

            if interaction_state["click"] is not None:
                x_click, y_click = interaction_state["click"]
                interaction_state["click"] = None
                clicked_label = resolve_communication_click(x_click, y_click, frame.shape[1], config.COMMUNICATION_BUTTONS)
                if clicked_label is not None:
                    if clicked_label == "Clear Text":
                        current_sentence = sentence_builder.clear()
                        message_text = config.DEFAULT_MESSAGE
                    elif clicked_label == "Speak Current":
                        if current_sentence:
                            speech.speak_now(current_sentence)
                            message_text = current_sentence
                        else:
                            message_text = config.DEFAULT_MESSAGE
                    else:
                        current_sentence = sentence_builder.add(clicked_label)
                        message_text = clicked_label
                        speech.speak(clicked_label)
                        history.add_message(clicked_label, "button")

            clear_progress = clear_timer.update(gesture_name == gesture.OPEN_PALM)
            if clear_progress >= 1.0:
                canvas.clear()
            elif clear_progress > 0:
                ui.draw_clear_progress(frame, clear_progress)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("c"):
                canvas.clear()
            elif key == ord("s"):
                try:
                    file_name = canvas.save()
                    print(f"Drawing saved as {file_name}")
                except IOError as exc:
                    print(f"Could not save drawing: {exc}")
            elif key == ord("u"):
                canvas.undo()
            elif key == ord("r"):
                canvas.redo()
            elif key in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5")):
                index = key - ord("1")
                if index < len(config.DRAW_COLORS):
                    canvas.set_color(config.DRAW_COLORS[index])
                    canvas.set_eraser(False)
            elif key == ord("["):
                canvas.set_size(canvas.brush_size - 1)
            elif key == ord("]"):
                canvas.set_size(canvas.brush_size + 1)
            elif key == ord("e"):
                canvas.set_eraser(not canvas.eraser_mode)
            elif key == ord("t"):
                if current_sentence:
                    speech.speak_now(current_sentence)

            frame = canvas.overlay_on(frame)
            ui.draw_communication_board(frame, config.COMMUNICATION_BUTTONS, selected_label=message_text)
            ui.draw_header(frame, gesture_name, finger_count, mode_text, message_text, current_sentence)
            cv2.imshow(config.WINDOW_NAME, frame)

    finally:
        tracker.close()
        speech.shutdown()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
