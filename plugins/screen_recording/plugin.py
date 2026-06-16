"""MEGASUS Screen Recording Plugin — Record, convert, compress, trim."""
from __future__ import annotations
import os
import time
import logging
import subprocess
from datetime import datetime
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("screen_recording")
RECORD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "recordings")


class ScreenRecordingPlugin(Plugin):
    """Screen recording with quality settings and post-processing."""

    name = "screen_recording"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Record screen with quality settings and post-processing"

    def __init__(self) -> None:
        super().__init__()
        os.makedirs(RECORD_DIR, exist_ok=True)
        self._recording = False

    def _ts(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def record(self, duration: int = 30, bitrate: str = "4M",
               size: str = "720x1280", output_name: str = "") -> str:
        """Record device screen."""
        if not output_name:
            output_name = f"rec_{self._ts()}.mp4"
        remote_path = f"/sdcard/{output_name}"
        local_path = os.path.join(RECORD_DIR, output_name)

        self.log(f"Recording for {duration}s at {bitrate}...")
        self._recording = True

        cmd = f"screenrecord --bit-rate {bitrate} --size {size} --time-limit {duration} {remote_path}"
        out, err, rc = self.adb_shell(cmd, timeout=duration + 15)
        self._recording = False

        if rc != 0:
            self.log(f"Record failed: {err}")
            return ""

        # Pull
        out2, err2, rc2 = self.adb(["pull", remote_path, local_path])
        if rc2 == 0:
            self.adb_shell(f"rm {remote_path}")
            size_mb = os.path.getsize(local_path) / 1048576
            self.log(f"Saved: {local_path} ({size_mb:.1f} MB)")
            return local_path
        return ""

    def record_audio(self, duration: int = 10) -> str:
        """Record audio via mic."""
        ts = self._ts()
        remote_path = f"/sdcard/aud_{ts}.mp4"
        local_path = os.path.join(RECORD_DIR, f"aud_{ts}.mp4")

        self.log(f"Recording audio for {duration}s...")
        self.adb_shell(f"screenrecord --time-limit {duration} {remote_path}", timeout=duration + 10)
        self.adb(["pull", remote_path, local_path])
        self.adb_shell(f"rm {remote_path}")
        return local_path

    def trim(self, input_path: str, start_sec: int, end_sec: int) -> str:
        """Trim recording using ffmpeg if available."""
        output_path = input_path.replace(".mp4", "_trimmed.mp4")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", input_path,
                 "-ss", str(start_sec), "-to", str(end_sec),
                 "-c", "copy", output_path],
                capture_output=True, timeout=60,
            )
            if os.path.exists(output_path):
                self.log(f"Trimmed: {output_path}")
                return output_path
        except FileNotFoundError:
            self.log("ffmpeg not found — install ffmpeg for trimming")
        except Exception as e:
            self.log(f"Trim error: {e}")
        return ""

    def compress(self, input_path: str, crf: int = 28) -> str:
        """Compress video using ffmpeg."""
        output_path = input_path.replace(".mp4", "_compressed.mp4")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", input_path,
                 "-crf", str(crf), "-preset", "fast", output_path],
                capture_output=True, timeout=120,
            )
            if os.path.exists(output_path):
                orig = os.path.getsize(input_path) / 1048576
                comp = os.path.getsize(output_path) / 1048576
                self.log(f"Compressed: {orig:.1f}MB -> {comp:.1f}MB")
                return output_path
        except FileNotFoundError:
            self.log("ffmpeg not found")
        except Exception as e:
            self.log(f"Compress error: {e}")
        return ""

    def list_recordings(self) -> list[str]:
        files = sorted(
            [f for f in os.listdir(RECORD_DIR) if f.endswith((".mp4", ".mkv"))],
            reverse=True,
        )
        return [os.path.join(RECORD_DIR, f) for f in files]

    def run(self) -> None:
        """Interactive recording menu."""
        print("\n  === SCREEN RECORDING ===")
        print("  1. Record screen (default 30s)")
        print("  2. Record screen (custom)")
        print("  3. Record audio only")
        print("  4. List recordings")
        print("  5. Trim recording (ffmpeg)")
        print("  6. Compress recording (ffmpeg)")
        print("  0. Back")

        choice = input("\n  Choice: ").strip()
        if choice == "0":
            return
        elif choice == "1":
            p = self.record()
            if p:
                print(f"  Saved: {p}")
        elif choice == "2":
            dur = int(input("  Duration sec [30]: ").strip() or "30")
            bitrate = input("  Bitrate [4M]: ").strip() or "4M"
            size = input("  Size WxH [720x1280]: ").strip() or "720x1280"
            p = self.record(duration=dur, bitrate=bitrate, size=size)
            if p:
                print(f"  Saved: {p}")
        elif choice == "3":
            dur = int(input("  Duration sec [10]: ").strip() or "10")
            p = self.record_audio(dur)
            print(f"  Saved: {p}")
        elif choice == "4":
            files = self.list_recordings()
            for f in files:
                size = os.path.getsize(f) / 1048576
                print(f"  {os.path.basename(f):40s} {size:.1f} MB")
        elif choice == "5":
            files = self.list_recordings()
            if not files:
                print("  No recordings")
                return
            for i, f in enumerate(files[:10]):
                print(f"  {i+1}. {os.path.basename(f)}")
            idx = int(input("  Select: ").strip()) - 1
            start = int(input("  Start sec: ").strip())
            end = int(input("  End sec: ").strip())
            p = self.trim(files[idx], start, end)
            print(f"  Result: {p}")
        elif choice == "6":
            files = self.list_recordings()
            if not files:
                print("  No recordings")
                return
            for i, f in enumerate(files[:10]):
                print(f"  {i+1}. {os.path.basename(f)}")
            idx = int(input("  Select: ").strip()) - 1
            crf = int(input("  CRF (18-35, lower=better) [28]: ").strip() or "28")
            p = self.compress(files[idx], crf)
            print(f"  Result: {p}")

    def shutdown(self) -> None:
        self.log("Shutting down Screen Recording plugin")


def register() -> dict[str, Any]:
    plugin = ScreenRecordingPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
