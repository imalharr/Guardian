"""
Gesture detection helpers using MediaPipe Hands.

Gestures detected:
  - OPEN_HAND   : all 5 fingers extended
  - FIST        : all 4 fingers curled (thumb may vary)
  - OK          : thumb + index tips touching, other 3 fingers extended
  - NONE        : nothing recognised
"""

import math
import logging

log = logging.getLogger("guardian.gesture")

try:
    import mediapipe as mp
    _mp_hands = mp.solutions.hands
    _mp_drawing = mp.solutions.drawing_utils
    MEDIAPIPE_OK = True
except ImportError:
    MEDIAPIPE_OK = False
    log.error("mediapipe not installed — gesture modules will be disabled. Run: pip install mediapipe")

OPEN_HAND = "OPEN_HAND"
FIST      = "FIST"
OK        = "OK"
NONE      = "NONE"

# Finger tip landmark indices
TIP_IDS  = [4, 8, 12, 16, 20]   # thumb, index, middle, ring, pinky
MCP_IDS  = [2, 5, 9,  13, 17]   # corresponding base knuckles


def _dist(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def classify_hand(landmarks) -> str:
    """
    Takes a mediapipe NormalizedLandmarkList and returns a gesture string.
    """
    lm = landmarks.landmark

    # --- Finger extension: tip y < pip y means finger is up (image coords) ---
    # Thumb uses x-axis comparison (it bends sideways)
    thumb_up   = lm[4].x < lm[3].x  # left hand mirror; works for right-hand-facing-cam
    index_up   = lm[8].y  < lm[6].y
    middle_up  = lm[12].y < lm[10].y
    ring_up    = lm[16].y < lm[14].y
    pinky_up   = lm[20].y < lm[18].y

    fingers_up = [thumb_up, index_up, middle_up, ring_up, pinky_up]
    count_up   = sum(fingers_up)

    # OK gesture: thumb tip and index tip very close together,
    #             middle + ring + pinky extended
    thumb_index_dist = _dist(lm[4], lm[8])
    if thumb_index_dist < 0.07 and middle_up and ring_up and pinky_up:
        return OK

    # Open hand: all 5 fingers extended
    if count_up >= 4 and index_up and middle_up and ring_up and pinky_up:
        return OPEN_HAND

    # Fist: all four non-thumb fingers curled
    if not index_up and not middle_up and not ring_up and not pinky_up:
        return FIST

    return NONE


class GestureDetector:
    """
    Wraps a MediaPipe Hands instance.
    Call .detect(frame) → gesture string.
    Uses a confidence_frames counter to avoid accidental triggers.
    """

    def __init__(self, confidence_frames: int = 8):
        if not MEDIAPIPE_OK:
            raise RuntimeError("mediapipe not available")
        self.confidence_frames = confidence_frames
        self._hands = _mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )
        self._gesture_counts: dict[str, int] = {}

    def detect(self, frame) -> str:
        """
        Process one BGR frame. Returns a confirmed gesture only after
        it has been seen for `confidence_frames` consecutive frames.
        Returns NONE otherwise.
        """
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self._hands.process(rgb)

        raw = NONE
        if results.multi_hand_landmarks:
            raw = classify_hand(results.multi_hand_landmarks[0])

        # Update counts
        for g in [OPEN_HAND, FIST, OK, NONE]:
            if g == raw:
                self._gesture_counts[g] = self._gesture_counts.get(g, 0) + 1
            else:
                self._gesture_counts[g] = 0

        if self._gesture_counts.get(raw, 0) >= self.confidence_frames and raw != NONE:
            return raw
        return NONE

    def close(self):
        self._hands.close()