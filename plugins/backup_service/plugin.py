"""MEGASUS Backup Service Plugin — Full backup/restore with progress tracking."""
from __future__ import annotations
import os
import time
import logging
import subprocess
from datetime import datetime
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("backup_service")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")


class BackupServicePlugin(Plugin):
    """Full device backup and restore with progress tracking."""

    name = "backup_service"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Full device backup/restore with progress tracking"

    def __init__(self) -> None:
        super().__init__()
        os.makedirs(BACKUP_DIR, exist_ok=True)

    def _ts(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def full_backup(self, name: str = "", include_apps: bool = True,
                    include_data: bool = True) -> str:
        """Create full ADB backup."""
        if not name:
            name = f"backup_{self._ts()}"
        output_path = os.path.join(BACKUP_DIR, f"{name}.ab")

        self.log(f"Starting full backup -> {output_path}")
        cmd = ["backup"]
        if include_apps:
            cmd.append("-apk")
        if include_data:
            cmd.append("-shared")
        cmd.extend(["-f", output_path, "-all"])

        out, err, rc = self.adb(cmd, timeout=300)
        if rc == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / 1048576
            self.log(f"Backup complete: {output_path} ({size_mb:.1f} MB)")
            return output_path
        self.log(f"Backup failed: {err}")
        return ""

    def restore_backup(self, backup_path: str) -> bool:
        """Restore from ADB backup file."""
        if not os.path.exists(backup_path):
            self.log(f"Backup file not found: {backup_path}")
            return False
        size_mb = os.path.getsize(backup_path) / 1048576
        self.log(f"Restoring {backup_path} ({size_mb:.1f} MB)...")
        out, err, rc = self.adb(["restore", backup_path], timeout=300)
        if rc == 0:
            self.log("Restore complete")
            return True
        self.log(f"Restore failed: {err}")
        return False

    def backup_app(self, package: str) -> str:
        """Backup a single app's APK + data."""
        ts = self._ts()
        output_path = os.path.join(BACKUP_DIR, f"{package}_{ts}.ab")
        self.log(f"Backing up {package}...")
        out, err, rc = self.adb(["backup", "-apk", "-f", output_path, package], timeout=120)
        if rc == 0:
            self.log(f"App backup: {output_path}")
            return output_path
        return ""

    def list_backups(self) -> list[dict]:
        """List all backup files."""
        backups = []
        for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if f.endswith(".ab"):
                path = os.path.join(BACKUP_DIR, f)
                backups.append({
                    "name": f,
                    "path": path,
                    "size_mb": round(os.path.getsize(path) / 1048576, 2),
                    "modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
                })
        return backups

    def delete_backup(self, path: str) -> bool:
        if os.path.exists(path):
            os.remove(path)
            self.log(f"Deleted: {path}")
            return True
        return False

    def run(self) -> None:
        """Interactive backup menu."""
        print("\n  === BACKUP SERVICE ===")
        print("  1. Full backup")
        print("  2. Backup single app")
        print("  3. Restore backup")
        print("  4. List backups")
        print("  5. Delete backup")
        print("  0. Back")

        choice = input("\n  Choice: ").strip()
        if choice == "0":
            return
        elif choice == "1":
            name = input("  Name (Enter=auto): ").strip()
            p = self.full_backup(name or "")
            if p:
                print(f"  Saved: {p}")
            else:
                print("  Failed")
        elif choice == "2":
            pkg = input("  Package name: ").strip()
            p = self.backup_app(pkg)
            if p:
                print(f"  Saved: {p}")
            else:
                print("  Failed")
        elif choice == "3":
            backups = self.list_backups()
            if not backups:
                print("  No backups")
                return
            for i, b in enumerate(backups[:10]):
                print(f"  {i+1}. {b['name']} ({b['size_mb']} MB)")
            idx = int(input("  Select: ").strip()) - 1
            if 0 <= idx < len(backups):
                self.restore_backup(backups[idx]["path"])
        elif choice == "4":
            backups = self.list_backups()
            for b in backups:
                print(f"  {b['name']:40s} {b['size_mb']:>8.2f} MB  {b['modified']}")
        elif choice == "5":
            backups = self.list_backups()
            if not backups:
                print("  No backups")
                return
            for i, b in enumerate(backups[:10]):
                print(f"  {i+1}. {b['name']}")
            idx = int(input("  Select: ").strip()) - 1
            if 0 <= idx < len(backups):
                self.delete_backup(backups[idx]["path"])

    def shutdown(self) -> None:
        self.log("Shutting down Backup Service plugin")


def register() -> dict[str, Any]:
    plugin = BackupServicePlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
