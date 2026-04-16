# Guardian — Ideas & Roadmap

## Planned modules

### Module 4 — Panic clipboard wipe
Keyboard shortcut (e.g. `Ctrl+Shift+Del`) instantly clears the clipboard. Useful before stepping away from your machine.

### Module 5 — Idle screen lock
If no keyboard/mouse activity for N minutes AND the webcam sees no face, lock the screen (via the OS lock command). More reliable than just a timer because it won't lock while you're reading.

### Module 6 — USB sentinel
Alerts you (notification + log) whenever a new USB device is connected. Useful for detecting someone plugging in a keylogger or USB drop.

### Module 7 — Network watchdog
Monitors active connections and alerts when a new process starts making outbound connections. Can auto-kill processes that match a blocklist.

### Module 8 — Shoulder-surf detector
Uses the webcam to estimate how many faces are visible. If more than 1 face is detected while the screen has content, blur or minimize it. Great for working in coffee shops.

### Module 9 — Voice panic phrase
Listens for a configurable spoken phrase ("hey guardian lock") and triggers an immediate screen lock + mic mute. Uses Vosk for offline speech recognition.

### Module 10 — Screenshot guard
Intercepts screenshot hotkeys (PrtScn, Cmd+Shift+3, etc.) and either blocks them or watermarks the result with the current timestamp and username.

### Module 11 — Two-hand unlock
Require a specific two-handed gesture (e.g. both palms facing camera) to unlock the machine after idle lock — an alternative to a password for quick re-entry.

### Module 12 — App-specific face lock
Trigger face verification when specific apps open (e.g. your banking app, password manager). If the face check fails, the app closes.

---

## UI improvements

- Settings dashboard (tkinter or web-based via Flask)
- Per-module enable/disable toggle from tray menu
- Live gesture preview window (debug mode)
- Log viewer in tray menu

## Platform improvements

- Windows startup registry entry (via `winreg`)
- macOS notarization + `.app` bundle
- Linux: Wayland compatibility (pyautogui has limits on Wayland — explore `ydotool` as alternative)
