"""
MEGASUS Module: SECURITY - Security Audit & Analysis
Root detection, permissions audit, vulnerability scan, encryption check
"""
from core.engine import DeviceManager, ADB, _run_shell, _run, log_command
import re

MODULE_NAME = "Security Audit"
MODULE_ICON = "🔐"


def full_audit(device_manager, serial=None):
    """Run comprehensive security audit"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    results = {}

    # 1. Root Detection
    results["root"] = check_root(device_manager, serial)

    # 2. Encryption Status
    results["encryption"] = check_encryption(device_manager, serial)

    # 3. SELinux
    stdout, _, _ = _run_shell("getenforce", device=target)
    results["selinux"] = stdout.strip()

    # 4. Build security patch level
    stdout, _, _ = _run_shell("getprop ro.build.version.security_patch", device=target)
    results["security_patch"] = stdout.strip()

    # 5. Bootloader locked
    stdout, _, _ = _run_shell("getprop ro.boot.verifiedbootstate", device=target)
    results["bootloader_locked"] = stdout.strip() == "green" if stdout.strip() else "Unknown"

    # 6. Verified Boot
    stdout, _, _ = _run_shell("getprop ro.boot.vbmeta.device_state", device=target)
    results["vbmeta_state"] = stdout.strip() or "Unknown"

    # 7. Debuggable
    stdout, _, _ = _run_shell("getprop ro.debuggable", device=target)
    results["debuggable"] = stdout.strip() == "1"

    # 8. Secure boot
    stdout, _, _ = _run_shell("getprop ro.secure", device=target)
    results["secure"] = stdout.strip() == "1"

    # 9. Build tags
    stdout, _, _ = _run_shell("getprop ro.build.tags", device=target)
    results["build_tags"] = stdout.strip()
    results["test_keys"] = "test-keys" in stdout

    # 10. ADB over network
    stdout, _, _ = _run_shell("getprop persist.adb.tcp.port", device=target)
    results["adb_over_network"] = stdout.strip() != "" and stdout.strip() != "-1"

    # 11. Unknown sources
    stdout, _, _ = _run_shell("settings get secure install_non_market_apps", device=target)
    results["unknown_sources"] = stdout.strip() == "1"

    # 12. Password/PIN set
    stdout, _, _ = _run_shell("settings get secure lockscreen.password_type", device=target)
    results["password_set"] = stdout.strip() != "" and stdout.strip() != "0"

    # 13. Find dangerous permissions
    results["dangerous_apps"] = get_dangerous_apps(device_manager, serial)

    return results, "Audit complete"


def check_root(device_manager, serial=None):
    """Multi-method root detection"""
    target = serial or device_manager.get_active()
    if not target:
        return {"rooted": False, "reason": "No device"}

    checks = {}

    # Check 1: su binary
    su_paths = [
        "/system/bin/su", "/system/xbin/su", "/sbin/su",
        "/system/su", "/system/bin/.ext/.su", "/system/usr/we-need-root/su",
        "/data/local/xbin/su", "/data/local/bin/su", "/data/local/su",
        "/su/bin/su", "/magisk/.core/bin/su",
    ]
    su_found = []
    for path in su_paths:
        stdout, _, rc = _run_shell(f"ls -la '{path}' 2>/dev/null", device=target)
        if rc == 0 and stdout.strip():
            su_found.append(path)
    checks["su_binary"] = {"found": len(su_found) > 0, "paths": su_found}

    # Check 2: which su
    stdout, _, _ = _run_shell("which su 2>/dev/null", device=target)
    checks["which_su"] = stdout.strip() or "not found"

    # Check 3: Magisk
    stdout, _, _ = _run_shell("ls -la /sbin/.magisk 2>/dev/null || ls -la /data/adb/magisk 2>/dev/null", device=target)
    checks["magisk"] = stdout.strip() != ""

    # Check 4: Build tags
    stdout, _, _ = _run_shell("getprop ro.build.tags", device=target)
    checks["test_keys"] = "test-keys" in stdout

    # Check 5: rw system
    stdout, _, _ = _run_shell("mount | grep -w /system 2>/dev/null | head -5", device=target)
    checks["rw_system"] = "rw," in stdout or "rw " in stdout

    # Check 6: Root management apps
    root_apps = ["com.topjohnwu.magisk", "eu.chainfire.supersu", "com.koushikdutta.superuser",
                 "com.noshufou.android.su", "com.thirdparty.superuser"]
    stdout, _, _ = _run_shell("pm list packages", device=target)
    found_root_apps = [a for a in root_apps if a in stdout]
    checks["root_apps"] = found_root_apps

    # Verdict
    rooted = any([
        len(su_found) > 0,
        checks["which_su"] != "not found",
        checks["magisk"],
        checks["test_keys"],
        len(found_root_apps) > 0,
    ])

    return {
        "rooted": rooted,
        "confidence": "HIGH" if len(su_found) > 0 or checks["magisk"] else ("MEDIUM" if rooted else "LOW"),
        "checks": checks,
    }


def get_dangerous_apps(device_manager, serial=None):
    """Find apps with dangerous permissions"""
    target = serial or device_manager.get_active()
    if not target:
        return None

    dangerous_perms = [
        "android.permission.READ_SMS", "android.permission.SEND_SMS",
        "android.permission.READ_CONTACTS", "android.permission.WRITE_CONTACTS",
        "android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.CAMERA", "android.permission.RECORD_AUDIO",
        "android.permission.READ_PHONE_STATE", "android.permission.CALL_PHONE",
        "android.permission.READ_CALL_LOG", "android.permission.WRITE_CALL_LOG",
        "android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.SYSTEM_ALERT_WINDOW", "android.permission.WRITE_SETTINGS",
        "android.permission.DEVICE_ADMIN", "android.permission.BIND_ACCESSIBILITY_SERVICE",
        "android.permission.REQUEST_INSTALL_PACKAGES",
    ]

    stdout, _, _ = _run_shell("pm list packages -3", device=target)
    third_party = [l.replace("package:", "").strip() for l in stdout.splitlines() if l.strip()]

    dangerous = []
    for pkg in third_party[:50]:  # limit for speed
        pkg_stdout, _, _ = _run_shell(f"dumpsys package {pkg} | grep 'permission\\.'", device=target)
        perms = []
        for perm in dangerous_perms:
            if perm in pkg_stdout:
                perms.append(perm)
        if perms:
            dangerous.append({"package": pkg, "dangerous_permissions": perms})

    return dangerous


def check_encryption(device_manager, serial=None):
    """Check device encryption status"""
    target = serial or device_manager.get_active()
    if not target:
        return None

    results = {}

    # vold decrypt
    stdout, _, _ = _run_shell("getprop ro.crypto.state", device=target)
    results["crypto_state"] = stdout.strip() or "unknown"

    # File-based encryption
    stdout, _, _ = _run_shell("getprop ro.crypto.type", device=target)
    results["crypto_type"] = stdout.strip() or "unknown"

    # FBE
    stdout, _, _ = _run_shell("getprop ro.crypto.fs_crypto_blkdev", device=target)
    results["fbe"] = stdout.strip() != ""

    results["encrypted"] = results["crypto_state"] == "encrypted"
    return results


def list_all_permissions(device_manager, serial=None):
    """List all permission groups on device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell("pm list permissions -g -f", device=target, timeout=15)
    return stdout, "OK"


