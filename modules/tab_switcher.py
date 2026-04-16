"""
Module 1 — Tab Switcher

Open hand  → Alt+Tab       (next window)
Closed fist → Shift+Alt+Tab (previous window)

Runs continuously using the shared webcam.
"""

import time
import logging

log = logging.getLogger("guardian.tab_switcher")


class TabSwitcherModule:
    def __init__(self, camera, cfg: dict):
        self.camera = camera
        self.cooldown = cfg.get("cooldown_seconds", 1.5)
        self.confidence_frames = cfg.get("confidence_frames", 8)
        self._last_action_time = 0.0

    def run(self):
        try:
            from modules.gesture import GestureDetector, OPEN_HAND, FIST
            import pyautogui # type: ignore
        except ImportError as e:
            log.error("TabSwitcher disabled — missing dependency: %s", e)
            return

        detector = GestureDetector(confidence_frames=self.confidence_frames)
        log.info("TabSwitcher ready. Open hand = next tab, Fist = previous tab.")

        try:
            while True:
                frame = self.camera.get_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue

                gesture = detector.detect(frame)
                now = time.time()

                if gesture != "NONE" and (now - self._last_action_time) >= self.cooldown:
                    if gesture == OPEN_HAND:
                        log.info("Open hand detected → Alt+Tab")
                        pyautogui.hotkey("alt", "tab")
                        self._last_action_time = now
                    elif gesture == FIST:
                        log.info("Fist detected → Shift+Alt+Tab")
                        pyautogui.hotkey("shift", "alt", "tab")
                        self._last_action_time = now

                # ~20 fps is plenty for gesture detection
                time.sleep(0.05)

        except Exception as e:
            log.exception("TabSwitcher crashed: %s", e)
        finally:
            detector.close()