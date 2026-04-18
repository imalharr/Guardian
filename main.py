"""
Guardian — Personal Security Suite
Run with: python main.py
First-time setup: python main.py --setup
"""

import argparse
import sys
import os
import threading
import time
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s  %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("guardian")


def main():
    parser = argparse.ArgumentParser(description="Guardian Security Suite")
    parser.add_argument("--setup", action="store_true", help="Register your face and configure settings")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--no-tray", action="store_true", help="Skip system tray (useful for debugging)")
    args = parser.parse_args()

    from modules.config import load_config, default_config
    from modules.camera import SharedCamera

    if not os.path.exists(args.config):
        log.info("No config found — creating defaults at %s", args.config)
        with open(args.config, "w") as f:
            json.dump(default_config(), f, indent=2)

    cfg = load_config(args.config)

    if args.setup:
        from modules.setup import run_setup
        run_setup(cfg, args.config)
        return

    log.info("Starting Guardian…")

    # One shared camera for all modules
    cam = SharedCamera(index=cfg.get("camera_index", 0))
    if not cam.open():
        log.error("Could not open webcam. Check that no other app is using it.")
        sys.exit(1)

    threads = []

    # Module 1 — Tab-switcher gesture
    if cfg.get("tab_switcher", {}).get("enabled", True):
        from modules.tab_switcher import TabSwitcherModule
        m1 = TabSwitcherModule(cam, cfg["tab_switcher"])
        t1 = threading.Thread(target=m1.run, name="TabSwitcher", daemon=True)
        threads.append(t1)
        t1.start()
        log.info("Tab-switcher module started")

    # Module 2 — Face lock
    if cfg.get("face_lock", {}).get("enabled", True):
        face_data = cfg.get("face_lock", {}).get("face_data_path", "face_data.pkl")
        if not os.path.exists(face_data):
            log.warning("Face lock enabled but no face data found. Run with --setup first.")
        else:
            from modules.face_lock import FaceLockModule
            m2 = FaceLockModule(cam, cfg["face_lock"])
            t2 = threading.Thread(target=m2.run, name="FaceLock", daemon=True)
            threads.append(t2)
            t2.start()
            log.info("Face-lock module started")

    # Module 3 — OK-gesture window closer
    if cfg.get("window_closer", {}).get("enabled", True):
        from modules.window_closer import WindowCloserModule
        m3 = WindowCloserModule(cam, cfg["window_closer"])
        t3 = threading.Thread(target=m3.run, name="WindowCloser", daemon=True)
        threads.append(t3)
        t3.start()
        log.info("Window-closer module started")

    if not args.no_tray:
        try:
            from modules.tray import run_tray
            log.info("System tray active. Right-click the tray icon to quit.")
            run_tray(cam, threads, args.config)  # blocks until quit
        except ImportError:
            log.warning("pystray not installed — running without tray icon. Ctrl-C to stop.")
            _wait_forever(threads)
    else:
        _wait_forever(threads)


def _wait_forever(threads):
    try:
        while True:
            time.sleep(1)
            if not any(t.is_alive() for t in threads):
                log.info("All modules stopped — exiting.")
                break
    except KeyboardInterrupt:
        log.info("Interrupted. Goodbye.")


if __name__ == "__main__":
    main()
