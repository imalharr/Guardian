"""
Module 2 — Face Lock

Checks every N minutes whether the person at the webcam is you.
If an unknown face is detected for 20 continuous seconds → blackout screen.
Pressing the configured bypass key removes the blackout.
After bypass, face-lock re-arms after 15 seconds of confirmed re-recognition.
"""

import time
import threading
import logging
import os
import pickle

log = logging.getLogger("guardian.face_lock")


class BlackoutOverlay:
    """
    Full-screen black Tkinter window that blocks all input visually.
    Dismissed by pressing the bypass key.
    """

    def __init__(self, bypass_key: str, on_dismissed):
        self.bypass_key = bypass_key.lower()
        self.on_dismissed = on_dismissed
        self._root = None
        self._thread = None

    def show(self):
        if self._thread and self._thread.is_alive():
            return  # already showing
        self._thread = threading.Thread(target=self._run, daemon=True, name="Blackout")
        self._thread.start()

    def _run(self):
        import tkinter as tk

        self._root = tk.Tk()
        self._root.attributes("-fullscreen", True)
        self._root.attributes("-topmost", True)
        self._root.configure(background="black")
        self._root.overrideredirect(True)  # no title bar

        # Instruction label (subtle, small)
        lbl = tk.Label(
            self._root,
            text=f"Screen locked. Press {self.bypass_key.upper()} to unlock.",
            fg="#333333",
            bg="black",
            font=("Helvetica", 14),
        )
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Bind bypass key
        self._root.bind(f"<{self.bypass_key.upper()}>", self._dismiss)
        self._root.bind(f"<{self.bypass_key.lower()}>", self._dismiss)
        # Also bind as raw key name for function keys (F1–F12)
        if self.bypass_key.startswith("f") and self.bypass_key[1:].isdigit():
            self._root.bind(f"<{self.bypass_key.upper()}>", self._dismiss)

        self._root.focus_force()
        self._root.mainloop()

    def _dismiss(self, event=None):
        if self._root:
            self._root.destroy()
            self._root = None
        if self.on_dismissed:
            threading.Thread(target=self.on_dismissed, daemon=True).start()

    def hide(self):
        if self._root:
            self._root.after(0, self._root.destroy)


class FaceLockModule:
    def __init__(self, camera, cfg: dict):
        self.camera = camera
        self.check_interval = cfg.get("check_interval_minutes", 5) * 60
        self.face_data_path = cfg.get("face_data_path", "face_data.pkl")
        self.blackout_seconds = cfg.get("blackout_seconds", 20)
        self.bypass_key = cfg.get("bypass_key", "F12")
        self.re_verify_seconds = cfg.get("re_verify_seconds", 15)
        self.tolerance = cfg.get("tolerance", 0.55)

        self._known_encodings = []
        self._bypassed = False
        self._bypass_timer = None
        self._unknown_since = None
        self._blackout = None
        self._locked = False

    def _load_face_data(self) -> bool:
        if not os.path.exists(self.face_data_path):
            return False
        with open(self.face_data_path, "rb") as f:
            data = pickle.load(f)
        self._known_encodings = data.get("encodings", [])
        log.info("Loaded %d face encoding(s)", len(self._known_encodings))
        return len(self._known_encodings) > 0

    def _is_known_face(self, frame) -> bool:
        """Returns True if frame contains the registered face."""
        try:
            import face_recognition
        except ImportError:
            log.error("face_recognition not installed. Run: pip install face_recognition")
            return True  # fail open so we don't lock user out

        import cv2
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb, model="hog")
        if not locations:
            return True  # no face visible — don't lock (could be looking away)

        encodings = face_recognition.face_encodings(rgb, locations)
        for enc in encodings:
            matches = face_recognition.compare_faces(
                self._known_encodings, enc, tolerance=self.tolerance
            )
            if any(matches):
                return True
        return False

    def _on_bypass(self):
        """Called when user presses the bypass key."""
        log.info("Bypass key pressed — blackout dismissed. Re-arming in %ds.", self.re_verify_seconds)
        self._bypassed = True
        self._locked = False
        self._unknown_since = None
        # Re-arm after re_verify_seconds
        if self._bypass_timer:
            self._bypass_timer.cancel()
        self._bypass_timer = threading.Timer(
            self.re_verify_seconds, self._rearm_after_bypass
        )
        self._bypass_timer.daemon = True
        self._bypass_timer.start()

    def _rearm_after_bypass(self):
        log.info("Face-lock re-armed after bypass timeout.")
        self._bypassed = False

    def run(self):
        if not self._load_face_data():
            log.error("FaceLock: No face data. Run with --setup to register your face.")
            return

        self._blackout = BlackoutOverlay(self.bypass_key, self._on_bypass)
        log.info(
            "FaceLock ready. Checking every %dm. Bypass key: %s",
            self.check_interval // 60,
            self.bypass_key,
        )

        last_check = 0.0  # force immediate first check

        try:
            while True:
                now = time.time()

                if self._bypassed:
                    time.sleep(1)
                    continue

                # --- Scheduled periodic check ---
                if (now - last_check) >= self.check_interval:
                    frame = self.camera.get_frame()
                    if frame is not None:
                        known = self._is_known_face(frame)
                        if not known:
                            if self._unknown_since is None:
                                self._unknown_since = now
                                log.warning(
                                    "Unknown face detected — blackout in %ds if it persists.",
                                    self.blackout_seconds,
                                )
                        else:
                            if self._unknown_since is not None:
                                log.info("Known face confirmed — threat cleared.")
                            self._unknown_since = None
                            self._locked = False
                    last_check = now

                # --- Continuous watch while threat timer is running ---
                if self._unknown_since is not None and not self._locked:
                    elapsed = now - self._unknown_since
                    if elapsed >= self.blackout_seconds:
                        log.warning("Unknown face for %.0fs — BLACKOUT", elapsed)
                        self._locked = True
                        self._blackout.show()
                    else:
                        # Sample every 2s to check if threat has cleared
                        frame = self.camera.get_frame()
                        if frame is not None:
                            if self._is_known_face(frame):
                                log.info("Known face — clearing threat timer.")
                                self._unknown_since = None

                time.sleep(2)

        except Exception as e:
            log.exception("FaceLock crashed: %s", e)
