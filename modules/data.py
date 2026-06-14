"""
MEGASUS Module: DATA - Data Extraction
Contacts, SMS, call logs, clipboard, media metadata
"""
from core.engine import DeviceManager, ADB, _run_shell, _run, log_command
import json
import os

MODULE_NAME = "Data Extraction"
MODULE_ICON = "📋"


def get_contacts(device_manager, output_file=None, serial=None):
    """Extract contacts from device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Method 1: content query
    stdout, _, rc = _run_shell(
        "content query --uri content://com.android.contacts/data "
        "--projection display_name:number:contact_id",
        device=target, timeout=15
    )

    contacts = []
    if stdout:
        for line in stdout.splitlines():
            if "Row:" in line:
                # Parse: Row: 0 display_name=John, number=123, contact_id=1
                parts = line.split("Row:")[1].strip()
                contact = {}
                for item in parts.split(","):
                    item = item.strip()
                    if "=" in item:
                        k, v = item.split("=", 1)
                        contact[k.strip()] = v.strip()
                if contact:
                    contacts.append(contact)

    if not contacts:
        # Method 2: via contacts provider
        stdout2, _, _ = _run_shell(
            "content query --uri content://contacts/phones/ --projection display_name:number",
            device=target, timeout=15
        )
        if stdout2:
            for line in stdout2.splitlines():
                if "Row:" in line:
                    parts = line.split("Row:")[1].strip()
                    contact = {}
                    for item in parts.split(","):
                        item = item.strip()
                        if "=" in item:
                            k, v = item.split("=", 1)
                            contact[k.strip()] = v.strip()
                    if contact:
                        contacts.append(contact)

    if output_file and contacts:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)

    log_command("get_contacts", f"Found {len(contacts)} contacts")
    return contacts, f"Found {len(contacts)} contacts"


def get_sms(device_manager, output_file=None, serial=None):
    """Extract SMS messages"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "content query --uri content://sms/ "
        "--projection _id:address:body:date:type:read:thread_id "
        "--sort 'date DESC' "
        "--limit 500",
        device=target, timeout=15
    )

    messages = []
    if stdout:
        for line in stdout.splitlines():
            if "Row:" in line:
                parts = line.split("Row:")[1].strip()
                msg = {}
                for item in parts.split(","):
                    item = item.strip()
                    if "=" in item:
                        k, v = item.split("=", 1)
                        msg[k.strip()] = v.strip()
                if msg:
                    messages.append(msg)

    if output_file and messages:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

    log_command("get_sms", f"Found {len(messages)} messages")
    return messages, f"Found {len(messages)} SMS messages"


def get_call_logs(device_manager, output_file=None, serial=None):
    """Extract call logs"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "content query --uri content://call_log/calls "
        "projection _id:name:number:date:type:duration",
        device=target, timeout=15
    )

    calls = []
    if stdout:
        for line in stdout.splitlines():
            if "Row:" in line:
                parts = line.split("Row:")[1].strip()
                call = {}
                for item in parts.split(","):
                    item = item.strip()
                    if "=" in item:
                        k, v = item.split("=", 1)
                        call[k.strip()] = v.strip()
                if call:
                    calls.append(call)

    # Ensure correct projection
    stdout2, _, _ = _run_shell(
        "content query --uri content://call_log/calls "
        "--projection _id:number:name:date:type:duration:presentation",
        device=target, timeout=15
    )
    if stdout2:
        calls = []
        for line in stdout2.splitlines():
            if "Row:" in line:
                parts = line.split("Row:")[1].strip()
                call = {}
                for item in parts.split(","):
                    item = item.strip()
                    if "=" in item:
                        k, v = item.split("=", 1)
                        call[k.strip()] = v.strip()
                if call:
                    calls.append(call)

    if output_file and calls:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(calls, f, indent=2, ensure_ascii=False)

    log_command("get_call_logs", f"Found {len(calls)} calls")
    return calls, f"Found {len(calls)} call log entries"


def get_clipboard(device_manager, serial=None):
    """Read clipboard content (Android 10+ needs service call)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Try service call for clipboard
    stdout, _, _ = _run_shell(
        "service call clipboard 2", device=target
    )
    if not stdout:
        # Alternative: input command
        stdout, _, _ = _run_shell(
            "am broadcast -a ClipboardManager.TEXT -e text ''", device=target
        )
    return stdout, "OK (may need root for full clipboard access)"


