import json
import logging

log = logging.getLogger("guardian.config")


def default_config():
    return {
        "camera_index": 0,
        "tab_switcher": {
            "enabled": True,
            "cooldown_seconds": 1.5,
            "confidence_frames": 8,   # frames gesture must be held before firing
        },
        "face_lock": {
            "enabled": True,
            "check_interval_minutes": 5,
            "face_data_path": "face_data.pkl",
            "blackout_seconds": 20,
            "bypass_key": "F12",
            "re_verify_seconds": 15,   # after bypass, how long until face-lock re-arms
            "tolerance": 0.55,         # lower = stricter face match (0.4–0.6 recommended)
        },
        "window_closer": {
            "enabled": True,
            "cooldown_seconds": 2.0,
            "confidence_frames": 10,
            "redirect_url": "https://www.google.com",
        },
    }


def load_config(path: str) -> dict:
    with open(path) as f:
        data = json.load(f)
    # Merge with defaults so new keys don't break old configs
    merged = default_config()
    _deep_merge(merged, data)
    return merged


def save_config(cfg: dict, path: str):
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
    log.info("Config saved to %s", path)


def _deep_merge(base: dict, override: dict):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
