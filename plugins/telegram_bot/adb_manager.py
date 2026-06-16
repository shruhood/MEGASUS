"""ADB device management for Telegram Bot plugin."""
from __future__ import annotations
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("adb_manager")

class ADBError(Exception):
    pass

class ADBManager:
    """Manages ADB connections and device operations."""

    def __init__(self, adb_path: Optional[str] = None) -> None:
        self._adb_path = adb_path or self._find_adb()

    @staticmethod
    def _find_adb() -> str:
        import yaml, os
        cfg_file = Path(__file__).parent.parent.parent / "config.yaml"
        if cfg_file.exists():
            with open(cfg_file) as f:
                cfg = yaml.safe_load(f) or {}
            p = cfg.get("adb", {}).get("path", "")
            if p:
                base = Path(p)
                exe = base / ("adb.exe" if os.name == "nt" else "adb")
                if exe.exists():
                    return str(exe)
        return "adb.exe" if os.name == "nt" else "adb"

    def _run(self, cmd: list[str], timeout: int = 30) -> Tuple[str, str, int]:
        full_cmd = [self._adb_path] + cmd
        try:
            r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip(), r.stderr.strip(), r.returncode
        except FileNotFoundError:
            raise ADBError("ADB not found: " + self._adb_path)
        except subprocess.TimeoutExpired:
            raise ADBError("ADB command timed out: " + " ".join(cmd))

    def shell(self, cmd: str, timeout: int = 30) -> str:
        out, err, rc = self._run(["shell", cmd], timeout=timeout)
        if rc != 0:
            raise ADBError("Shell error (rc=" + str(rc) + "): " + err)
        return out

    def pull(self, remote: str, local: Path) -> Path:
        local.parent.mkdir(parents=True, exist_ok=True)
        _, err, rc = self._run(["pull", remote, str(local)])
        if rc != 0:
            raise ADBError("Pull failed: " + err)
        return local

    def push(self, local: Path, remote: str) -> None:
        if not local.exists():
            raise ADBError("File not found: " + str(local))
        _, err, rc = self._run(["push", str(local), remote])
        if rc != 0:
            raise ADBError("Push failed: " + err)

    def get_device_info(self) -> dict:
        model = self.shell("getprop ro.product.model")
        brand = self.shell("getprop ro.product.brand")
        android = self.shell("getprop ro.build.version.release")
        sdk = self.shell("getprop ro.build.version.sdk")
        return {"model": model, "brand": brand, "android": android, "sdk": sdk}

    def get_battery_info(self) -> str:
        return self.shell("dumpsys battery")

    def get_running_apps(self, limit: int = 50) -> str:
        return self.shell("pm list packages -3 | head -" + str(limit))

    def get_storage(self) -> str:
        return self.shell("df -h /data /sdcard")

    def get_network_info(self) -> str:
        return self.shell("ip addr show | grep -E " + chr(39) + "inet |wlan|rmnet" + chr(39))

    def take_screenshot(self, output_dir: Path) -> Path:
        from datetime import datetime
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote = "/sdcard/mgs_ss.png"
        local = output_dir / "ss_" + ts + ".png"
        self.shell("screencap -p " + remote)
        return self.pull(remote, local)

    def list_directory(self, path: str = "/sdcard") -> str:
        return self.shell("ls -la " + path)
