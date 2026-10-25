import os
import tempfile
import threading
import time
import unittest

import numpy as np

import config
import gesture
import history
from drawing_canvas import DrawingCanvas
from main import SentenceBuilder, SpeechManager, resolve_communication_click


class SmartSignLogicTests(unittest.TestCase):
    def test_sentence_builder_deduplicates_and_builds(self):
        builder = SentenceBuilder()
        self.assertEqual(builder.add("Hello"), "Hello")
        self.assertEqual(builder.add("Hello"), "Hello")
        self.assertEqual(builder.add("Please"), "Hello Please")
        self.assertEqual(builder.clear(), "")

    def test_gesture_mapping(self):
        self.assertEqual(gesture.get_message_for_gesture(gesture.OPEN_PALM), "Hello!")
        self.assertEqual(gesture.get_message_for_gesture(gesture.CLOSED_FIST), "No")
        self.assertEqual(gesture.get_message_for_gesture(gesture.THUMBS_UP), "Yes")
        self.assertEqual(gesture.get_message_for_gesture(gesture.PEACE_SIGN), "Thank You")
        self.assertEqual(gesture.get_message_for_gesture(gesture.UNKNOWN), "Unknown Gesture")

    def test_communication_button_hit_detection(self):
        frame_width = 1280
        label = resolve_communication_click(840, 140, frame_width, config.COMMUNICATION_BUTTONS)
        self.assertEqual(label, "Yes")
        self.assertIsNone(resolve_communication_click(10, 10, frame_width, config.COMMUNICATION_BUTTONS))

    def test_history_stores_recent_messages(self):
        history.add_message("Hello from test", "button")
        messages = history.get_recent_messages(5)
        self.assertTrue(any(item["phrase"] == "Hello from test" for item in messages))

    def test_drawing_undo_redo(self):
        canvas = DrawingCanvas((200, 200, 3))
        canvas.draw(50, 50)
        canvas.draw(60, 60)
        self.assertEqual(len(canvas.undo_stack), 1)
        canvas.undo()
        self.assertTrue(np.all(canvas.canvas == 0))
        canvas.redo()
        self.assertFalse(np.all(canvas.canvas == 0))

    def test_drawing_overlay_and_save(self):
        canvas = DrawingCanvas((80, 80, 3))
        canvas.set_color((0, 255, 0))
        canvas.draw(20, 20)
        canvas.draw(30, 30)
        frame = np.zeros((80, 80, 3), dtype=np.uint8)
        output = canvas.overlay_on(frame)
        self.assertFalse(np.all(output == 0))

        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            try:
                path = canvas.save()
                self.assertTrue(os.path.exists(path))
                self.assertTrue(path.lower().endswith(".png"))
                self.assertGreater(os.path.getsize(path), 0)
            finally:
                os.chdir(original_cwd)

    def test_speech_queue_returns_without_blocking_call(self):
        speech = SpeechManager()

        class FakeEngine:
            def say(self, text):
                time.sleep(0.05)

            def runAndWait(self):
                pass

            def stop(self):
                pass

        speech._engine = FakeEngine()
        speech._ready = True
        speech._thread = threading.Thread(target=speech._worker, daemon=True)
        speech._thread.start()

        start = time.perf_counter()
        speech.speak("Hello")
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.2)
        speech.shutdown()


if __name__ == "__main__":
    unittest.main()
