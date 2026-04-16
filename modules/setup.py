"""
Guardian Setup

Registers your face for the face-lock module and lets you configure settings.
Run with: python main.py --setup
"""

import time
import json
import pickle
import logging
import os

log = logging.getLogger("guardian.setup")


def run_setup(cfg: dict, config_path: str):
    print("\n=== Guardian Setup ===\n")

    # --- Settings ---
    print("Current settings (press Enter to keep, or type new value):\n")

    interval = _ask(
        f"Face-lock check interval in minutes [{cfg['face_lock']['check_interval_minutes']}]: ",
        default=str(cfg["face_lock"]["check_interval_minutes"]),
    )
    try:
        cfg["face_lock"]["check_interval_minutes"] = int(interval)
    except ValueError:
        print("Invalid number, keeping default.")

    bypass = _ask(
        f"Bypass key [{cfg['face_lock']['bypass_key']}]: ",
        default=cfg["face_lock"]["bypass_key"],
    )
    cfg["face_lock"]["bypass_key"] = bypass.strip() or "F12"

    url = _ask(
        f"Redirect URL for OK gesture [{cfg['window_closer']['redirect_url']}]: ",
        default=cfg["window_closer"]["redirect_url"],
    )
    cfg["window_closer"]["redirect_url"] = url.strip() or "https://www.google.com"

    tolerance = _ask(
        f"Face recognition tolerance 0.4 (strict) – 0.6 (lenient) [{cfg['face_lock']['tolerance']}]: ",
        default=str(cfg["face_lock"]["tolerance"]),
    )
    try:
        cfg["face_lock"]["tolerance"] = float(tolerance)
    except ValueError:
        print("Invalid value, keeping default.")

    from modules.config import save_config
    save_config(cfg, config_path)
    print(f"\nSettings saved to {config_path}\n")

    # --- Face registration ---
    print("=== Face Registration ===\n")
    do_face = _ask("Register/update your face now? [y/N]: ", default="n").lower()
    if do_face == "y":
        _register_face(cfg)
    else:
        print("Skipping face registration.\n")

    print("Setup complete! Run 'python main.py' to start Guardian.\n")


def _register_face(cfg: dict):
    try:
        import face_recognition # type: ignore
        import cv2
    except ImportError:
        print("\nERROR: face_recognition or opencv not installed.")
        print("Run: pip install face_recognition opencv-python\n")
        return

    print("\nLook directly at the camera.")
    print("We'll capture 10 samples for a robust encoding. Hold still...\n")

    cap = cv2.VideoCapture(cfg.get("camera_index", 0))
    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        return

    encodings = []
    sample_count = 10
    attempts = 0
    max_attempts = 100

    while len(encodings) < sample_count and attempts < max_attempts:
        ret, frame = cap.read()
        if not ret:
            continue
        attempts += 1

        # Show preview
        cv2.imshow("Guardian Setup — Look at the camera (press Q to cancel)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("Cancelled.")
            break

        rgb = cv2.cvtColor(cv2.resize(frame, (0, 0), fx=0.5, fy=0.5), cv2.COLOR_BGR2RGB)
        locs = face_recognition.face_locations(rgb, model="hog")
        if locs:
            enc = face_recognition.face_encodings(rgb, locs)
            if enc:
                encodings.append(enc[0])
                print(f"  Sample {len(encodings)}/{sample_count} captured")
                time.sleep(0.3)
        else:
            if attempts % 10 == 0:
                print("  No face detected yet — make sure your face is visible...")

    cap.release()
    cv2.destroyAllWindows()

    if len(encodings) < 5:
        print(f"\nOnly got {len(encodings)} samples — need at least 5. Try again.")
        return

    face_data_path = cfg["face_lock"]["face_data_path"]
    with open(face_data_path, "wb") as f:
        pickle.dump({"encodings": encodings}, f)

    print(f"\nFace registered! {len(encodings)} samples saved to {face_data_path}")
    print("Face-lock is now active.\n")


def _ask(prompt: str, default: str) -> str:
    try:
        val = input(prompt).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        return default