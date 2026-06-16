"""MEGASUS AI Agent Plugin v2 — Multi-layer intelligent device automation.

Architecture:
  Layer 1: Device Intelligence  — reads state, detects anomalies, builds context
  Layer 2: Task Planning         — NLU → structured action plans
  Layer 3: Execution Engine      — runs ADB commands with retry/error handling
  Layer 4: Learning & Memory     — stores patterns, what worked/failed, preferences
  Layer 5: Communication         — reports via Telegram/Discord/CLI/Web

Modes:
  - REACTIVE:  You ask → it does (chat interface)
  - PROACTIVE: Monitors device → acts on rules (battery low → save state)
  - AUTONOMOUS: Full agent loop → plans → executes → learns
"""
from __future__ import annotations
import os
import json
import time
import logging
import threading
import subprocess
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

from core.plugin import Plugin

logger = logging.getLogger("ai_agent")

BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR / "memory"
RULES_FILE = BASE_DIR / "rules.json"
LEARNING_FILE = BASE_DIR / "learning.json"
CONTEXT_FILE = BASE_DIR / "context.json"

for d in [MEMORY_DIR]:
    d.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# Layer 1: Device Intelligence
# ═══════════════════════════════════════════════════════════════

class DeviceIntelligence:
    """Reads and interprets device state. Builds rich context for the agent."""

    def __init__(self, plugin: "AIAgentPlugin"):
        self.plugin = plugin

    def get_full_context(self) -> dict:
        """Build complete device context snapshot."""
        ctx = {
            "timestamp": datetime.now().isoformat(),
            "device": self._device_info(),
            "battery": self._battery(),
            "network": self._network(),
            "storage": self._storage(),
            "memory": self._memory(),
            "cpu": self._cpu(),
            "apps": self._apps(),
            "processes": self._processes(),
            "notifications": self._notifications(),
            "screen": self._screen_state(),
        }
        # Persist for other layers
        try:
            with open(CONTEXT_FILE, "w") as f:
                json.dump(ctx, f, indent=2, default=str)
        except Exception:
            pass
        return ctx

    def _device_info(self) -> dict:
        out, _, _ = self.plugin.adb_shell("getprop ro.product.model")
        model = out.strip()
        out, _, _ = self.plugin.adb_shell("getprop ro.build.version.release")
        android = out.strip()
        out, _, _ = self.plugin.adb_shell("getprop ro.build.display.id")
        build = out.strip()
        out, _, _ = self.plugin.adb_shell("getprop ro.hardware")
        hardware = out.strip()
        out, _, _ = self.plugin.adb_shell("getprop ro.build.version.sdk")
        sdk = out.strip()
        return {"model": model, "android": android, "build": build,
                "hardware": hardware, "sdk": sdk}

    def _battery(self) -> dict:
        out, _, _ = self.plugin.adb_shell("dumpsys battery")
        bat = {}
        for line in out.splitlines():
            line = line.strip()
            if "level:" in line:
                bat["level"] = int(line.split(":")[-1].strip())
            elif "status:" in line:
                bat["status"] = line.split(":")[-1].strip()
            elif "temperature:" in line:
                bat["temp_c"] = int(line.split(":")[-1].strip()) / 10.0
            elif "health:" in line:
                bat["health"] = line.split(":")[-1].strip()
            elif "plugged:" in line:
                bat["plugged"] = int(line.split(":")[-1].strip())
        return bat

    def _network(self) -> dict:
        net = {}
        out, _, _ = self.plugin.adb_shell("ip route get 8.8.8.8 2>/dev/null")
        if out:
            parts = out.split()
            if "src" in parts:
                net["ip"] = parts[parts.index("src") + 1]
        out, _, _ = self.plugin.adb_shell("dumpsys wifi | grep -E 'mWifiInfo|SSID' | head -3")
        if out:
            for line in out.splitlines():
                if "SSID:" in line:
                    net["wifi_ssid"] = line.split("SSID:")[-1].strip().strip("'")
        out, _, _ = self.plugin.adb_shell("dumpsys connectivity | grep -i 'active' | head -3")
        net["connectivity"] = out.strip()[:200] if out else ""
        return net

    def _storage(self) -> dict:
        out, _, _ = self.plugin.adb_shell("df /data /sdcard /storage/emulated 2>/dev/null")
        storage = {}
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5:
                mount = parts[4]
                storage[mount] = {
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "percent": parts[5] if len(parts) > 5 else "?",
                }
        return storage

    def _memory(self) -> dict:
        out, _, _ = self.plugin.adb_shell("cat /proc/meminfo | head -5")
        mem = {}
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip().split()[0]
                mem[key] = int(val) // 1024  # convert KB to MB
        return mem

    def _cpu(self) -> dict:
        out, _, _ = self.plugin.adb_shell("cat /proc/loadavg")
        loads = out.strip().split()[:3] if out else []
        out, _, _ = self.plugin.adb_shell("nproc")
        cores = out.strip()
        return {"load_1m": loads[0] if len(loads) > 0 else "?",
                "load_5m": loads[1] if len(loads) > 1 else "?",
                "load_15m": loads[2] if len(loads) > 2 else "?",
                "cores": cores}

    def _apps(self) -> dict:
        out, _, _ = self.plugin.adb_shell("pm list packages -3 2>/dev/null | wc -l")
        third_party = int(out.strip()) if out.strip().isdigit() else 0
        out, _, _ = self.plugin.adb_shell("pm list packages -s 2>/dev/null | wc -l")
        system = int(out.strip()) if out.strip().isdigit() else 0
        out, _, _ = self.plugin.adb_shell("dumpsys activity activities | grep -i 'mResumedActivity' | head -1")
        foreground = out.strip() if out else ""
        return {"third_party": third_party, "system": system, "foreground": foreground}

    def _processes(self) -> list:
        out, _, _ = self.plugin.adb_shell("ps -A -o PID,USER,NAME,%CPU,%MEM 2>/dev/null | sort -k4 -rn | head -10")
        procs = []
        for line in out.splitlines()[1:]:
            parts = line.split(None, 4)
            if len(parts) >= 5:
                procs.append({
                    "pid": parts[0], "user": parts[1],
                    "name": parts[4], "cpu": parts[2], "mem": parts[3],
                })
        return procs

    def _notifications(self) -> list:
        out, _, _ = self.plugin.adb_shell("dumpsys notification --noredact 2>/dev/null | grep -A2 'NotificationRecord' | head -20")
        notifs = []
        for line in out.splitlines():
            if "pkg=" in line:
                pkg = ""
                for part in line.split():
                    if part.startswith("pkg="):
                        pkg = part.split("=")[1]
                if pkg:
                    notifs.append({"package": pkg})
        return notifs[:10]

    def _screen_state(self) -> dict:
        out, _, _ = self.plugin.adb_shell("dumpsys power | grep -E 'mWakefulness|mScreenOn|Display Power' | head -3")
        return {"power_state": out.strip()[:200] if out else ""}

    def detect_anomalies(self, ctx: dict) -> list[str]:
        """Analyze context and flag anomalies."""
        alerts = []
        bat = ctx.get("battery", {})
        if isinstance(bat.get("level"), int) and bat["level"] < 15:
            alerts.append(f"LOW BATTERY: {bat['level']}%")
        if isinstance(bat.get("temp_c"), (int, float)) and bat["temp_c"] > 45:
            alerts.append(f"HIGH TEMP: {bat['temp_c']}°C")
        cpu = ctx.get("cpu", {})
        try:
            load = float(cpu.get("load_1m", 0))
            cores = int(cpu.get("cores", 1))
            if load > cores * 0.9:
                alerts.append(f"HIGH CPU LOAD: {load} on {cores} cores")
        except (ValueError, TypeError):
            pass
        mem = ctx.get("memory", {})
        total = mem.get("MemTotal", 1)
        avail = mem.get("MemAvailable", 0)
        if total and (total - avail) / total > 0.9:
            alerts.append(f"LOW MEMORY: {avail}MB free of {total}MB")
        return alerts


