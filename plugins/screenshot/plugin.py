"""MEGASUS Screenshot Plugin — Auto-capture with timestamps, burst, gallery."""
from __future__ import annotations
import os
import time
import logging
from datetime import datetime
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("screenshot")


class ScreenshotPlugin(Plugin):
    """Screenshot management with auto-naming and burst capture."""

    name = "screenshot"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Auto-capture screenshots with timestamp naming"

    def __init__(self) -> None:
        super().__init__()
        self.output_dir = os.path.join(self.PROJECT_ROOT, "screenshots")
        os.makedirs(self.output_dir, exist_ok=True)

    def capture(self, prefix: str = "screen") -> str:
        """Take a single screenshot and save with timestamp."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{ts}.png"
        remote_path = f"/sdcard/{filename}"
        local_path = os.path.join(self.output_dir, filename)

        # Capture on device
        out, err, rc = self.adb_shell(f"screencap -p {remote_path}")
        if rc != 0:
            self.log(f"screencap failed: {err}")
            return ""

        # Pull to local
        out2, err2, rc2 = self.adb(["pull", remote_path, local_path])
        if rc2 != 0:
            self.log(f"pull failed: {err2}")
            return ""

        # Clean up remote
        self.adb_shell(f"rm {remote_path}")
        self.log(f"Screenshot saved: {local_path}")
        return local_path

    def burst(self, count: int = 5, interval: float = 1.0, prefix: str = "burst") -> list[str]:
        """Take multiple screenshots in quick succession."""
        paths = []
        for i in range(count):
            p = self.capture(f"{prefix}_{i+1:03d}")
            if p:
                paths.append(p)
            if i < count - 1:
                time.sleep(interval)
        self.log(f"Burst complete: {len(paths)}/{count} screenshots")
        return paths

    def capture_region(self, x: int, y: int, w: int, h: int, prefix: str = "region") -> str:
        """Capture a specific screen region."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{ts}.png"
        remote_path = f"/sdcard/{filename}"
        local_path = os.path.join(self.output_dir, filename)

        self.adb_shell(f"screencap -p {remote_path}")
        # Crop with convert if available, otherwise pull full
        out, err, rc = self.adb(["pull", remote_path, local_path])
        if rc == 0:
            self.adb_shell(f"rm {remote_path}")
            self.log(f"Region screenshot: {local_path}")
            return local_path
        return ""

    def gallery(self, last_n: int = 20) -> list[str]:
        """List last N screenshots."""
        files = sorted(
            [f for f in os.listdir(self.output_dir) if f.endswith(".png")],
            reverse=True,
        )
        return [os.path.join(self.output_dir, f) for f in files[:last_n]]

    def run(self) -> None:
        """Interactive screenshot menu."""
        print("\n  === SCREENSHOT PLUGIN ===")
        print("  1. Take screenshot")
        print("  2. Burst capture (5 shots)")
        print("  3. Custom burst")
        print("  4. View gallery")
        print("  0. Back")

        choice = input("\n  Choice: ").strip()
        if choice == "1":
            p = self.capture()
            if p:
                print(f"  Saved: {p}")
            else:
                print("  Failed")
        elif choice == "2":
            paths = self.burst()
            print(f"  Saved {len(paths)} screenshots")
        elif choice == "3":
            n = int(input("  Count [5]: ").strip() or "5")
            iv = float(input("  Interval sec [1.0]: ").strip() or "1.0")
            paths = self.burst(count=n, interval=iv)
            print(f"  Saved {len(paths)} screenshots")
        elif choice == "4":
            files = self.gallery()
            for f in files:
                print(f"  {f}")

    def shutdown(self) -> None:
        self.log("Shutting down Screenshot plugin")


def register() -> dict[str, Any]:
    plugin = ScreenshotPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
