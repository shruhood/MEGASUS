"""MEGASUS File Manager Plugin — Push/pull with progress, batch ops, file browser."""
from __future__ import annotations
import os
import logging
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("file_manager")


class FileManagerPlugin(Plugin):
    """Enhanced file management with progress tracking."""

    name = "file_manager"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Enhanced file manager with progress and batch operations"

    def __init__(self) -> None:
        super().__init__()

    def push_file(self, local_path: str, remote_path: str) -> bool:
        """Push file to device with size reporting."""
        if not os.path.exists(local_path):
            self.log(f"Local file not found: {local_path}")
            return False
        size = os.path.getsize(local_path)
        self.log(f"Pushing {local_path} ({size} bytes) -> {remote_path}")
        out, err, rc = self.adb(["push", local_path, remote_path])
        if rc == 0:
            self.log("Push complete")
            return True
        self.log(f"Push failed: {err}")
        return False

    def pull_file(self, remote_path: str, local_path: str) -> bool:
        """Pull file from device."""
        self.log(f"Pulling {remote_path} -> {local_path}")
        out, err, rc = self.adb(["pull", remote_path, local_path])
        if rc == 0:
            size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            self.log(f"Pull complete ({size} bytes)")
            return True
        self.log(f"Pull failed: {err}")
        return False

    def push_dir(self, local_dir: str, remote_dir: str) -> tuple[int, int]:
        """Push all files from a directory. Returns (success, total)."""
        if not os.path.isdir(local_dir):
            return 0, 0
        success = 0
        total = 0
        for root, _, files in os.walk(local_dir):
            for fname in files:
                total += 1
                local_path = os.path.join(root, fname)
                rel = os.path.relpath(local_path, local_dir)
                remote_path = f"{remote_dir}/{rel}"
                if self.push_file(local_path, remote_path):
                    success += 1
        self.log(f"Push dir: {success}/{total} files")
        return success, total

    def pull_dir(self, remote_dir: str, local_dir: str) -> tuple[int, int]:
        """Pull directory listing and download files."""
        out, err, rc = self.adb_shell(f"ls -R {remote_dir}")
        if rc != 0 or not out:
            return 0, 0
        os.makedirs(local_dir, exist_ok=True)
        success = 0
        total = 0
        for line in out.splitlines():
            line = line.strip()
            if not line or ":" in line:
                continue
            total += 1
            remote_path = f"{remote_dir}/{line}"
            local_path = os.path.join(local_dir, line)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            if self.pull_file(remote_path, local_path):
                success += 1
        return success, total

    def browse(self, remote_path: str = "/sdcard") -> list[str]:
        """List files in a remote directory."""
        out, err, rc = self.adb_shell(f"ls -la {remote_path}")
        if rc == 0 and out:
            return out.splitlines()
        return []

    def delete_remote(self, remote_path: str) -> bool:
        """Delete a file on device."""
        out, err, rc = self.adb_shell(f"rm -f {remote_path}")
        return rc == 0

    def mkdir_remote(self, remote_path: str) -> bool:
        """Create directory on device."""
        out, err, rc = self.adb_shell(f"mkdir -p {remote_path}")
        return rc == 0

    def run(self) -> None:
        """Interactive file manager menu."""
        current = "/sdcard"
        while True:
            print(f"\n  === FILE MANAGER ===  Current: {current}")
            print("  1. Browse directory")
            print("  2. Push file to device")
            print("  3. Pull file from device")
            print("  4. Push directory")
            print("  5. Delete remote file")
            print("  6. Create remote directory")
            print("  0. Back")

            choice = input("\n  Choice: ").strip()
            if choice == "0":
                break
            elif choice == "1":
                path = input(f"  Path [{current}]: ").strip() or current
                files = self.browse(path)
                for f in files:
                    print(f"  {f}")
            elif choice == "2":
                local = input("  Local file: ").strip().strip('"')
                remote = input(f"  Remote path [{current}/]: ").strip() or current
                if self.push_file(local, remote):
                    print("  OK")
                else:
                    print("  FAILED")
            elif choice == "3":
                remote = input("  Remote file: ").strip()
                local = input("  Local path [./]: ").strip() or "./"
                if self.pull_file(remote, local):
                    print("  OK")
                else:
                    print("  FAILED")
            elif choice == "4":
                local = input("  Local dir: ").strip().strip('"')
                remote = input(f"  Remote dir [{current}]: ").strip() or current
                s, t = self.push_dir(local, remote)
                print(f"  Pushed {s}/{t} files")
            elif choice == "5":
                remote = input("  Remote file to delete: ").strip()
                if self.delete_remote(remote):
                    print("  Deleted")
                else:
                    print("  Failed")
            elif choice == "6":
                remote = input("  New dir path: ").strip()
                if self.mkdir_remote(remote):
                    print("  Created")
                else:
                    print("  Failed")

    def shutdown(self) -> None:
        self.log("Shutting down File Manager plugin")


def register() -> dict[str, Any]:
    plugin = FileManagerPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