# ═══════════════════════════════════════════════════════════════
# Layer 2: Task Planning — NLU → structured action plans
# ═══════════════════════════════════════════════════════════════

class TaskPlanner:
    """Natural language → structured action plans.

    Uses pattern matching + rule-based NLU. Can be extended with
    LLM-based planning via the external API bridge.
    """

    # Pattern: (regex_pattern, action_builder)
    PATTERNS = [
        # Battery
        (r"(?:battery|charge)\s*(?:level|status|info|percent)",
         lambda m, ctx: {"type": "query", "target": "battery", "command": "dumpsys battery"}),
        (r"(?:is|check)\s*(?:it|device)\s*(?:charging|plugged)",
         lambda m, ctx: {"type": "query", "target": "battery", "command": "dumpsys battery | grep 'plugged'"}),

        # Screenshot
        (r"(?:take|capture|grab|get)\s*(?:a\s*)?(?:screenshot|screen\s*shot|photo)",
         lambda m, ctx: {"type": "action", "target": "screenshot", "command": "screenshot"}),
        (r"(?:screen|display)\s*(?:off|lock|sleep)",
         lambda m, ctx: {"type": "action", "target": "screen", "command": "input keyevent 26"}),
        (r"(?:wake|unlock|turn\s*on)\s*(?:screen|display)",
         lambda m, ctx: {"type": "action", "target": "screen", "command": "input keyevent 26"}),

        # Reboot / Power
        (r"(?:reboot|restart|re\s*boot)\s*(?:device|phone|system)?",
         lambda m, ctx: {"type": "action", "target": "power", "command": "reboot"}),
        (r"(?:power\s*off|shutdown|turn\s*off)",
         lambda m, ctx: {"type": "action", "target": "power", "command": "reboot -p"}),
        (r"reboot\s*(?:to\s*)?(?:recovery|bootloader|fastboot)",
         lambda m, ctx: {"type": "action", "target": "power",
                         "command": "reboot " + (m.group(1) if m.lastindex and m.group(1) else "recovery")}),

        # Apps
        (r"(?:open|launch|start|run)\s+(?:app\s+)?(.+)",
         lambda m, ctx: {"type": "action", "target": "app",
                         "command": "monkey -p " + m.group(1).strip() + " -c android.intent.category.LAUNCHER 1"}),
        (r"(?:close|kill|stop|force\s*stop)\s+(?:app\s+)?(.+)",
         lambda m, ctx: {"type": "action", "target": "app",
                         "command": "am force-stop " + m.group(1).strip()}),
        (r"(?:list|show|what)\s+(?:all\s+)?(?:running\s+)?(?:apps|processes|packages)",
         lambda m, ctx: {"type": "query", "target": "apps",
                         "command": "ps -A -o PID,USER,NAME | head -20"}),
        (r"(?:install)\s+(.+\.apk)",
         lambda m, ctx: {"type": "action", "target": "app",
                         "command": "install -r " + m.group(1).strip()}),

        # Network
        (r"(?:wifi|wireless)\s*(?:on|enable|activate)",
         lambda m, ctx: {"type": "action", "target": "network", "command": "svc wifi enable"}),
        (r"(?:wifi|wireless)\s*(?:off|disable|deactivate)",
         lambda m, ctx: {"type": "action", "target": "network", "command": "svc wifi disable"}),
        (r"(?:mobile\s*data|cellular\s*data|data)\s*(?:on|enable)",
         lambda m, ctx: {"type": "action", "target": "network", "command": "svc data enable"}),
        (r"(?:mobile\s*data|cellular\s*data|data)\s*(?:off|disable)",
         lambda m, ctx: {"type": "action", "target": "network", "command": "svc data disable"}),
        (r"(?:get|show|what(?:'s| is))\s*(?:the\s*)?(?:ip|IP\s*address)",
         lambda m, ctx: {"type": "query", "target": "network", "command": "ip addr show | grep 'inet '"}),

        # Storage
        (r"(?:storage|disk|space|memory)\s*(?:info|status|usage|free)",
         lambda m, ctx: {"type": "query", "target": "storage", "command": "df -h /data /sdcard"}),

        # Files
        (r"(?:list|show|ls)\s+(?:files\s+)?(?:in\s+)?(?:the\s+)?(.+)",
         lambda m, ctx: {"type": "query", "target": "files", "command": f"ls -la {m.group(1).strip()}"}),
        (r"(?:pull|download|copy)\s+(.+)\s+(?:to|from)\s+(.+)",
         lambda m, ctx: {"type": "action", "target": "files", "command": f"pull {m.group(1).strip()} {m.group(2).strip()}"}),
        (r"(?:push|upload|send)\s+(.+)\s+(?:to)\s+(.+)",
         lambda m, ctx: {"type": "action", "target": "files", "command": f"push {m.group(1).strip()} {m.group(2).strip()}"}),

        # Security
        (r"(?:security|safe)\s*(?:audit|check|scan|status)",
         lambda m, ctx: {"type": "action", "target": "security", "command": "dumpsys package | grep -E 'permission|dangerous' | head -20"}),
        (r"(?:root|rooted|jailbreak)\s*(?:check|detect|status)",
         lambda m, ctx: {"type": "query", "target": "security", "command": "which su 2>/dev/null; getprop ro.debuggable; getprop ro.secure"}),

        # Info
        (r"(?:device|phone|system)\s*(?:info|status|details|specs)",
         lambda m, ctx: {"type": "query", "target": "device", "command": "getprop | grep -E 'ro.product|ro.build|ro.hardware' | sort"}),
        (r"(?:how\s*long|uptime|running\s*time)",
         lambda m, ctx: {"type": "query", "target": "device", "command": "uptime"}),

        # Notifications
        (r"(?:notification|alert|toast)\s*(?:list|show|check|get)",
         lambda m, ctx: {"type": "query", "target": "notifications", "command": "dumpsys notification --noredact | head -30"}),
        (r"(?:dismiss|clear)\s*(?:all\s*)?(?:notification|alert)s?",
         lambda m, ctx: {"type": "action", "target": "notifications", "command": "service call notification 1"}),

        # Shell passthrough
        (r"(?:run|execute|do)\s+(.+)",
         lambda m, ctx: {"type": "shell", "target": "custom", "command": m.group(1).strip()}),
    ]

    def plan(self, user_input: str, context: dict) -> list[dict]:
        """Parse user input into a list of action plans."""
        import re
        text = user_input.strip().lower()
        plans = []

        for pattern, builder in self.PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                plan = builder(m, context)
                plan["input"] = user_input
                plan["matched_pattern"] = pattern
                plans.append(plan)
                break  # first match wins

        if not plans:
            # Fallback: treat as shell command if it looks like one
            if any(text.startswith(p) for p in ["adb", "shell", "am ", "pm ", "dumpsys", "getprop", "setprop", "input", "svc "]):
                plans.append({"type": "shell", "target": "custom", "command": text, "input": user_input})
            else:
                plans.append({"type": "unknown", "target": "none", "command": "", "input": user_input})

        return plans


