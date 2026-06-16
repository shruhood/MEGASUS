"""MEGASUS Telegram Bot Plugin - Entrypoint and lifecycle."""
from __future__ import annotations
import logging
import threading
from typing import Any, Optional

from core.plugin import Plugin

from config import PluginConfig
from telegram_client import TelegramClient, TelegramError
from adb_manager import ADBManager, ADBError
from commands import CommandHandler

logger = logging.getLogger("telegram_bot")


class TelegramBotPlugin(Plugin):
    """Telegram Bot plugin for remote MEGASUS control."""

    name = "telegram_bot"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Remote control MEGASUS via Telegram Bot API"

    def __init__(self) -> None:
        super().__init__()
        self.config = PluginConfig()
        self.client: Optional[TelegramClient] = None
        self.adb: Optional[ADBManager] = None
        self.handler: Optional[CommandHandler] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def initialize(self) -> None:
        """Initialize the bot."""
        self.log("Initializing Telegram Bot plugin")
        self.adb = ADBManager()
        self.client = TelegramClient(token=self.config.bot_token, max_retries=3)
        self.handler = CommandHandler(self.client, self.adb)
        self.log("Telegram Bot plugin initialized")

    def run(self) -> None:
        """Start the bot polling loop (blocking)."""
        if not self.client or not self.handler:
            self.log("Plugin not initialized")
            return
        token = self.config.bot_token
        if token == "YOUR_BOT_TOKEN_HERE":
            self.log("ERROR: Set bot_token in plugins/telegram_bot/config.json")
            return
        self.log("Bot starting...")
        self._running = True
        offset = None
        while self._running:
            try:
                updates = self.client.get_updates(offset=offset, timeout=30)
                for update in updates:
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = msg.get("chat", {}).get("id")
                    if text and chat_id:
                        if not self.config.is_chat_allowed(chat_id):
                            self.client.send_message(chat_id, "Unauthorized")
                            continue
                        parts = text.strip().split()
                        if parts and parts[0].startswith("/m"):
                            cmd = parts[0][2:].lower() if len(parts[0]) > 2 else ""
                            args = parts[1:]
                            self.handler.execute(cmd, chat_id, args)
            except TelegramError as e:
                self.log("Telegram error: " + str(e))
                import time
                time.sleep(5)
            except KeyboardInterrupt:
                self.log("Bot stopped by user")
                break
            except Exception as e:
                self.log("Bot error: " + str(e))
                import time
                time.sleep(5)

    def start(self) -> None:
        """Start bot in background thread."""
        if self._thread and self._thread.is_alive():
            self.log("Bot already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
        self.log("Bot thread started")

    def stop(self) -> None:
        """Stop the bot."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None
        self.log("Bot stopped")

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        self.log("Shutting down Telegram Bot plugin")
        self.stop()


def register() -> dict[str, Any]:
    """Register the plugin with MEGASUS."""
    plugin = TelegramBotPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
