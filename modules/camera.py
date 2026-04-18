"""
SharedCamera — one cv2.VideoCapture instance shared across all modules.

Each module calls .get_frame() which returns the latest frame.
A background reader thread continuously grabs frames so modules
always get a fresh one without each doing their own cap.read().
"""

import cv2
import threading
import time
import logging

log = logging.getLogger("guardian.camera")


class SharedCamera:
    def __init__(self, index: int = 0):
        self.index = index
        self._cap = None
        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def open(self) -> bool:
        self._cap = cv2.VideoCapture(self.index)
        if not self._cap.isOpened():
            return False
        # Lower resolution to save CPU — 640×480 is plenty for gestures/faces
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._running = True
        self._thread = threading.Thread(target=self._reader, name="CamReader", daemon=True)
        self._thread.start()
        # Wait for first frame
        for _ in range(50):
            time.sleep(0.05)
            if self._frame is not None:
                return True
        log.warning("Camera opened but no frames received after 2.5s")
        return False

    def _reader(self):
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._frame = frame
            else:
                time.sleep(0.01)

    def get_frame(self):
        """Return the latest frame (numpy array) or None."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def close(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        log.info("Camera closed")

    def __del__(self):
        self.close()