# ═══════════════════════════════════════════════════════════════
# Layer 3: Execution Engine
# ═══════════════════════════════════════════════════════════════

class ExecutionEngine:
    """Executes action plans with retry, error handling, and logging."""

    def __init__(self, plugin: "AIAgentPlugin"):
        self.plugin = plugin

    def execute(self, plan: dict) -> dict:
        """Execute a single action plan. Returns result dict."""
        target = plan.get("target", "none")
        cmd = plan.get("command", "")
        plan_type = plan.get("type", "unknown")

        result = {
            "plan": plan,
            "success": False,
            "output": "",
            "error": "",
            "timestamp": datetime.now().isoformat(),
        }

        if plan_type == "unknown":
            result["error"] = f"Could not understand: '{plan.get('input', '')}'"
            return result

        if not cmd:
            result["error"] = "No command to execute"
            return result

        try:
            if target == "screenshot":
                result = self._do_screenshot(result)
            elif target == "app":
                result = self._do_app_action(cmd, result)
            elif target == "screen":
                out, err, rc = self.plugin.adb_shell(cmd, timeout=15)
                result["success"] = rc == 0
                result["output"] = out
                result["error"] = err
            elif target == "power":
                result = self._do_power(cmd, result)
            elif target == "network":
                out, err, rc = self.plugin.adb_shell(cmd, timeout=15)
                result["success"] = rc == 0
                result["output"] = out
                result["error"] = err
            else:
                # Generic shell execution
                out, err, rc = self.plugin.adb_shell(cmd, timeout=30)
                result["success"] = rc == 0
                result["output"] = out
                result["error"] = err
        except Exception as e:
            result["error"] = str(e)

        return result

    def _do_screenshot(self, result: dict) -> dict:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote = f"/sdcard/ai_screenshot_{ts}.png"
        local = str(self.plugin.PROJECT_ROOT / "screenshots" / f"ai_screenshot_{ts}.png")
        self.plugin.adb_shell(f"screencap -p {remote}")
        out, err, rc = self.plugin.adb(["pull", remote, local])
        self.plugin.adb_shell(f"rm {remote}")
        result["success"] = rc == 0
        result["output"] = f"Screenshot saved: {local}" if rc == 0 else err
        result["screenshot_path"] = local if rc == 0 else ""
        return result

    def _do_app_action(self, cmd: str, result: dict) -> dict:
        out, err, rc = self.plugin.adb_shell(cmd, timeout=30)
        result["success"] = rc == 0
        result["output"] = out
        result["error"] = err
        return result

    def _do_power(self, cmd: str, result: dict) -> result:
        if "reboot" in cmd:
            result["output"] = f"Executing: {cmd}"
            result["success"] = True
            # Don't actually reboot in agent mode — just report
            result["warning"] = "Power commands are logged but not auto-executed by agent. Confirm manually."
        else:
            out, err, rc = self.plugin.adb_shell(cmd, timeout=15)
            result["success"] = rc == 0
            result["output"] = out
            result["error"] = err
        return result

    def execute_batch(self, plans: list[dict]) -> list[dict]:
        """Execute multiple plans in sequence."""
        results = []
        for plan in plans:
            r = self.execute(plan)
            results.append(r)
            if not r["success"] and plan.get("type") != "query":
                # Stop on first failure for action plans
                break
        return results


