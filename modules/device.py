"""
MEGASUS Module: DEVICE - Device Info & Control
Get full device info, battery, storage, sensors, control power states
"""
from core.engine import DeviceManager, ADB, _run_shell, human_size, log_command

MODULE_NAME = "Device Info & Control"
MODULE_ICON = "📱"


def get_device_info(device_manager):
    """Get comprehensive device information"""
    devices = device_manager.list_devices()
    if not devices:
        return None, "No devices connected"

    results = {}
    for serial, info in devices.items():
        dev_results = {"basic": info}

        # Build.prop dump
        stdout, _, _ = _run_shell("getprop", device=serial, timeout=15)
        props = {}
        for line in stdout.splitlines():
            line = line.strip()
            if ": " in line:
                # Parse [key]: [value]
                m = line.split(": ", 1)
                if len(m) == 2:
                    k = m[0].strip().strip("[]")
                    v = m[1].strip().strip("[]")
                    props[k] = v
        dev_results["props"] = props

        # Key properties we care about
        key_props = {
            "ro.product.model": "Model",
            "ro.product.brand": "Brand",
            "ro.product.name": "Product",
            "ro.build.version.release": "Android Version",
            "ro.build.version.sdk": "SDK Level",
            "ro.build.display.id": "Build",
            "ro.build.type": "Build Type",
            "ro.debuggable": "Debuggable",
            "ro.secure": "Secure",
            "ro.build.tags": "Build Tags",
            "ro.hardware": "Hardware",
            "ro.board.platform": "Platform",
            "ro.product.cpu.abi": "CPU ABI",
            "persist.sys.timezone": "Timezone",
            "ro.serialno": "Serial",
        }
        summary = {}
        for prop_key, label in key_props.items():
            summary[label] = props.get(prop_key, "N/A")
        dev_results["summary"] = summary

        # Battery
        stdout, _, _ = _run_shell("dumpsys battery", device=serial)
        battery = {}
        for line in stdout.splitlines():
            if ":" in line:
                k, v = line.strip().split(":", 1)
                battery[k.strip()] = v.strip()
        dev_results["battery"] = battery

        # Screen info
        stdout, _, _ = _run_shell("wm size", device=serial)
        dev_results["screen_size"] = stdout.strip()
        stdout, _, _ = _run_shell("wm density", device=serial)
        dev_results["screen_density"] = stdout.strip()

        # Uptime
        stdout, _, _ = _run_shell("uptime", device=serial)
        dev_results["uptime"] = stdout.strip()

        # SELinux
        stdout, _, _ = _run_shell("getenforce", device=serial)
        dev_results["selinux"] = stdout.strip()

        results[serial] = dev_results

    return results, "OK"


def get_storage_info(device_manager, serial=None):
    """Get storage usage"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No active device"

    stdout, _, _ = _run_shell("df -h", device=target)
    storage = {}
    for line in stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 6:
            storage[parts[5]] = {
                "filesystem": parts[0],
                "size": parts[1],
                "used": parts[2],
                "available": parts[3],
                "use_percent": parts[4],
            }
    return storage, "OK"


def get_battery_info(device_manager, serial=None):
    """Get battery status"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("dumpsys battery", device=target)
    info = {}
    for line in stdout.splitlines():
        if ":" in line:
            k, v = line.strip().split(":", 1)
            info[k.strip()] = v.strip()
    return info, "OK"


def power_off(device_manager, serial=None):
    """Power off device"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell("reboot -p", device=target)
    log_command(f"power_off {target}", stdout)
    return rc == 0, stdout or stderr


def reboot(device_manager, serial=None, mode=None):
    """Reboot device. mode: None=normal, 'recovery', 'bootloader', 'fastboot'"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    cmd = "reboot"
    if mode:
        cmd = f"reboot {mode}"
    stdout, stderr, rc = _run_shell(cmd, device=target)
    log_command(f"reboot {target} mode={mode}", stdout)
    return rc == 0, stdout or stderr


def toggle_wifi(device_manager, enable=True, serial=None):
    """Toggle WiFi on/off"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    cmd = "svc wifi enable" if enable else "svc wifi disable"
    stdout, stderr, rc = _run_shell(cmd, device=target)
    state = "ON" if enable else "OFF"
    return rc == 0, f"WiFi turned {state}: {stdout or stderr}"


def toggle_airplane(device_manager, enable=True, serial=None):
    """Toggle airplane mode"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    cmd = f"settings put global airplane_mode_on {1 if enable else 0}"
    _run_shell(cmd, device=target)
    # Broadcast the change
    _run_shell("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true" if enable else
               "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false", device=target)
    state = "ON" if enable else "OFF"
    return True, f"Airplane mode {state}"


def change_hostname(device_manager, hostname, serial=None):
    """Change device hostname"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"setprop net.hostname {hostname}", device=target)
    return rc == 0, f"Hostname set to {hostname}"


def dump_build_prop(device_manager, output_file=None, serial=None):
    """Dump full build.prop to file"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, _, _ = _run_shell("cat /system/build.prop", device=target, timeout=30)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(stdout)
        return True, f"Build.prop saved to {output_file}"
    return True, stdout


def get_connected_wifi(device_manager, serial=None):
    """Get currently connected WiFi network"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("dumpsys wifi | grep 'mWifiInfo'", device=target)
    if not stdout:
        stdout, _, _ = _run_shell("dumpsys connectivity | grep -i 'wifi'", device=target)
    return stdout.strip(), "OK"


def set_screen_brightness(device_manager, level, serial=None):
    """Set screen brightness (0-255)"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    level = max(0, min(255, int(level)))
    stdout, stderr, rc = _run_shell(
        f"settings put system screen_brightness {level}", device=target
    )
    return rc == 0, f"Brightness set to {level}"


def set_screen_timeout(device_manager, seconds, serial=None):
    """Set screen timeout in seconds"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    ms = int(seconds) * 1000
    stdout, stderr, rc = _run_shell(
        f"settings put system screen_off_timeout {ms}", device=target
    )
    return rc == 0, f"Screen timeout set to {seconds}s"


def get_cpu_info(device_manager, serial=None):
    """Get CPU information"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("cat /proc/cpuinfo", device=target)
    info = {}
    for line in stdout.splitlines():
        if ":" in line:
            k, v = line.strip().split(":", 1)
            info[k.strip()] = v.strip()
    return info, "OK"


def get_ram_info(device_manager, serial=None):
    """Get RAM information"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("cat /proc/meminfo", device=target)
    info = {}
    for line in stdout.splitlines():
        if ":" in line:
            k, v = line.strip().split(":", 1)
            info[k.strip()] = v.strip()
    return info, "OK"


def get_installed_users(device_manager, serial=None):
    """Get list of users/profiles on device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("pm list users", device=target)
    return stdout, "OK"
