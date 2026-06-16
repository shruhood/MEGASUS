"""Remote control via Telegram Bot"""
import os, sys
from core.plugin import Plugin

class TelegramBotPlugin(Plugin):
    name = "telegram_bot"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Remote control via Telegram Bot"

    def initialize(self):
        self.log("Initialized " + self.name)

    def shutdown(self):
        self.log("Shutdown " + self.name)

def register():
    return TelegramBotPlugin