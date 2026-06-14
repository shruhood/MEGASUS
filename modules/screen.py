"""
MEGASUS Module: SCREEN - Screenshot, Screen Recording, Mirror
"""
from core.engine import DeviceManager, ADB, _run_shell, _run, log_command
import os
import time

MODULE_NAME = "Screen Tools"
MODULE_ICON = "🖥️"


def screenshot(device_manager, output_dir=".", serial=None):
    """Take screenshot and pull to PC"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    ts = time.strftime("%Y%m%d_%H%M%S")
    remote_file = f"/sdcard/megasus_screenshot_{ts}.png"
    local_file = os.path.join(output_dir, f"megasus_screenshot_{ts}.png")

    # Capture
    stdout, stderr, rc = _run_shell(f"screencap -p '{remote_file}'", device=target, timeout=15)
    if rc != 0:
        return False, stderr or "Screenshot failed"

    time.sleep(0.5)

    # Pull
    stdout, stderr, rc = _run(["-s", target, "pull", remote_file, local_file], timeout=30)
    # Clean up remote
    _run_shell(f"rm -f '{remote_file}'", device=target)

    if rc == 0:
        log_command("screenshot", local_file)
        return True, f"Screenshot saved: {os.path.abspath(local_file)}"
    return False, stderr


def screen_record(device_manager, duration=30, output_dir=".", serial=None):
    """Record screen for specified duration (seconds)"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    duration = min(duration, 180)  # max 3 min (android limit)
    ts = time.strftime("%Y%m%d_%H%M%S")
    remote_file = f"/sdcard/megasus_record_{ts}.mp4"
    local_file = os.path.join(output_dir, f"megasus_record_{ts}.mp4")

    print(f"[*] Recording for {duration}s... (max 180s, press Ctrl+C to stop early)")

    # Start recording in background
    import subprocess as sp
    record_cmd = [_adb_binary_from_engine(), "-s", target, "shell", "screenrecord",
                  "--time-limit", str(duration), remote_file]
    proc = sp.Popen(record_cmd, stdout=sp.PIPE, stderr=sp.PIPE)

    try:
        for i in range(duration):
            time.sleep(1)
            print(f"\r[*] Recording: {i+1}/{duration}s", end="", flush=True)
    except KeyboardInterrupt:
        print("\n[*] Stopping recording...")
        proc.terminate()

    proc.wait(timeout=10)
    print(f"\n[*] Pulling video...")

    # Pull
    stdout, stderr, rc = _run(["-s", target, "pull", remote_file, local_file], timeout=60)
    _run_shell(f"rm -f '{remote_file}'", device=target)

    if rc == 0 and os.path.exists(local_file):
        log_command("screen_record", local_file)
        return True, f"Video saved: {os.path.abspath(local_file)}"
    return False, stderr or "Recording failed"


def _adb_binary_from_engine():
    """Get adb binary path"""
    import yaml
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    try:
        with open(config_file) as f:
            cfg = yaml.safe_load(f)
        return os.path.join(cfg.get("adb", {}).get("path", ""), "adb.exe")
    except Exception:
        return "adb"


def start_mirror(device_manager, serial=None):
    """Launch scrcpy screen mirror"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    # Check if scrcpy is available
    import shutil
    scrcpy_path = shutil.which("scrcpy")
    if not scrcpy_path:
        # Try common locations
        common_paths = [
            r"C:\Program Files\scrcpy\scrcpy.exe",
            r"C:\scrcpy\scrcpy.exe",
            os.path.expanduser(r"~\scrcpy\scrcpy.exe"),
            os.path.expanduser(r"~\Downloads\scrcpy-win64\scrcpy.exe"),
        ]
        for p in common_paths:
            if os.path.exists(p):
                scrcpy_path = p
                break

    if not scrcpy_path:
        return False, "scrcpy not found. Download from: https://github.com/Genymobile/scrcpy/releases"

    print(f"[*] Starting scrcpy mirror for {target}...")
    cmd = [scrcpy_path, "-s", target]
    import subprocess as sp
    proc = sp.Popen(cmd)
    return True, f"scrcpy started (PID {proc.pid}). Close scrcpy window to stop."


def get_screenshot_quick(device_manager, serial=None):
    """Fast screenshot via stdout pipe (no temp file on device)"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    ts = time.strftime("%Y%m%d_%H%M%S")
    local_file = f"megasus_screenshot_{ts}.png"

    import subprocess as sp
    adb_bin = _adb_binary_from_engine()
    # screencap to stdout, save directly
    proc = sp.Popen([adb_bin, "-s", target, "shell", "screencap", "-p"],
                    stdout=sp.PIPE, stderr=sp.PIPE)

    try:
        stdout, stderr = proc.communicate(timeout=15)
        if proc.returncode == 0 and stdout:
            # Remove carriage returns (Windows line ending issue)
            stdout = stdout.replace(b"\r\n", b"\n").replace(b"\r", b"")
            with open(local_file, "wb") as f:
                f.write(stdout)
            return True, f"Screenshot saved: {os.path.abspath(local_file)}"
        return False, "Failed to capture"
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "Timeout"


def set_orientation(device_manager, orientation="0", serial=None):
    """
    Set screen orientation.
    0=portrait, 1=landscape, 2=portrait-reverse, 3=landscape-reverse
    Use 'auto' for auto-rotate
    """
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    if orientation == "auto":
        cmd = "settings put system accelerometer_rotation 1"
    else:
        cmd = (f"settings put system accelerometer_rotation 0 && "
               f"settings put system user_rotation {orientation}")
    stdout, stderr, rc = _run_shell(cmd, device=target)
    return rc == 0, f"Orientation set to {orientation}"


def stay_awake(device_manager, enable=True, serial=None):
    """Keep screen on while charging"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    val = 1 if enable else 0
    stdout, stderr, rc = _run_shell(f"settings put global stay_on_while_plugged_in {val}", device=target)
    state = "ON" if enable else "OFF"
    return rc == 0, f"Stay awake: {state}"


def get_screen_state(device_manager, serial=None):
    """Check if screen is on/off"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("dumpsys power | grep 'Display Power'", device=target)
    if "ON" in stdout:
        return "ON", "Screen is ON"
    return "OFF", "Screen is OFF"


def wake_screen(device_manager, serial=None):
    """Wake screen if off"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    # Press power button
    _run_shell("input keyevent KEYCODE_WAKEUP", device=target)
    _run_shell("input keyevent 26", device=target)  # POWER key
    return True, "Screen wake attempted"


def lock_screen(device_manager, serial=None):
    """Lock screen"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    _run_shell("input keyevent 26", device=target)  # POWER key
    return True, "Screen locked"


def tap(device_manager, x, y, serial=None):
    """Tap at coordinates"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"input tap {x} {y}", device=target)
    return rc == 0, f"Tapped at ({x}, {y})"


def swipe(device_manager, x1, y1, x2, y2, duration=300, serial=None):
    """Swipe gesture"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"input swipe {x1} {y1} {x2} {y2} {duration}", device=target)
    return rc == 0, f"Swiped ({x1},{y1}) -> ({x2},{y2})"


def type_text(device_manager, text, serial=None):
    """Type text on device"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    # Escape special chars for adb shell
    escaped = text.replace(" ", "%s").replace("'", "\\'").replace("&", "\\&").replace("<", "\\<").replace(">", "\\>")
    stdout, stderr, rc = _run_shell(f"input text '{escaped}'", device=target)
    return rc == 0, f"Typed: {text}"
