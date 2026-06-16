"""MEGASUS Task Scheduler Plugin — Schedule ADB commands with cron-like support."""
from __future__ import annotations
import os
import json
import time
import threading
import logging
from datetime import datetime
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("task_scheduler")

SCHEDULE_FILE = os.path.join(os.path.dirname(__file__), "schedules.json")


class TaskSchedulerPlugin(Plugin):
    """Schedule recurring or one-time ADB shell commands."""

    name = "task_scheduler"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Schedule ADB commands with cron-like support"

    def __init__(self) -> None:
        super().__init__()
        self._schedules = self._load_schedules()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _load_schedules(self) -> list[dict]:
        if os.path.exists(SCHEDULE_FILE):
            try:
                with open(SCHEDULE_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_schedules(self) -> None:
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(self._schedules, f, indent=2)

    def add_schedule(self, name: str, command: str, interval_sec: int,
                     recurring: bool = True, max_runs: int = 0) -> None:
        """Add a new scheduled task."""
        task = {
            "id": str(int(time.time() * 1000)),
            "name": name,
            "command": command,
            "interval_sec": interval_sec,
            "recurring": recurring,
            "max_runs": max_runs,
            "run_count": 0,
            "last_run": None,
            "enabled": True,
            "created": datetime.now().isoformat(),
        }
        self._schedules.append(task)
        self._save_schedules()
        self.log(f"Scheduled: {name} ({command}) every {interval_sec}s")

    def remove_schedule(self, task_id: str) -> bool:
        """Remove a scheduled task by ID."""
        before = len(self._schedules)
        self._schedules = [s for s in self._schedules if s.get("id") != task_id]
        if len(self._schedules) < before:
            self._save_schedules()
            return True
        return False

    def list_schedules(self) -> list[dict]:
        return list(self._schedules)

    def toggle_schedule(self, task_id: str) -> bool:
        for s in self._schedules:
            if s.get("id") == task_id:
                s["enabled"] = not s.get("enabled", True)
                self._save_schedules()
                return True
        return False

    def _execute(self, task: dict) -> None:
        """Execute a single scheduled task."""
        cmd = task.get("command", "")
        if not cmd:
            return
        self.log(f"Running: {task['name']} -> {cmd}")
        out, err, rc = self.adb_shell(cmd)
        task["last_run"] = datetime.now().isoformat()
        task["last_rc"] = rc
        task["run_count"] = task.get("run_count", 0) + 1
        if not task.get("recurring", False):
            task["enabled"] = False
        self._save_schedules()

    def _loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            now = time.time()
            for task in self._schedules:
                if not task.get("enabled", True):
                    continue
                max_runs = task.get("max_runs", 0)
                if max_runs > 0 and task.get("run_count", 0) >= max_runs:
                    task["enabled"] = False
                    continue
                interval = task.get("interval_sec", 60)
                last_run = task.get("_last_exec", 0)
                if now - last_run >= interval:
                    self._execute(task)
                    task["_last_exec"] = now
            self._save_schedules()
            time.sleep(1)

    def run(self) -> None:
        """Interactive scheduler menu."""
        print("\n  === TASK SCHEDULER ===")
        print("  1. List schedules")
        print("  2. Add schedule")
        print("  3. Remove schedule")
        print("  4. Toggle enable/disable")
        print("  5. Run task now")
        print("  0. Back")

        choice = input("\n  Choice: ").strip()
        if choice == "0":
            return
        elif choice == "1":
            if not self._schedules:
                print("  No schedules")
            for s in self._schedules:
                status = "ON" if s.get("enabled", True) else "OFF"
                print(f"  [{status}] {s['name']}: {s['command']} "
                      f"(every {s['interval_sec']}s, runs: {s.get('run_count', 0)})")
        elif choice == "2":
            name = input("  Name: ").strip()
            cmd = input("  ADB shell command: ").strip()
            interval = int(input("  Interval seconds [60]: ").strip() or "60")
            recurring = input("  Recurring? (y/n) [y]: ").strip().lower() != "n"
            self.add_schedule(name, cmd, interval, recurring)
        elif choice == "3":
            task_id = input("  Task ID: ").strip()
            if self.remove_schedule(task_id):
                print("  Removed")
            else:
                print("  Not found")
        elif choice == "4":
            task_id = input("  Task ID: ").strip()
            if self.toggle_schedule(task_id):
                print("  Toggled")
            else:
                print("  Not found")
        elif choice == "5":
            task_id = input("  Task ID: ").strip()
            for s in self._schedules:
                if s.get("id") == task_id:
                    self._execute(s)
                    print(f"  Executed: {s['name']}")
                    break

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            self.log("Scheduler already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.log("Scheduler started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self.log("Scheduler stopped")

    def shutdown(self) -> None:
        self.log("Shutting down Task Scheduler")
        self.stop()
        self._save_schedules()


def register() -> dict[str, Any]:
    plugin = TaskSchedulerPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
