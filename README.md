# 🛡️ Guardian — Personal Security Suite

A lightweight, gesture-powered security tool that runs silently in your system tray.

## Features

| Module | Trigger | Action |
|--------|---------|--------|
| **Tab Switcher** | ✋ Open hand | `Alt+Tab` (next window) |
| **Tab Switcher** | ✊ Fist | `Shift+Alt+Tab` (previous window) |
| **Face Lock** | Unknown face for 20s | Full-screen blackout |
| **Window Closer** | 👌 OK gesture | Close window + open your URL |

---

## Installation

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/guardian.git
cd guardian
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

> **Note on `face_recognition`**: This library requires `cmake` and `dlib` to compile.
> - **Windows**: Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) first
> - **macOS**: `brew install cmake`
> - **Linux**: `sudo apt install cmake libboost-all-dev`
> 
> Then: `pip install face_recognition`

### 3. First-time setup
```bash
python main.py --setup
```

This will:
- Let you configure the check interval, bypass key, and redirect URL
- Register your face for the face-lock module (look at your webcam)

### 4. Run
```bash
python main.py
```

Guardian starts silently in the system tray. Right-click the icon to quit.

---

## Run on startup

### Windows
Add a shortcut to `main.py` in:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

### macOS
Create a `launchd` plist in `~/Library/LaunchAgents/`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.guardian.security</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/path/to/guardian/main.py</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
```

### Linux (systemd)
```ini
[Unit]
Description=Guardian Security Suite

[Service]
ExecStart=/usr/bin/python3 /path/to/guardian/main.py --no-tray
Restart=on-failure

[Install]
WantedBy=default.target
```

---

## Configuration

Edit `config.json` (auto-created on first run):

```json
{
  "camera_index": 0,
  "tab_switcher": {
    "enabled": true,
    "cooldown_seconds": 1.5,
    "confidence_frames": 8
  },
  "face_lock": {
    "enabled": true,
    "check_interval_minutes": 5,
    "blackout_seconds": 20,
    "bypass_key": "F12",
    "re_verify_seconds": 15,
    "tolerance": 0.55
  },
  "window_closer": {
    "enabled": true,
    "cooldown_seconds": 2.0,
    "confidence_frames": 10,
    "redirect_url": "https://www.google.com"
  }
}
```

**Disable a module**: set `"enabled": false` in its section.

**Face recognition tolerance**: `0.4` = strict (fewer false positives), `0.6` = lenient (easier to match). Default `0.55` works well for most lighting conditions.

---

## Project structure

```
guardian/
├── main.py                  # Entry point
├── config.json              # User settings (auto-created)
├── face_data.pkl            # Your face encodings (auto-created on setup)
├── requirements.txt
└── modules/
    ├── config.py            # Config load/save
    ├── camera.py            # Shared webcam singleton
    ├── gesture.py           # MediaPipe gesture detection
    ├── tab_switcher.py      # Module 1
    ├── face_lock.py         # Module 2
    ├── window_closer.py     # Module 3
    ├── setup.py             # First-time setup wizard
    └── tray.py              # System tray icon
```

---

## Troubleshooting

**Camera won't open**: Make sure no other app (Zoom, Teams, etc.) is using the webcam.

**Gestures not triggering**: Try adjusting lighting. MediaPipe works best with even, front-facing light. Increase `confidence_frames` if you're getting false positives, decrease it if gestures are sluggish.

**Face not recognised**: Re-run `--setup` and capture samples in the same lighting conditions you'll use day-to-day. Increase `tolerance` slightly if you're getting locked out too often.

**High CPU**: The camera module runs at ~20fps. If CPU is a concern, you can lower this by editing the `time.sleep(0.05)` calls in each module to `time.sleep(0.1)`.

---

## Roadmap / Ideas

See [IDEAS.md](IDEAS.md) for planned features.

---

## Contributing

PRs welcome! Each new security tool should be:
- A self-contained file in `modules/`
- Registered in `main.py` with an `enabled` flag in `config.json`
- Documented in this README

---

## License

MIT
