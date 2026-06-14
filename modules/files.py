"""
MEGASUS Module: FILES - File Operations & Filesystem Browser
Push, pull, browse, delete, search files on device
"""
from core.engine import DeviceManager, ADB, _run_shell, human_size, _run, log_command
import os

MODULE_NAME = "File Manager"
MODULE_ICON = "📂"


def browse(device_manager, path="/sdcard", serial=None):
    """Browse a directory on device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, stderr, rc = _run_shell(f"ls -la '{path}'", device=target)
    if rc != 0:
        return None, stderr or f"Cannot access {path}"

    entries = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("total"):
            continue
        parts = line.split(None, 8)
        if len(parts) >= 9:
            entries.append({
                "permissions": parts[0],
                "owner": parts[2],
                "group": parts[3],
                "size": parts[4],
                "date": " ".join(parts[5:8]),
                "name": parts[8],
                "is_dir": parts[0].startswith("d"),
            })
    return entries, path


def push_file(device_manager, local_path, remote_path, serial=None):
    """Push file from PC to device"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    if not os.path.exists(local_path):
        return False, f"Local file not found: {local_path}"

    size = os.path.getsize(local_path)
    print(f"[*] Pushing {os.path.basename(local_path)} ({human_size(size)})...")
    stdout, stderr, rc = _run(["-s", target, "push", local_path, remote_path], timeout=120)
    log_command(f"push {local_path} {remote_path}", stdout[:100])
    if rc == 0:
        return True, f"Pushed to {remote_path}"
    return False, stderr


def pull_file(device_manager, remote_path, local_path=None, serial=None):
    """Pull file from device to PC"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    if local_path is None:
        local_path = os.path.basename(remote_path)

    print(f"[*] Pulling {remote_path}...")
    stdout, stderr, rc = _run(["-s", target, "pull", remote_path, local_path], timeout=120)
    log_command(f"pull {remote_path} {local_path}", stdout[:100])
    if rc == 0:
        return True, f"Saved to {os.path.abspath(local_path)}"
    return False, stderr


def pull_directory(device_manager, remote_dir, local_dir=None, serial=None):
    """Pull entire directory from device"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"

    if local_dir is None:
        local_dir = os.path.basename(remote_dir.rstrip("/"))

    os.makedirs(local_dir, exist_ok=True)
    print(f"[*] Pulling directory {remote_dir}...")
    stdout, stderr, rc = _run(["-s", target, "pull", remote_dir, local_dir], timeout=300)
    if rc == 0:
        return True, f"Directory saved to {os.path.abspath(local_dir)}"
    return False, stderr


def delete_file(device_manager, remote_path, serial=None):
    """Delete file/directory on device"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"rm -rf '{remote_path}'", device=target)
    log_command(f"delete {remote_path}", user="admin")
    return rc == 0, f"Deleted {remote_path}"


def create_directory(device_manager, remote_path, serial=None):
    """Create directory on device"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(f"mkdir -p '{remote_path}'", device=target)
    return rc == 0, f"Created {remote_path}"


def search_files(device_manager, name_pattern, search_path="/sdcard", serial=None):
    """Search for files by name pattern"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell(
        f"find '{search_path}' -name '{name_pattern}' 2>/dev/null", device=target, timeout=30
    )
    results = [l.strip() for l in stdout.splitlines() if l.strip()]
    return results, f"Found {len(results)} matches"


def get_file_info(device_manager, remote_path, serial=None):
    """Get file info (size, permissions, etc.)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell(f"ls -la '{remote_path}' && stat '{remote_path}' 2>/dev/null", device=target)
    return stdout, "OK"


def cat_file(device_manager, remote_path, serial=None):
    """Read/cat a text file from device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, stderr, rc = _run_shell(f"cat '{remote_path}'", device=target)
    if rc == 0:
        return stdout, "OK"
    return None, stderr


def push_and_install(device_manager, apk_path, serial=None):
    """Push APK to device and install it"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    if not os.path.exists(apk_path):
        return False, f"File not found: {apk_path}"

    # Push to temp
    remote_tmp = f"/sdcard/temp_install_{os.path.basename(apk_path)}"
    ok, msg = push_file(device_manager, apk_path, remote_tmp, serial)
    if not ok:
        return False, msg

    # Install
    stdout, stderr, rc = _run(["-s", target, "shell", "pm", "install", "-r", remote_tmp], timeout=60)
    # Clean up
    _run_shell(f"rm -f '{remote_tmp}'", device=target)

    if "Success" in stdout:
        return True, "Installed successfully"
    return False, stdout or stderr


def get_disk_usage(device_manager, path="/", serial=None):
    """Get disk usage summary"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell(f"df -h '{path}'", device=target)
    return stdout, "OK"
