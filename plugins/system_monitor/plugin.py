"""MEGASUS System Monitor Plugin — Live CPU/RAM/battery/network dashboard."""
from __future__ import annotations
import os
import sys
import time
import threading
import logging
from datetime import datetime
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("system_monitor")


class SystemMonitorPlugin(Plugin):
    """Real-time system monitoring dashboard."""

    name = "system_monitor"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Live CPU/RAM/battery/network/process monitoring"

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._interval = 2.0
        self._history: list[dict] = []
        self._max_history = 300  # 2 min at 2s interval

    # ── Data collectors ──────────────────────────────────────────

    def _get_cpu(self) -> dict:
        """Read /proc/stat for CPU usage."""
        try:
            if sys.platform == "linux":
                with open("/proc/stat") as f:
                    line = f.readline()
                parts = line.split()
                if parts[0] == "cpu":
                    total = sum(int(x) for x in parts[1:])
                    idle = int(parts[3])
                    return {"usage_percent": round((1 - idle / total) * 100, 1) if total else 0}
            # Fallback: use adb shell
            out = self.adb_shell("cat /proc/stat | head -1")
            if out:
                parts = out.split()
                total = sum(int(x) for x in parts[1:])
                idle = int(parts[3])
                return {"usage_percent": round((1 - idle / total) * 100, 1) if total else 0}
        except Exception:
            pass
        return {"usage_percent": -1}

    def _get_ram(self) -> dict:
        """Read memory info."""
        try:
            if sys.platform == "linux":
                mem = {}
                with open("/proc/meminfo") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            mem[parts[0].strip()] = int(parts[1].strip().split()[0])
                total = mem.get("MemTotal", 0)
                avail = mem.get("MemAvailable", 0)
                used = total - avail
                return {
                    "total_mb": total // 1024,
                    "used_mb": used // 1024,
                    "available_mb": avail // 1024,
                    "percent": round((used / total) * 100, 1) if total else 0,
                }
            out = self.adb_shell("cat /proc/meminfo | head -5")
            if out:
                mem = {}
                for line in out.splitlines():
                    parts = line.split(":")
                    if len(parts) == 2:
                        mem[parts[0].strip()] = int(parts[1].strip().split()[0])
                total = mem.get("MemTotal", 0)
                avail = mem.get("MemAvailable", 0)
                used = total - avail
                return {
                    "total_mb": total // 1024,
                    "used_mb": used // 1024,
                    "available_mb": avail // 1024,
                    "percent": round((used / total) * 100, 1) if total else 0,
                }
        except Exception:
            pass
        return {"total_mb": 0, "used_mb": 0, "available_mb": 0, "percent": 0}

    def _get_battery(self) -> dict:
        """Get battery status via adb."""
        try:
            out = self.adb_shell("dumpsys battery")
            if not out:
                return {}
            bat = {}
            for line in out.splitlines():
                line = line.strip()
                if "level:" in line:
                    bat["level"] = int(line.split(":")[-1].strip())
                elif "status:" in line:
                    bat["status"] = line.split(":")[-1].strip()
                elif "temperature:" in line:
                    bat["temp"] = int(line.split(":")[-1].strip()) / 10.0
                elif "health:" in line:
                    bat["health"] = line.split(":")[-1].strip()
            return bat
        except Exception:
            pass
        return {}

    def _get_network(self) -> dict:
        """Get network stats."""
        try:
            out = self.adb_shell("cat /proc/net/dev")
            if not out:
                return {}
            interfaces = {}
            for line in out.splitlines()[2:]:
                parts = line.split(":")
                if len(parts) != 2:
                    continue
                iface = parts[0].strip()
                if iface in ("lo",):
                    continue
                vals = parts[1].split()
                if len(vals) >= 16:
                    rx = int(vals[0])
                    tx = int(vals[8])
                    interfaces[iface] = {
                        "rx_mb": round(rx / 1048576, 2),
                        "tx_mb": round(tx / 1048576, 2),
                    }
            return interfaces
        except Exception:
            pass
        return {}

    def _get_top_processes(self, n: int = 5) -> list[dict]:
        """Get top N processes by CPU."""
        try:
            out = self.adb_shell(f"top -b -n1 -o %CPU | head -{n + 5}")
            if not out:
                return []
            procs = []
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 9 and parts[0].isdigit():
                    procs.append({
                        "pid": parts[0],
                        "cpu": parts[2] if "%" in parts[2] else "?",
                        "name": parts[-1],
                    })
                if len(procs) >= n:
                    break
            return procs
        except Exception:
            pass
        return []

    # ── Display ──────────────────────────────────────────────────

    def _bar(self, percent: float, width: int = 20) -> str:
        filled = int(percent / 100 * width)
        if percent > 80:
            color = "\033[91m"  # red
        elif percent > 50:
            color = "\033[93m"  # yellow
        else:
            color = "\033[92m"  # green
        reset = "\033[0m"
        return f"{color}{'█' * filled}{'░' * (width - filled)}{reset}"

    def _render(self) -> str:
        """Render a single dashboard frame."""
        cpu = self._get_cpu()
        ram = self._get_ram()
        bat = self._get_battery()
        net = self._get_network()
        procs = self._get_top_processes(5)

        ts = datetime.now().strftime("%H:%M:%S")
        lines = [
            f"\033[2J\033[H",  # clear screen
            f"  ╔══════════════════════════════════════════════════╗",
            f"  ║  \033[1m🔍 SYSTEM MONITOR\033[0m  —  {ts}                    ║",
            f"  ╚══════════════════════════════════════════════════╝",
            "",
        ]

        # CPU
        cpu_pct = cpu.get("usage_percent", 0)
        lines.append(f"  \033[1mCPU:\033[0m  {self._bar(cpu_pct)} {cpu_pct}%")

        # RAM
        ram_pct = ram.get("percent", 0)
        lines.append(
            f"  \033[1mRAM:\033[0m  {self._bar(ram_pct)} {ram_pct}%  "
            f"({ram.get('used_mb', 0)}MB / {ram.get('total_mb', 0)}MB)"
        )

        # Battery
        if bat:
            level = bat.get("level", "?")
            status = bat.get("status", "?")
            temp = bat.get("temp", "?")
            health = bat.get("health", "?")
            lines.append(
                f"  \033[1mBAT:\033[0m  {level}%  Status: {status}  "
                f"Temp: {temp}°C  Health: {health}"
            )

        # Network
        if net:
            lines.append("")
            lines.append(f"  \033[1mNETWORK:\033[0m")
            for iface, stats in net.items():
                lines.append(
                    f"    {iface:12s}  ↓ {stats['rx_mb']:8.2f} MB  "
                    f"↑ {stats['tx_mb']:8.2f} MB"
                )

        # Top processes
        if procs:
            lines.append("")
            lines.append(f"  \033[1mTOP PROCESSES:\033[0m")
            for p in procs:
                lines.append(f"    PID {p['pid']:>6s}  CPU {p['cpu']:>5s}  {p['name']}")

        lines.append("")
        lines.append("  Press Ctrl+C to stop monitoring")

        return "\n".join(lines)

    # ── Lifecycle ─────────────────────────────────────────────────

    def run(self) -> None:
        """Run live monitoring loop."""
        self._running = True
        try:
            while self._running:
                print(self._render())
                time.sleep(self._interval)
        except KeyboardInterrupt:
            self.log("Monitor stopped by user")

    def start(self) -> None:
        """Start in background thread."""
        if self._thread and self._thread.is_alive():
            self.log("Already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
        self.log("Monitor thread started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        self.log("Monitor stopped")

    def shutdown(self) -> None:
        self.log("Shutting down System Monitor")
        self.stop()


def register() -> dict[str, Any]:
    plugin = SystemMonitorPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