def set_clipboard(device_manager, text, serial=None):
    """Set clipboard content"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    # Use am broadcast to set clipboard (limited but works without root)
    escaped = text.replace(" ", "%s").replace("'", "\\'")
    stdout, stderr, rc = _run_shell(
        f"am broadcast -a ClipboardManager.SET -e text '{escaped}'", device=target
    )
    return rc == 0, "Clipboard set (best effort, may need root)"


def get_media_files(device_manager, media_type="all", serial=None):
    """List photos, videos, audio on device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    queries = {
        "photos": "/sdcard/DCIM /sdcard/Pictures",
        "videos": "/sdcard/DCIM /sdcard/Movies /sdcard/Video",
        "audio": "/sdcard/Music /sdcard/Audio /sdcard/Podcasts",
        "downloads": "/sdcard/Download /sdcard/Downloads",
        "all": "/sdcard/DCIM /sdcard/Pictures /sdcard/Movies /sdcard/Music /sdcard/Download",
    }

    paths = queries.get(media_type, queries["all"])
    all_files = []
    for path in paths.split():
        stdout, _, _ = _run_shell(
            f"find '{path}' -type f \\( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' -o "
            f"-name '*.mp4' -o -name '*.mp3' -o -name '*.wav' -o -name '*.gif' \\) 2>/dev/null | head -200",
            device=target, timeout=20
        )
        for line in stdout.splitlines():
            line = line.strip()
            if line:
                all_files.append(line)

    return all_files, f"Found {len(all_files)} media files"


def send_sms(device_manager, phone_number, message, serial=None):
    """Send SMS via intent (opens messaging app with pre-filled data)"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(
        f"am start -a android.intent.action.SENDTO -d sms:{phone_number} "
        f"--es sms_body '{message}' --ez exit_on_sent true",
        device=target
    )
    return rc == 0, f"SMS intent sent to {phone_number}"


def make_call(device_manager, phone_number, serial=None):
    """Open dialer with number"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(
        f"am start -a android.intent.action.CALL -d tel:{phone_number}",
        device=target
    )
    return rc == 0, f"Calling {phone_number}"


def get_notifications(device_manager, serial=None):
    """Get active notifications via notification listener (if available)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # dumpsys notification
    stdout, _, _ = _run_shell(
        "dumpsys notification --noredact 2>/dev/null | head -100",
        device=target, timeout=10
    )
    return stdout, "OK"


def get_accounts(device_manager, serial=None):
    """List registered accounts on device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, _, _ = _run_shell(
        "dumpsys account | grep -A2 'Account {' | head -100",
        device=target, timeout=10
    )
    return stdout, "OK"


def get_wifi_passwords(device_manager, serial=None):
    """Get saved WiFi passwords (needs root on Android 10+)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Try wpa_supplicant (older Android)
    stdout, _, _ = _run_shell(
        "cat /data/misc/wifi/WifiConfigStore.xml 2>/dev/null || "
        "cat /data/misc/apexdata/com.android.wifi/WifiConfigStore.xml 2>/dev/null || "
        "cat /data/vendor/wifi/wpa/wpa_supplicant.conf 2>/dev/null",
        device=target, timeout=10
    )
    if not stdout:
        return None, "WiFi passwords require root access on Android 10+. Try using a root shell."
    return stdout, "OK (root required)"


def get_browser_history(device_manager, serial=None):
    """Get Chrome browser history (pull DB and parse)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Chrome history path
    remote_path = "/data/data/com.android.chrome/app_chrome/Default/History"
    local_path = "logs/chrome_history_temp.db"

    stdout, stderr, rc = _run(["-s", target, "pull", remote_path, local_path], timeout=30)
    if rc != 0:
        return None, f"Cannot access Chrome history: {stderr}\nMay need backup API or root."

    try:
        import sqlite3
        conn = sqlite3.connect(local_path)
        cursor = conn.execute(
            "SELECT url, title, last_visit_time, visit_count FROM urls ORDER BY last_visit_time DESC LIMIT 100"
        )
        rows = cursor.fetchall()
        conn.close()
        os.remove(local_path)
        return [{"url": r[0], "title": r[1], "visits": r[3]} for r in rows], f"Found {len(rows)} history entries"
    except Exception as e:
        return None, f"Error parsing history DB: {e}"
