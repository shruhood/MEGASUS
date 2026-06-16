"""MEGASUS Discord Bot Plugin — Remote control via Discord."""
from __future__ import annotations
import os
import json
import logging
import threading
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("discord_bot")

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "bot_token": "YOUR_DISCORD_BOT_TOKEN",
    "prefix": "!m",
    "allowed_users": [],
    "allowed_channels": [],
}


def _load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return dict(DEFAULT_CONFIG)


class DiscordBotPlugin(Plugin):
    """Discord bot for remote MEGASUS control."""

    name = "discord_bot"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Discord bot for remote MEGASUS control"

    def __init__(self) -> None:
        super().__init__()
        self.config = _load_config()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _check_discord(self) -> bool:
        """Check if discord.py is available."""
        try:
            import discord  # noqa: F401
            return True
        except ImportError:
            return False

    def _run_bot(self) -> None:
        """Run the Discord bot (requires discord.py)."""
        try:
            import discord
            from discord.ext import commands
        except ImportError:
            self.log("discord.py not installed — pip install discord.py")
            return

        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix=self.config["prefix"], intents=intents)

        @bot.event
        async def on_ready():
            self.log(f"Discord bot ready: {bot.user}")

        @bot.command()
        async def status(ctx):
            """Get device status."""
            out, _, _ = self.adb_shell("dumpsys battery | grep level")
            battery = out.strip().split(":")[-1].strip() if out else "?"
            out2, _, _ = self.adb_shell("getprop ro.product.model")
            model = out2.strip() if out2 else "?"
            await ctx.send(f"Device: {model} | Battery: {battery}%")

        @bot.command()
        async def screenshot(ctx):
            """Take a screenshot."""
            ts = self.adb_shell("date +%s")[0].strip()
            remote = f"/sdcard/discord_{ts}.png"
            local = os.path.join(self.PROJECT_ROOT, "screenshots", f"discord_{ts}.png")
            os.makedirs(os.path.dirname(local), exist_ok=True)
            self.adb_shell(f"screencap -p {remote}")
            self.adb(["pull", remote, local])
            self.adb_shell(f"rm {remote}")
            if os.path.exists(local):
                await ctx.send(file=discord.File(local))
            else:
                await ctx.send("Screenshot failed")

        @bot.command()
        async def shell(ctx, *, command: str):
            """Run ADB shell command."""
            out, err, rc = self.adb_shell(command, timeout=30)
            result = out[:1900] if out else err[:1900] if err else "(no output)"
            await ctx.send(f"```\n{result}\n```")

        @bot.command()
        async def info(ctx):
            """Get device info."""
            out, _, _ = self.adb_shell("getprop ro.build.version.release")
            android = out.strip() if out else "?"
            out2, _, _ = self.adb_shell("getprop ro.product.model")
            model = out2.strip() if out2 else "?"
            out3, _, _ = self.adb_shell("dumpsys battery")
            bat_level = "?"
            for line in out3.splitlines():
                if "level:" in line:
                    bat_level = line.split(":")[-1].strip()
            await ctx.send(
                f"Model: {model}\nAndroid: {android}\nBattery: {bat_level}%"
            )

        token = self.config["bot_token"]
        if token == "YOUR_DISCORD_BOT_TOKEN":
            self.log("Set bot_token in plugins/discord_bot/config.json")
            return
        bot.run(token)

    def run(self) -> None:
        """Interactive menu."""
        print("\n  === DISCORD BOT ===")
        print("  1. Start bot")
        print("  2. Check discord.py")
        print("  3. Edit config")
        print("  0. Back")

        choice = input("\n  Choice: ").strip()
        if choice == "0":
            return
        elif choice == "1":
            if not self._check_discord():
                print("  discord.py not installed — pip install discord.py")
                return
            print("  Starting bot (Ctrl+C to stop)...")
            self._run_bot()
        elif choice == "2":
            if self._check_discord():
                print("  discord.py: INSTALLED")
            else:
                print("  discord.py: NOT FOUND")
        elif choice == "3":
            print(f"  Config file: {CONFIG_FILE}")
            print(f"  Current token: {self.config['bot_token'][:10]}...")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            self.log("Bot already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_bot, daemon=True)
        self._thread.start()
        self.log("Discord bot thread started")

    def stop(self) -> None:
        self._running = False
        self.log("Discord bot stopped")

    def shutdown(self) -> None:
        self.log("Shutting down Discord Bot plugin")
        self.stop()


def register() -> dict[str, Any]:
    plugin = DiscordBotPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
