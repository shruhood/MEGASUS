"""
MEGASUS Module: CONNECTION - USB + WiFi Multi-Device Manager
"""
from core.engine import DeviceManager, _run, log_command
import time

MODULE_NAME = "Connection Manager"
MODULE_ICON = "🔗"


def list_all(device_manager):
    """List all connected devices with full details"""
    devices = device_manager.list_devices()
    result = []
    for serial, info in devices.items():
        d = dict(info)
        # Add extra details
        stdout, _, _ = _run(["-s", serial, "shell", "getprop", "ro.product.model"])
        if stdout.strip():
            d["model_name"] = stdout.strip()
        stdout, _, _ = _run(["-s", serial, "shell", "getprop", "ro.build.version.release"])
        if stdout.strip():
            d["android_version"] = stdout.strip()
        # Transport type
        if "transport" in info:
            d["transport_type"] = "WiFi" if info.get("transport") == "tcp" else "USB"
        else:
            d["transport_type"] = "USB"
        result.append(d)
    return result


def connect_wireless(device_manager, ip, port=5555):
    """Connect to device over WiFi"""
    print(f"[*] Connecting to {ip}:{port}...")
    stdout, stderr, rc = device_manager.connect_wireless(ip, port)
    log_command(f"connect_wireless {ip}:{port}", stdout)
    if "connected" in stdout.lower() or "already connected" in stdout.lower():
        return True, stdout
    if "cannot connect" in stdout.lower() or "failed" in stdout.lower():
        return False, stdout
    return rc == 0, stdout or stderr


def disconnect_device(device_manager, serial=None):
    """Disconnect specific or all wireless devices"""
    stdout, stderr, rc = device_manager.disconnect(serial)
    return rc == 0, stdout or stderr


def pair_wireless(device_manager, device_ip, port=5555):
    """Pair and connect to wireless device"""
    # First set device to listen
    print("[*] Put device in wireless debugging mode (Settings > Developer > Wireless)")
    print(f"[*] Attempting connection to {device_ip}:{port}...")
    return connect_wireless(device_manager, device_ip, port)


def restart_adb_server(device_manager):
    """Restart ADB server"""
    print("[*] Restarting ADB server...")
    stdout, stderr, rc = device_manager.restart_server()
    time.sleep(2)
    return rc == 0, stdout or str(stderr)


def troubleshoot(device_manager):
    """Full troubleshooting checklist"""
    results = []
    results.append("=== MEGASUS TROUBLESHOOT ===")

    # 1. Check ADB
    stdout, stderr, rc = _run(["version"], timeout=10)
    if rc == 0:
        results.append(f"[OK] ADB: {stdout}")
    else:
        results.append(f"[FAIL] ADB not found: {stderr}")
        return results

    # 2. Check server
    stdout, stderr, rc = _run(["start-server"], timeout=10)
    results.append(f"[OK] Server: {stdout or 'running'}")
    time.sleep(1)

    # 3. Check devices
    devices = device_manager.list_devices()
    if devices:
        for serial, info in devices.items():
            status = info["status"]
            if status == "device":
                results.append(f"[OK] Device {serial}: connected & authorized")
            elif status == "unauthorized":
                results.append(f"[WARN] Device {serial}: UNAUTHORIZED - Accept prompt on phone")
            elif status == "offline":
                results.append(f"[WARN] Device {serial}: OFFLINE")
            else:
                results.append(f"[??] Device {serial}: {status}")
    else:
        results.append("[FAIL] No devices detected")

    # 4. Check adbusb driver hint
    results.append("")
    results.append("TIPS:")
    results.append("- Use a DATA cable (not charge-only)")
    results.append("- Accept 'Allow USB Debugging' prompt on phone")
    results.append("- Settings > Developer > Revoke USB debugging > reconnect")
    results.append("- Try different USB port")
    results.append("- On phone: Settings > Developer > USB Debugging ON")

    return results


def tcpip_mode(device_manager, port=5555, serial=None):
    """Switch USB device to TCP/IP mode"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run(["-s", target, "tcpip", str(port)], timeout=10)
    if rc == 0:
        # Get device IP
        time.sleep(1)
        ip_out, _, _ = _run(["-s", target, "shell", "ip", "addr", "show", "wlan0"])
        import re
        ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", ip_out)
        ip = ip_match.group(1) if ip_match else "unknown"
        return True, f"TCP/IP mode on port {port}. Device IP: {ip}\nUse: connect {ip}:{port}"
    return False, stderr


def usb_mode(device_manager, serial=None):
    """Switch back to USB mode"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run(["-s", target, "usb"], timeout=10)
    return rc == 0, stdout or stderr


def get_connection_history():
    """Show session connection history"""
    logfile = "logs/connection_history.log"
    if not os.path.exists(logfile):
        return "No history yet"
    try:
        with open(logfile, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[-50:])
    except Exception:
        return "Error reading history"


import os
