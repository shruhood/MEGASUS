"""
MEGASUS Core Engine - ADB Command Runner & Device Manager
Built for speed, zero bloat, maximum control

Author: Suraj Singh (@shruhood) — Bakweb, SunDial Technologies, Cyber SunDial
"""
import subprocess
import os
import sys
import re
import time
import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path

# ── Config Loader ──────────────────────────────────────────────
try:
    import yaml
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(CONFIG_FILE, "r") as f:
        CONFIG = yaml.safe_load(f)
except Exception:
    CONFIG = {}

ADB_PATH = CONFIG.get("adb", {}).get("path", "")
ADB_TIMEOUT = CONFIG.get("connection", {}).get("default_timeout", 10)


def _adb_binary():
    """Return full path to adb binary (cross-platform)."""
    if ADB_PATH:
        base = os.path.join(ADB_PATH, "adb.exe" if os.name == "nt" else "adb")
        if os.path.exists(base): return base
        alt = os.path.join(ADB_PATH, "adb" if os.name == "nt" else "adb.exe")
        if os.path.exists(alt): return alt
        return base
    return "adb.exe" if os.name == "nt" else "adb"


def _run(cmd, timeout=None, shell=False):
    """
    Run an ADB command and return (stdout, stderr, returncode).
    This is the ONLY function that talks to adb. Everything goes through here.
    """
    full_cmd = [_adb_binary()] + cmd if isinstance(cmd, list) else cmd
    try:
        r = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout or ADB_TIMEOUT,
            shell=shell,
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError:
        return "", f"ERROR: adb not found at '{_adb_binary()}'. Install Android Platform Tools.", 127
    except subprocess.TimeoutExpired:
        return "", "ERROR: Command timed out", 124
    except Exception as e:
        return "", f"ERROR: {e}", -1


def _run_shell(cmd_str, device=None, timeout=None):
    """Run a shell command on the device: adb shell <cmd_str>"""
    base = ["shell", cmd_str]
    if device:
        base = ["-s", device, "shell", cmd_str]
    return _run(base, timeout=timeout)


def log_command(cmd, output="", user="admin"):
    """Audit log every command for accountability"""
    if not CONFIG.get("logging", {}).get("enabled", False):
        return
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(log_dir, f"audit_{datetime.now().strftime('%Y%m%d')}.log")
    entry = f"[{ts}] [{user}] CMD: {cmd} | RC: {output[:200] if output else 'ok'}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


# ── Device Manager ──────────────────────────────────────────────
class DeviceManager:
    """Manages connected ADB devices — USB and Wireless"""

    def __init__(self):
        self.devices = {}
        self.active_device = None
        self._refresh()

    def _refresh(self):
        """Refresh device list from adb"""
        stdout, stderr, rc = _run(["devices", "-l"], timeout=15)
        self.devices = {}
        if rc != 0:
            return
        for line in stdout.splitlines()[1:]:  # skip "List of devices attached"
            line = line.strip()
            if not line or "offline" in line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial = parts[0]
            status = parts[1]
            # Parse -l fields
            info = {"serial": serial, "status": status, "model": "", "device": "", "product": "", "transport": ""}
            for p in parts[2:]:
                if ":" in p:
                    k, v = p.split(":", 1)
                    info[k] = v
            self.devices[serial] = info

    def list_devices(self):
        """Return list of connected devices"""
        self._refresh()
        return self.devices

    def get_active(self):
        """Return active device serial"""
        if self.active_device and self.active_device in self.devices:
            return self.active_device
        # Auto-select if only one device
        if len(self.devices) == 1:
            self.active_device = list(self.devices.keys())[0]
        return self.active_device

    def set_active(self, serial):
        """Set active device by serial"""
        if serial in self.devices:
            self.active_device = serial
            return True
        return False

    def connect_wireless(self, ip, port=5555):
        """Connect to device over WiFi: adb connect ip:port"""
        stdout, stderr, rc = _run(["connect", f"{ip}:{port}"], timeout=15)
        self._refresh()
        return stdout, stderr, rc

    def disconnect(self, serial=None):
        """Disconnect a device"""
        cmd = ["disconnect"]
        if serial:
            cmd.append(serial)
        return _run(cmd, timeout=10)

    def restart_server(self):
        """Kill and restart ADB server"""
        _run(["kill-server"], timeout=10)
        time.sleep(1)
        stdout, stderr, rc = _run(["start-server"], timeout=15)
        time.sleep(1)
        self._refresh()
        return stdout, stderr, rc

    def get_device_count(self):
        self._refresh()
        return len(self.devices)


# ── ADB Command Builder ─────────────────────────────────────────
class ADB:
    """
    Fluent ADB command builder.
    Usage:
        adb = ADB(device="RZCT806RANE")
        adb.shell("ls /sdcard").run()
        adb.push("local.apk", "/sdcard/remote.apk").run()
    """

    def __init__(self, device=None):
        self.device = device
        self._cmd = []

    def _build(self, *args):
        cmd = []
        if self.device:
            cmd.extend(["-s", self.device])
        cmd.extend(list(args))
        return cmd

    def shell(self, command):
        self._cmd = self._build("shell", command)
        return self

    def push(self, local, remote):
        self._cmd = self._build("push", local, remote)
        return self

    def pull(self, remote, local):
        self._cmd = self._build("pull", remote, local)
        return self

    def install(self, apk_path):
        self._cmd = self._build("install", "-r", apk_path)
        return self

    def uninstall(self, package):
        self._cmd = self._build("uninstall", package)
        return self

    def forward(self, local, remote):
        self._cmd = self._build("forward", local, remote)
        return self

    def reverse(self, remote, local):
        self._cmd = self._build("reverse", remote, local)
        return self

    def run(self, timeout=None):
        stdout, stderr, rc = _run(self._cmd, timeout=timeout)
        log_command(" ".join(self._cmd), stdout[:200])
        return stdout, stderr, rc


# ── Utility Functions ───────────────────────────────────────────
def human_size(size_bytes):
    """Convert bytes to human readable"""
    if not size_bytes:
        return "0 B"
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return str(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def parse_table(text, delimiter=None):
    """Parse adb shell command output into list of dicts"""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    if delimiter:
        return [{f"col_{i}": v for i, v in enumerate(l.split(delimiter))} for l in lines]
    return lines


def check_adb():
    """Check if ADB is available and working"""
    stdout, stderr, rc = _run(["version"], timeout=10)
    if rc == 0:
        return True, stdout
    return False, stderr or "ADB not found"


def check_device_connected(device_manager):
    """Check if any device is connected and authorized"""
    devices = device_manager.list_devices()
    for serial, info in devices.items():
        if info["status"] == "device":
            return True, serial
        if info["status"] == "unauthorized":
            return False, "Device found but unauthorized. Accept USB debugging prompt on phone."
    return False, "No device found. Connect phone via USB and enable USB debugging."
