"""
Module 3 — Window Closer

OK gesture (thumb + index tips touching, other fingers up)
→ Close current window (Alt+F4) and open configured URL in browser.
"""

import time
import logging
import webbrowser

log = logging.getLogger("guardian.window_closer")


class WindowCloserModule:
    def __init__(self, camera, cfg: dict):
        self.camera = camera
        self.cooldown = cfg.get("cooldown_seconds", 2.0)
        self.confidence_frames = cfg.get("confidence_frames", 10)
        self.redirect_url = cfg.get("redirect_url", "https://www.google.com")
        self._last_action_time = 0.0

    def run(self):
        try:
            from modules.gesture import GestureDetector, OK
            import pyautogui
        except ImportError as e:
            log.error("WindowCloser disabled — missing dependency: %s", e)
            return

        detector = GestureDetector(confidence_frames=self.confidence_frames)
        log.info(
            "WindowCloser ready. OK gesture → close window + open %s",
            self.redirect_url,
        )

        try:
            while True:
                frame = self.camera.get_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue

                gesture = detector.detect(frame)
                now = time.time()

                if gesture == OK and (now - self._last_action_time) >= self.cooldown:
                    log.info("OK gesture → closing window and opening URL")
                    self._last_action_time = now
                    # Close the active window
                    pyautogui.hotkey("alt", "F4")
                    time.sleep(0.3)  # brief pause so window closes first
                    # Open redirect URL
                    webbrowser.open(self.redirect_url)

                time.sleep(0.05)

        except Exception as e:
            log.exception("WindowCloser crashed: %s", e)
        finally:
            detector.close()
