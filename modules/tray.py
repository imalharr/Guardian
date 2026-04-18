"""
System tray icon for Guardian.
Requires: pip install pystray pillow
"""

import logging
import sys

log = logging.getLogger("guardian.tray")


def run_tray(camera, threads, config_path: str):
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        raise ImportError("pystray/pillow not installed")

    # Draw a simple shield icon
    img = Image.new("RGB", (64, 64), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    # Shield outline
    pts = [(32, 4), (58, 16), (58, 36), (32, 60), (6, 36), (6, 16)]
    draw.polygon(pts, outline=(80, 200, 120), fill=(40, 40, 50))
    # G letter
    draw.text((22, 22), "G", fill=(80, 200, 120))

    def on_quit(icon, item):
        log.info("Quit from tray.")
        icon.stop()
        camera.close()
        sys.exit(0)

    def on_status(icon, item):
        alive = [t.name for t in threads if t.is_alive()]
        log.info("Active modules: %s", ", ".join(alive) if alive else "none")

    menu = pystray.Menu(
        pystray.MenuItem("Guardian — active", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Status (see console)", on_status),
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon("Guardian", img, "Guardian Security Suite", menu)
    icon.run()  # blocks