def scan_open_ports(device_manager, serial=None):
    """Scan device's open ports via /proc/net"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell("cat /proc/net/tcp /proc/net/tcp6 2>/dev/null", device=target)
    listeners = []
    for line in stdout.splitlines():
        if "00000000:0000" in line or ":0000 " in line:
            continue
        parts = line.strip().split()
        if len(parts) >= 4 and parts[3] == "0A":  # LISTEN state
            # Parse hex port
            local = parts[1]
            if ":" in local:
                port_hex = local.split(":")[1]
                try:
                    port = int(port_hex, 16)
                    ip = local.split(":")[0]
                    listeners.append({"ip": ip, "port": port, "state": "LISTEN"})
                except ValueError:
                    pass

    return listeners, f"Found {len(listeners)} listening ports"


def check_debuggable_apps(device_manager, serial=None):
    """Find debuggable apps"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Get third-party packages
    stdout, _, _ = _run_shell("pm list packages -3", device=target)
    packages = [l.replace("package:", "").strip() for l in stdout.splitlines() if l.strip()]

    debuggable = []
    for pkg in packages[:30]:  # limit for speed
        pkg_stdout, _, _ = _run_shell(f"dumpsys package {pkg} 2>/dev/null | grep -i DEBUGGABLE", device=target)
        if pkg_stdout.strip():
            debuggable.append(pkg)

    return debuggable, f"Found {len(debuggable)} debuggable apps"


