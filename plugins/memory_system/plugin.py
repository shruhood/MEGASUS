"""MEGASUS Memory System Plugin — Auto-save device state snapshots with diff."""
from __future__ import annotations
import os
import json
import time
import logging
from datetime import datetime
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("memory_system")
SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "snapshots")


class MemorySystemPlugin(Plugin):
    """Save and compare device state snapshots."""

    name = "memory_system"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Auto-save device state snapshots with diff comparison"

    def __init__(self) -> None:
        super().__init__()
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    def _ts(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def snapshot(self, name: str = "") -> str:
        """Capture full device state snapshot."""
        if not name:
            name = f"snap_{self._ts()}"
        snap = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "device": {},
            "battery": {},
            "network": {},
            "apps": [],
            "processes": [],
        }

        # Device info
        out, _, _ = self.adb_shell("getprop ro.product.model")
        snap["device"]["model"] = out.strip()
        out, _, _ = self.adb_shell("getprop ro.build.version.release")
        snap["device"]["android"] = out.strip()

        # Battery
        out, _, _ = self.adb_shell("dumpsys battery")
        for line in out.splitlines():
            if "level:" in line:
                snap["battery"]["level"] = int(line.split(":")[-1].strip())
            elif "status:" in line:
                snap["battery"]["status"] = line.split(":")[-1].strip()
            elif "temperature:" in line:
                snap["battery"]["temp"] = int(line.split(":")[-1].strip()) / 10.0

        # Network
        out, _, _ = self.adb_shell("ip route | head -1")
        snap["network"]["route"] = out.strip()
        out, _, _ = self.adb_shell("getprop dhcp.eth0.gateway")
        snap["network"]["gateway"] = out.strip()

        # Apps
        out, _, _ = self.adb_shell("pm list packages -3 | wc -l")
        snap["apps_count"] = int(out.strip()) if out.strip().isdigit() else 0

        # Processes
        out, _, _ = self.adb_shell("ps -A | wc -l")
        snap["processes_count"] = int(out.strip()) if out.strip().isdigit() else 0

        # Save
        path = os.path.join(SNAPSHOT_DIR, f"{name}.json")
        with open(path, "w") as f:
            json.dump(snap, f, indent=2)
        self.log(f"Snapshot saved: {path}")
        return path

    def list_snapshots(self) -> list[dict]:
        snaps = []
        for f in sorted(os.listdir(SNAPSHOT_DIR), reverse=True):
            if f.endswith(".json"):
                path = os.path.join(SNAPSHOT_DIR, f)
                with open(path) as fh:
                    data = json.load(fh)
                snaps.append({
                    "name": data.get("name", f),
                    "timestamp": data.get("timestamp", ""),
                    "path": path,
                })
        return snaps

    def compare(self, snap1_path: str, snap2_path: str) -> dict:
        """Compare two snapshots and return differences."""
        with open(snap1_path) as f:
            s1 = json.load(f)
        with open(snap2_path) as f:
            s2 = json.load(f)

        diffs = {}
        for key in set(list(s1.keys()) + list(s2.keys())):
            if key in ("name", "timestamp", "path"):
                continue
            v1 = s1.get(key)
            v2 = s2.get(key)
            if v1 != v2:
                diffs[key] = {"before": v1, "after": v2}
        return diffs

    def run(self) -> None:
        """Interactive snapshot menu."""
        print("\n  === MEMORY SYSTEM ===")
        print("  1. Take snapshot")
        print("  2. List snapshots")
        print("  3. Compare two snapshots")
        print("  4. View snapshot details")
        print("  0. Back")

        choice = input("\n  Choice: ").strip()
        if choice == "0":
            return
        elif choice == "1":
            name = input("  Name (Enter=auto): ").strip()
            p = self.snapshot(name or "")
            print(f"  Saved: {p}")
        elif choice == "2":
            snaps = self.list_snapshots()
            for i, s in enumerate(snaps):
                print(f"  {i+1}. {s['name']} — {s['timestamp']}")
        elif choice == "3":
            snaps = self.list_snapshots()
            if len(snaps) < 2:
                print("  Need at least 2 snapshots")
                return
            for i, s in enumerate(snaps[:10]):
                print(f"  {i+1}. {s['name']}")
            a = int(input("  First: ").strip()) - 1
            b = int(input("  Second: ").strip()) - 1
            diffs = self.compare(snaps[a]["path"], snaps[b]["path"])
            if diffs:
                for k, v in diffs.items():
                    print(f"  {k}: {v['before']} -> {v['after']}")
            else:
                print("  No differences")
        elif choice == "4":
            snaps = self.list_snapshots()
            if not snaps:
                print("  No snapshots")
                return
            for i, s in enumerate(snaps[:10]):
                print(f"  {i+1}. {s['name']}")
            idx = int(input("  Select: ").strip()) - 1
            with open(snaps[idx]["path"]) as f:
                data = json.load(f)
            for k, v in data.items():
                print(f"  {k}: {v}")

    def shutdown(self) -> None:
        self.log("Shutting down Memory System plugin")


def register() -> dict[str, Any]:
    plugin = MemorySystemPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
