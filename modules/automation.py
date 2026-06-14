"""
MEGASUS Module: AUTOMATION - Script Runner, Macros, Bulk Commands
Run custom ADB scripts, batch operations, scheduled tasks
"""
from core.engine import DeviceManager, ADB, _run_shell, _run, log_command
import os
import time
import json

MODULE_NAME = "Automation"
MODULE_ICON = "⚡"


def run_adb_shell_command(device_manager, command, serial=None):
    """Run any ADB shell command"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    log_command(f"shell: {command[:50]}", user="admin")
    stdout, stderr, rc = _run_shell(command, device=target, timeout=30)
    return {"stdout": stdout, "stderr": stderr, "rc": rc}, "OK"


def batch_command(device_manager, commands, delay=1, serial=None):
    """Run multiple commands in sequence"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    results = []
    for i, cmd in enumerate(commands):
        print(f"[*] [{i+1}/{len(commands)}] {cmd}")
        stdout, stderr, rc = _run_shell(cmd, device=target, timeout=30)
        results.append({"command": cmd, "stdout": stdout, "stderr": stderr, "rc": rc})
        if delay > 0 and i < len(commands) - 1:
            time.sleep(delay)
    return results, f"Executed {len(commands)} commands"


def execute_script_file(device_manager, script_path, serial=None, variables=None):
    """
    Execute a script file containing shell commands.
    Lines starting with # are comments.
    Variables: { "VAR": "value" } for template substitution.
    """
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    if not os.path.exists(script_path):
        return None, f"Script not found: {script_path}"

    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    results = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Variable substitution
        if variables:
            for var, val in variables.items():
                line = line.replace(f"${{{var}}}", val).replace(f"${var}", val)

        print(f"[*] Line {i+1}: {line}")
        stdout, stderr, rc = _run_shell(line, device=target, timeout=60)
        results.append({"line": i+1, "command": line, "rc": rc, "output": stdout})

    return results, f"Executed {len(results)} commands from script"


def create_macro(name, commands):
    """Save a macro for later use"""
    macros_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
    os.makedirs(macros_dir, exist_ok=True)

    macro_file = os.path.join(macros_dir, f"macro_{name}.json")
    macro = {"name": name, "commands": commands, "created": time.strftime("%Y-%m-%d %H:%M:%S")}

    with open(macro_file, "w") as f:
        json.dump(macro, f, indent=2)

    return True, f"Macro '{name}' saved ({len(commands)} commands)"


def load_macro(name):
    """Load a saved macro"""
    macros_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
    macro_file = os.path.join(macros_dir, f"macro_{name}.json")

    if not os.path.exists(macro_file):
        return None, f"Macro '{name}' not found"

    with open(macro_file, "r") as f:
        return json.load(f), "OK"


def list_macros():
    """List all saved macros"""
    macros_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
    if not os.path.isdir(macros_dir):
        return []

    macros = []
    for f in os.listdir(macros_dir):
        if f.startswith("macro_") and f.endswith(".json"):
            fpath = os.path.join(macros_dir, f)
            try:
                with open(fpath) as fh:
                    data = json.load(fh)
                macros.append({"name": data.get("name", f), "commands": len(data.get("commands", []))})
            except Exception:
                pass
    return macros


def run_macro(device_manager, name, serial=None):
    """Execute a saved macro"""
    macro, msg = load_macro(name)
    if not macro:
        return None, msg
    commands = macro.get("commands", [])
    return batch_command(device_manager, commands, delay=1, serial=serial)


def setup_keylogger_accessibility(device_manager, serial=None):
    """
    Guide for setting up accessibility-based key logging.
    This requires installing a keylogger APK and enabling accessibility service.
    """
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    guide = """
    === KEYLOGGER SETUP GUIDE ===
    
    Method 1: Accessibility Service (No Root Required)
    1. Install a keylogger APK (e.g., "Keylogger" from trusted source)
    2. Go to Settings > Accessibility > Installed Services
    3. Enable the keylogger service
    4. Grant all requested permissions
    
    Method 2: ADB Input Monitor (Limited, No Extra App)
    - Can monitor input events via getevent
    - Run: adb shell getevent -lt /dev/input/eventX
    - Need to find correct event device:
      adb shell getevent -lp | grep -i keyboard
    
    Method 3: logcat monitoring
    - Some keyboards log to logcat
    - Filter: adb logcat | grep -i key
    """
    return guide, "Keylogger setup guide"


def get_input_events(device_manager, serial=None):
    """Monitor input events (keyboard/touch) via getevent"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Find input devices
    stdout, _, _ = _run_shell("getevent -lp 2>/dev/null | grep -B5 -i 'keyboard\\|touch' | head -30", device=target, timeout=10)
    return stdout.strip(), "OK"


def simulate_keyevent(device_manager, keycode, serial=None):
    """Simulate a key press"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"input keyevent {keycode}", device=target)
    return rc == 0, f"Keyevent {keycode} sent"


def launch_url(device_manager, url, serial=None):
    """Open URL in browser"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"am start -a android.intent.action.VIEW -d '{url}'", device=target)
    return rc == 0, f"Opened {url}"


def set_alarm(device_manager, message, seconds_from_now=10, serial=None):
    """Set a device alarm/notification after delay"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    _run_shell(
        f"am broadcast -a android.intent.action.SET_ALARM "
        f"--es android.intent.extra.alarm.MESSAGE '{message}' "
        f"--ei android.intent.extra.alarm.MINUTES {seconds_from_now}",
        device=target
    )
    return True, f"Alarm set in ~{seconds_from_now} for '{message}'"


def bulk_install_from_list(device_manager, package_list, serial=None):
    """
    Uninstall a list of packages.
    package_list: list of package names
    """
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    results = []
    for pkg in package_list:
        stdout, stderr, rc = _run(["-s", target, "uninstall", pkg], timeout=30)
        results.append({
            "package": pkg,
            "success": "Success" in stdout,
            "output": stdout or stderr,
        })
    return results, f"Processed {len(results)} packages"


def create_backup(device_manager, output_file="backup.ab", serial=None):
    """
    Create ADB backup (deprecated in Android 12+ but still useful for older devices)
    """
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    print("[*] Creating backup... Phone will show backup confirmation UI")
    print("[*] Set a password on the phone backup screen if you want encryption")
    stdout, stderr, rc = _run(
        ["-s", target, "backup", "-apk", "-shared", "-all", "-f", output_file],
        timeout=600
    )
    return rc == 0, f"Backup saved to {output_file}" if rc == 0 else stderr


def restore_backup(device_manager, backup_file, serial=None):
    """Restore from ADB backup"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    if not os.path.exists(backup_file):
        return False, f"Backup file not found: {backup_file}"

    print("[*] Restoring backup... Phone will show restore confirmation UI")
    stdout, stderr, rc = _run(["-s", target, "restore", backup_file], timeout=600)
    return rc == 0, "Restore complete" if rc == 0 else stderr