def get_selinux_status(device_manager, serial=None):
    """Get detailed SELinux status"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    results = {}
    stdout, _, _ = _run_shell("getenforce", device=target)
    results["mode"] = stdout.strip() or "unknown"

    stdout, _, _ = _run_shell("cat /sys/fs/selinux/policy 2>/dev/null | head -c 100", device=target)
    results["policy_loaded"] = stdout.strip() != ""

    stdout, _, _ = _run_shell("sestatus 2>/dev/null", device=target)
    results["sestatus"] = stdout or "sestatus not available"

    return results, "OK"


def check_vulnerability_patch_level(device_manager, threshold_days=90, serial=None):
    """Check if security patch is older than threshold"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    import datetime
    stdout, _, _ = _run_shell("getprop ro.build.version.security_patch", device=target)
    patch_str = stdout.strip()

    if not patch_str:
        return None, "Cannot determine patch level"

    try:
        patch_date = datetime.datetime.strptime(patch_str, "%Y-%m-%d")
        days_old = (datetime.datetime.now() - patch_date).days
        return {
            "patch_date": patch_str,
            "days_old": days_old,
            "outdated": days_old > threshold_days,
            "risk": "HIGH" if days_old > 365 else ("MEDIUM" if days_old > 90 else "LOW"),
        }, "OK"
    except ValueError:
        return None, f"Cannot parse patch date: {patch_str}"


def audit_apk_permissions(device_manager, serial=None):
    """Full dump of all app permissions (slow but thorough)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "dumpsys package | grep -A200 'Permissions:' | head -200",
        device=target, timeout=15
    )
    return stdout, "OK"


def check_frida(device_manager, serial=None):
    """Check if Frida server is running on device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Check for frida-server process
    stdout, _, _ = _run_shell("ps -A | grep -i frida", device=target)
    frida_running = stdout.strip() != ""

    # Check for frida agent files
    stdout2, _, _ = _run_shell("ls /data/local/tmp/frida* 2>/dev/null || echo 'not found'", device=target)

    return {
        "frida_running": frida_running,
        "frida_processes": stdout.strip() or "none",
        "frida_files": stdout2.strip() or "none",
    }, "OK"


def check_magisk(device_manager, serial=None):
    """Detailed Magisk detection"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    results = {}

    # Magisk app
    stdout, _, _ = _run_shell("pm list packages | grep -i magisk", device=target)
    results["magisk_app"] = stdout.strip() or "not found"

    # Magisk files
    magisk_paths = [
        "/sbin/.magisk", "/data/adb/magisk", "/data/adb/modules",
        ".magisk", "/cache/.disable_magisk",
    ]
    found = []
    for p in magisk_paths:
        s, _, rc = _run_shell(f"ls -la '{p}' 2>/dev/null", device=target)
        if rc == 0:
            found.append(p)
    results["magisk_files"] = found

    # MagiskHide / Zygisk
    stdout, _, _ = _run_shell("getprop persist.magisk.hide 2>/dev/null", device=target)
    results["magisk_hide"] = stdout.strip() or "not set"

    # Try magisk version
    stdout, _, _ = _run_shell("/data/adb/magisk/magisk -v 2>/dev/null || magisk -v 2>/dev/null", device=target)
    results["magisk_version"] = stdout.strip() or "unknown"

    results["detected"] = len(found) > 0 or results["magisk_app"] != "not found"

    return results, "OK"
