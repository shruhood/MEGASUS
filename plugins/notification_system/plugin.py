"""MEGASUS Notification System Plugin — Monitor, read, dismiss, reply notifications."""
from __future__ import annotations
import os
import time
import threading
import logging
from datetime import datetime
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("notification_system")


class NotificationSystemPlugin(Plugin):
    """Monitor and manage device notifications."""

    name = "notification_system"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Monitor, read, dismiss, and reply to device notifications"

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._notifications: list[dict] = []

    def get_notifications(self) -> list[dict]:
        """Get current notifications from device."""
        out, err, rc = self.adb_shell("dumpsys notification --noredact")
        if rc != 0 or not out:
            return []
        notifications = []
        current = {}
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("NotificationRecord("):
                if current:
                    notifications.append(current)
                current = {"raw": line}
            elif "pkg=" in line:
                for part in line.split():
                    if part.startswith("pkg="):
                        current["package"] = part.split("=")[1]
            elif "text=" in line:
                current["text"] = line.split("text=")[-1].strip()
            elif line == "}":
                if current:
                    notifications.append(current)
                    current = {}
        if current:
            notifications.append(current)
        self._notifications = notifications
        return notifications

    def dismiss_all(self) -> bool:
        """Dismiss all notifications."""
        out, err, rc = self.adb_shell("service call notification 1")
        return rc == 0

    def dismiss_key(self, key: str) -> bool:
        """Dismiss a specific notification by key."""
        out, err, rc = self.adb_shell(f"service call notification 2 s16 {key}")
        return rc == 0

    def reply_notification(self, key: str, text: str) -> bool:
        """Reply to a notification (requires Android 7+)."""
        out, err, rc = self.adb_shell(
            f"am broadcast -a android.intent.action.TEXT_REPLY "
            f"--es reply '{text}' --es notification_key '{key}'"
        )
        return rc == 0

    def monitor_loop(self, duration: int = 30, callback=None) -> list[dict]:
        """Monitor notifications for a duration, collecting new ones."""
        seen = set()
        collected = []
        start = time.time()
        while time.time() - start < duration:
            notifs = self.get_notifications()
            for n in notifs:
                key = n.get("package", "") + n.get("text", "")[:30]
                if key not in seen:
                    seen.add(key)
                    n["timestamp"] = datetime.now().isoformat()
                    collected.append(n)
                    if callback:
                        callback(n)
            time.sleep(2)
        return collected

    def run(self) -> None:
        """Interactive notification menu."""
        print("\n  === NOTIFICATION SYSTEM ===")
        print("  1. List current notifications")
        print("  2. Dismiss all")
        print("  3. Monitor notifications (30s)")
        print("  4. Reply to notification")
        print("  0. Back")

        choice = input("\n  Choice: ").strip()
        if choice == "0":
            return
        elif choice == "1":
            notifs = self.get_notifications()
            if not notifs:
                print("  No notifications")
            for n in notifs:
                pkg = n.get("package", "?")
                text = n.get("text", "")[:60]
                print(f"  [{pkg}] {text}")
        elif choice == "2":
            if self.dismiss_all():
                print("  All dismissed")
            else:
                print("  Failed")
        elif choice == "3":
            dur = int(input("  Duration sec [30]: ").strip() or "30")
            print(f"  Monitoring for {dur}s...")
            collected = self.monitor_loop(dur)
            print(f"  Found {len(collected)} new notifications")
            for n in collected:
                print(f"    [{n.get('package', '?')}] {n.get('text', '')[:60]}")
        elif choice == "4":
            key = input("  Notification key: ").strip()
            text = input("  Reply text: ").strip()
            if self.reply_notification(key, text):
                print("  Reply sent")
            else:
                print("  Failed")

    def shutdown(self) -> None:
        self.log("Shutting down Notification System plugin")


def register() -> dict[str, Any]:
    plugin = NotificationSystemPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