# ═══════════════════════════════════════════════════════════════
# Layer 4: Learning & Memory
# ═══════════════════════════════════════════════════════════════

class LearningMemory:
    """Stores patterns, preferences, and execution history.
    Learns from successes and failures to improve future plans."""

    def __init__(self):
        self.history: list[dict] = []
        self.patterns: dict[str, int] = {}  # pattern → success count
        self.preferences: dict[str, Any] = {}
        self._load()

    def _load(self):
        if LEARNING_FILE.exists():
            try:
                with open(LEARNING_FILE) as f:
                    data = json.load(f)
                self.history = data.get("history", [])[-100:]  # keep last 100
                self.patterns = data.get("patterns", {})
                self.preferences = data.get("preferences", {})
            except Exception:
                pass

    def _save(self):
        try:
            with open(LEARNING_FILE, "w") as f:
                json.dump({
                    "history": self.history[-100:],
                    "patterns": self.patterns,
                    "preferences": self.preferences,
                    "last_updated": datetime.now().isoformat(),
                }, f, indent=2, default=str)
        except Exception:
            pass

    def record(self, user_input: str, plan: dict, result: dict):
        """Record an execution for learning."""
        entry = {
            "input": user_input,
            "target": plan.get("target"),
            "command": plan.get("command"),
            "success": result.get("success"),
            "timestamp": datetime.now().isoformat(),
        }
        self.history.append(entry)

        # Update pattern success rates
        pattern = plan.get("matched_pattern", plan.get("target", "unknown"))
        if pattern not in self.patterns:
            self.patterns[pattern] = 0
        if result.get("success"):
            self.patterns[pattern] += 1
        else:
            self.patterns[pattern] -= 1

        self._save()

    def get_favorite_commands(self, n: int = 5) -> list[str]:
        """Return most successful commands."""
        successes = [h for h in self.history if h.get("success")]
        counts: dict[str, int] = {}
        for s in successes:
            cmd = s.get("command", "")
            counts[cmd] = counts.get(cmd, 0) + 1
        return [cmd for cmd, _ in sorted(counts.items(), key=lambda x: -x[1])[:n]]

    def get_common_targets(self) -> dict[str, int]:
        """What does the user most often ask about?"""
        counts: dict[str, int] = {}
        for h in self.history:
            t = h.get("target", "unknown")
            counts[t] = counts.get(t, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    def set_preference(self, key: str, value: Any):
        self.preferences[key] = value
        self._save()


# ═══════════════════════════════════════════════════════════════
# Layer 5: Communication / Reporting
# ═══════════════════════════════════════════════════════════════

class CommunicationLayer:
    """Formats and sends reports. Works with Telegram, Discord, CLI, Web."""

    @staticmethod
    def format_status(ctx: dict) -> str:
        """Format device context as readable report."""
        lines = ["📱 DEVICE STATUS", "─" * 30]
        d = ctx.get("device", {})
        if d:
            lines.append(f"  Model: {d.get('model', '?')}")
            lines.append(f"  Android: {d.get('android', '?')}")
        b = ctx.get("battery", {})
        if b:
            level = b.get("level", "?")
            lines.append(f"  Battery: {level}% ({b.get('status', '?')})")
            if b.get("temp_c"):
                lines.append(f"  Temp: {b['temp_c']}°C")
        n = ctx.get("network", {})
        if n:
            lines.append(f"  IP: {n.get('ip', '?')}")
            if n.get("wifi_ssid"):
                lines.append(f"  WiFi: {n['wifi_ssid']}")
        m = ctx.get("memory", {})
        if m:
            total = m.get("MemTotal", 0)
            avail = m.get("MemAvailable", 0)
            if total:
                used_pct = round((1 - avail / total) * 100)
                lines.append(f"  RAM: {avail}MB free / {total}MB ({used_pct}% used)")
        s = ctx.get("storage", {})
        if s:
            lines.append("  Storage:")
            for mount, info in list(s.items())[:3]:
                lines.append(f"    {mount}: {info.get('percent', '?')} used")
        return "\n".join(lines)

    @staticmethod
    def format_result(result: dict) -> str:
        """Format execution result."""
        if result.get("success"):
            out = result.get("output", "Done")
            return f"✅ {out[:500]}"
        else:
            err = result.get("error", "Unknown error")
            return f"❌ {err[:500]}"

    @staticmethod
    def format_alerts(alerts: list[str]) -> str:
        if not alerts:
            return ""
        return "⚠️ ALERTS:\n" + "\n".join(f"  • {a}" for a in alerts)


# ═══════════════════════════════════════════════════════════════
# Main Plugin — ties all layers together
# ═══════════════════════════════════════════════════════════════

class AIAgentPlugin(Plugin):
    """Multi-layer AI agent for MEGASUS."""

    name = "ai_agent"
    version = "2.0.0"
    author = "MEGASUS"
    description = "Multi-layer AI agent — device intelligence, task planning, auto-execution, learning memory"

    def __init__(self) -> None:
        super().__init__()
        self.intelligence = DeviceIntelligence(self)
        self.planner = TaskPlanner()
        self.engine = ExecutionEngine(self)
        self.memory = LearningMemory()
        self.comm = CommunicationLayer()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._proactive_rules: list[dict] = self._load_rules()

    def _load_rules(self) -> list[dict]:
        if RULES_FILE.exists():
            try:
                with open(RULES_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        # Default proactive rules
        return [
            {"name": "low_battery_alert", "condition": "battery.level < 15",
             "action": "notify", "message": "Battery critically low!"},
            {"name": "high_temp_alert", "condition": "battery.temp_c > 45",
             "action": "notify", "message": "Device overheating!"},
            {"name": "high_memory_alert", "condition": "memory.percent > 90",
             "action": "notify", "message": "Memory usage critical!"},
        ]

    def _save_rules(self):
        with open(RULES_FILE, "w") as f:
            json.dump(self._proactive_rules, f, indent=2)

    # ── Reactive mode: user asks → agent does ──────────────────

    def ask(self, user_input: str) -> str:
        """Process user input and return response."""
        # Get current context
        ctx = self.intelligence.get_full_context()

        # Plan
        plans = self.planner.plan(user_input, ctx)
        plan = plans[0]

        if plan["type"] == "unknown":
            return f"🤔 I don't understand: '{user_input}'\nTry: 'battery status', 'take screenshot', 'open chrome', 'list apps'"

        # Execute
        result = self.engine.execute(plan)

        # Learn
        self.memory.record(user_input, plan, result)

        # Respond
        return self.comm.format_result(result)

    # ── Proactive mode: monitor → alert → act ──────────────────

    def _proactive_loop(self, interval: int = 30):
        """Background loop that monitors device and acts on rules."""
        while self._running:
            try:
                ctx = self.intelligence.get_full_context()
                alerts = self.intelligence.detect_anomalies(ctx)

                if alerts:
                    report = self.comm.format_alerts(alerts)
                    self.log(f"ALERT: {alerts}")
                    # In proactive mode, could auto-act:
                    # - low battery → enable battery saver
                    # - high temp → kill heavy processes
                    # - high memory → clear caches

                # Check custom rules
                for rule in self._proactive_rules:
                    self._evaluate_rule(rule, ctx)

            except Exception as e:
                self.log(f"Proactive error: {e}")

            time.sleep(interval)

    def _evaluate_rule(self, rule: dict, ctx: dict):
        """Evaluate a proactive rule against current context."""
        condition = rule.get("condition", "")
        try:
            # Simple condition evaluator
            if "battery.level" in condition:
                level = ctx.get("battery", {}).get("level", 100)
                threshold = int(condition.split("<")[-1].strip()) if "<" in condition else 0
                if level < threshold:
                    self.log(f"Rule triggered: {rule['name']} (battery={level}%)")
            elif "battery.temp_c" in condition:
                temp = ctx.get("battery", {}).get("temp_c", 0)
                threshold = int(condition.split(">")[-1].strip()) if ">" in condition else 999
                if temp > threshold:
                    self.log(f"Rule triggered: {rule['name']} (temp={temp}°C)")
        except Exception:
            pass

    # ── Lifecycle ────────────────────────────────────────────────

    def run(self) -> None:
        """Interactive agent chat."""
        print("\n  ╔══════════════════════════════════════╗")
        print("  ║  🤖 MEGASUS AI AGENT v2              ║")
        print("  ║  Type 'status' for device info       ║")
        print("  ║  Type 'proactive' to start monitor   ║")
        print("  ║  Type 'history' to see past actions   ║")
        print("  ║  Type 'quit' to exit                  ║")
        print("  ╚══════════════════════════════════════╝")

        while True:
            try:
                user_input = input("\n  🤖 > ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                break
            if user_input.lower() == "status":
                ctx = self.intelligence.get_full_context()
                print(self.comm.format_status(ctx))
                continue
            if user_input.lower() == "proactive":
                print("  Starting proactive monitor (Ctrl+C to stop)...")
                self._running = True
                try:
                    self._proactive_loop()
                except KeyboardInterrupt:
                    self._running = False
                    print("  Stopped.")
                continue
            if user_input.lower() == "history":
                favs = self.memory.get_favorite_commands()
                if favs:
                    print("  Most used commands:")
                    for f in favs:
                        print(f"    • {f}")
                else:
                    print("  No history yet")
                continue
            if user_input.lower() == "alerts":
                ctx = self.intelligence.get_full_context()
                alerts = self.intelligence.detect_anomalies(ctx)
                if alerts:
                    print(self.comm.format_alerts(alerts))
                else:
                    print("  ✅ All clear — no anomalies detected")
                continue

            # Normal query
            response = self.ask(user_input)
            print(f"  {response}")

    def start_proactive(self, interval: int = 30):
        """Start proactive monitoring in background."""
        if self._thread and self._thread.is_alive():
            self.log("Proactive already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._proactive_loop, args=(interval,), daemon=True)
        self._thread.start()
        self.log(f"Proactive monitor started (interval={interval}s)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self.log("Agent stopped")

    def shutdown(self):
        self.log("Shutting down AI Agent")
        self.stop()


def register() -> dict[str, Any]:
    plugin = AIAgentPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
