"""
MEGASUS Module: APPS - Application Management
Install, uninstall, start, stop, freeze, clear data, permissions
"""
from core.engine import DeviceManager, ADB, _run_shell, _run, log_command
import os

MODULE_NAME = "App Manager"
MODULE_ICON = "📦"


def list_apps(device_manager, filter_type="all", serial=None):
    """
    List installed apps.
    filter_type: all, system, third_party, enabled, disabled
    """
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    flag_map = {
        "all": "",
        "system": "-s",
        "third_party": "-3",
        "enabled": "-e",
        "disabled": "-d",
    }
    flag = flag_map.get(filter_type, "")

    cmd = ["-s", target, "shell", "pm", "list", "packages"]
    if flag:
        cmd.append(flag)

    stdout, stderr, rc = _run(cmd, timeout=15)
    if rc != 0:
        return None, stderr

    apps = []
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            pkg = line.split(":", 1)[1].strip()
            apps.append(pkg)
    return sorted(apps), "OK"


def get_app_info(device_manager, package, serial=None):
    """Get detailed info about an app"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Package info
    stdout, _, _ = _run(["-s", target, "shell", "dumpsys", "package", package], timeout=15)
    if not stdout:
        return None, f"Package {package} not found"

    info = {"package": package}
    for line in stdout.splitlines():
        line = line.strip()
        if "versionName=" in line:
            info["version"] = line.split("versionName=", 1)[1].split()[0]
        elif "versionCode=" in line:
            info["version_code"] = line.split("versionCode=", 1)[1].split()[0]
        elif "targetSdk=" in line:
            info["target_sdk"] = line.split("targetSdk=", 1)[1].split()[0]
        elif "firstInstallTime=" in line:
            info["first_install"] = line.split("firstInstallTime=", 1)[1]
        elif "lastUpdateTime=" in line:
            info["last_update"] = line.split("lastUpdateTime=", 1)[1]

    # Permissions
    stdout2, _, _ = _run(["-s", target, "shell", "dumpsys", "package", package], timeout=15)
    perms = []
    in_perms = False
    for line in stdout2.splitlines():
        if "requested permissions:" in line:
            in_perms = True
            continue
        if in_perms:
            if line.strip().startswith("android.") or line.strip().startswith("com."):
                perms.append(line.strip())
            elif line.strip() == "" or not line.startswith(" "):
                in_perms = False
    info["permissions"] = perms

    # App size
    stdout3, _, _ = _run(["-s", target, "shell", "du", "-sh", f"/data/app/{package}*"], timeout=10)
    info["size"] = stdout3.strip() if stdout3 else "Unknown"

    return info, "OK"


def install_apk(device_manager, apk_path, serial=None):
    """Install an APK file"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    if not os.path.exists(apk_path):
        return False, f"File not found: {apk_path}"

    print(f"[*] Installing {os.path.basename(apk_path)}...")
    stdout, stderr, rc = _run(["-s", target, "install", "-r", "-d", apk_path], timeout=120)
    log_command(f"install {apk_path}", stdout)
    if "Success" in stdout:
        return True, "Installation successful"
    return False, stdout or stderr


def install_multiple(device_manager, apk_dir, serial=None):
    """Install all APKs from a directory"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    if not os.path.isdir(apk_dir):
        return False, f"Directory not found: {apk_dir}"

    apks = [f for f in os.listdir(apk_dir) if f.endswith(".apk")]
    if not apks:
        return False, "No APK files found"

    results = []
    for apk in apks:
        path = os.path.join(apk_dir, apk)
        ok, msg = install_apk(device_manager, path, serial)
        results.append({"file": apk, "success": ok, "message": msg})
    return results, f"Installed {sum(1 for r in results if r['success'])}/{len(results)}"


def uninstall_app(device_manager, package, serial=None):
    """Uninstall an app"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run(["-s", target, "uninstall", package], timeout=30)
    log_command(f"uninstall {package}", stdout)
    if "Success" in stdout:
        return True, f"{package} uninstalled"
    return False, stdout or stderr


def force_stop(device_manager, package, serial=None):
    """Force stop an app"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"am force-stop {package}", device=target)
    return rc == 0, f"Force stopped {package}"


def start_app(device_manager, package, serial=None):
    """Start/launch an app"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    # Get launch activity
    stdout, _, _ = _run_shell(
        f"cmd package resolve-activity --brief {package}", device=target
    )
    activity = stdout.strip().split("\n")[-1] if stdout.strip() else None
    if activity and "/" in activity:
        stdout, stderr, rc = _run_shell(f"am start -n {activity}", device=target)
    else:
        stdout, stderr, rc = _run_shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1", device=target)
    return rc == 0, f"Launched {package}"


def clear_app_data(device_manager, package, serial=None):
    """Clear app data/cache"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"pm clear {package}", device=target)
    if "Success" in stdout:
        return True, f"Data cleared for {package}"
    return False, stdout or stderr


def freeze_app(device_manager, package, serial=None):
    """Disable/freeze an app"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"pm disable {package}", device=target)
    return rc == 0, f"Frozen {package}"


def unfreeze_app(device_manager, package, serial=None):
    """Enable/unfreeze an app"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"pm enable {package}", device=target)
    return rc == 0, f"Unfrozen {package}"


def get_app_permissions(device_manager, package, serial=None):
    """Get runtime permissions for an app"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run(["-s", target, "shell", "dumpsys", "package", package], timeout=15)
    perms = []
    in_runtime = False
    in_declared = False
    for line in stdout.splitlines():
        line_s = line.strip()
        if "runtime permissions:" in line_s:
            in_runtime = True
            in_declared = False
            continue
        if "declared permissions:" in line_s:
            in_declared = True
            in_runtime = False
            continue
        if in_runtime or in_declared:
            if line_s.startswith("android.") or line_s.startswith("com.") or line_s.startswith("android:"):
                perms.append(line_s)
            elif line_s == "" or (not line.startswith(" ") and ":" not in line_s):
                in_runtime = False
                in_declared = False
    return perms, "OK"


def extract_apk(device_manager, package, output_dir=".", serial=None):
    """Extract APK from device to PC"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    # Get APK path
    stdout, _, _ = _run_shell(f"pm path {package}", device=target)
    if not stdout:
        return False, f"Cannot find APK path for {package}"

    apk_path = stdout.strip().replace("package:", "")
    output_file = os.path.join(output_dir, f"{package}.apk")

    stdout, stderr, rc = _run(["-s", target, "pull", apk_path, output_file], timeout=60)
    if rc == 0:
        return True, f"APK saved to {output_file}"
    return False, stderr


def get_running_apps(device_manager, serial=None):
    """Get currently running apps/processes"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("ps -A -o PID,USER,NAME", device=target)
    return stdout, "OK"


def get_top_activity(device_manager, serial=None):
    """Get currently foreground activity"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("dumpsys activity activities | grep mResumedActivity", device=target)
    if not stdout:
        stdout, _, _ = _run_shell("dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'", device=target)
    return stdout.strip(), "OK"
