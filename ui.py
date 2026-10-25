import cv2

import config

FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_header(frame, gesture, finger_count, mode_text, message_text="", sentence_text=""):
    width = frame.shape[1]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 120), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    cv2.putText(frame, f"Gesture: {gesture}", (20, 30),
                FONT, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Fingers: {finger_count}", (20, 62),
                FONT, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, mode_text, (width - 260, 30),
                FONT, 0.7, config.BRUSH_COLOR, 2)

    label = message_text if message_text else "No message"
    cv2.putText(frame, f"Text: {label[:28]}", (20, 90),
                FONT, 0.6, (255, 255, 255), 2)

    if sentence_text:
        cv2.putText(frame, f"Sentence: {sentence_text[:35]}", (20, 108),
                    FONT, 0.55, (200, 200, 200), 1)

    cv2.putText(frame, "Keys: C Clear   S Save   Q Quit   1-5 Colors   [ ] Brush   E Erase   U Undo   R Redo",
                (width - 700, 62), FONT, 0.45, (200, 200, 200), 1)


def draw_clear_progress(frame, progress):
    cv2.rectangle(frame, (20, 150), (220, 170), (255, 255, 255), 2)
    cv2.rectangle(frame, (20, 150), (20 + int(200 * progress), 170),
                  (0, 0, 255), -1)
    cv2.putText(frame, "Clearing...", (230, 167), FONT, 0.6, (0, 0, 255), 2)


def draw_communication_board(frame, buttons, selected_label=None):
    width = frame.shape[1]
    box_x = max(0, width - 500)
    box_y = 100
    box_w = 470
    box_h = 330

    overlay = frame.copy()
    cv2.rectangle(overlay, (box_x, box_y), (box_x + box_w, box_y + box_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    cv2.putText(frame, "Quick Communication", (box_x + 15, box_y + 25),
                FONT, 0.7, (255, 255, 255), 2)

    for label, rect in buttons:
        x, y, w, h = rect
        if x < box_x:
            x = box_x + x
        color = (60, 60, 60)
        if label == selected_label:
            color = (0, 200, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, label, (x + 10, y + 28), FONT, 0.52, (255, 255, 255), 2)
