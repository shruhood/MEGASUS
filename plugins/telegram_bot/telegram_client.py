"""Telegram Bot API client with retry and rate limiting."""
from __future__ import annotations
import logging
import time
from typing import Any, Optional
from pathlib import Path
import requests

logger = logging.getLogger("telegram_client")

class TelegramError(Exception):
    pass

class TelegramClient:
    """Telegram Bot API wrapper with retry and rate limiting."""
    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, token: str, timeout: int = 30, max_retries: int = 3) -> None:
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = requests.Session()
        self._last_request_time: float = 0
        self._min_interval: float = 0.05

    def _url(self, method: str) -> str:
        return self.BASE_URL.format(token=self.token, method=method)

    def _request(self, method: str, data: Optional[dict] = None, files: Optional[dict] = None) -> dict:
        for attempt in range(1, self.max_retries + 1):
            try:
                elapsed = time.time() - self._last_request_time
                if elapsed < self._min_interval:
                    time.sleep(self._min_interval - elapsed)
                url = self._url(method)
                if files:
                    resp = self._session.post(url, data=data, files=files, timeout=self.timeout)
                elif data:
                    resp = self._session.post(url, json=data, timeout=self.timeout)
                else:
                    resp = self._session.get(url, timeout=self.timeout)
                self._last_request_time = time.time()
                resp.raise_for_status()
                result = resp.json()
                if not result.get("ok"):
                    raise TelegramError("API error: " + str(result.get("description", "unknown")))
                return result
            except requests.RequestException as e:
                logger.warning("Attempt %d/%d failed: %s", attempt, self.max_retries, e)
                if attempt < self.max_retries:
                    time.sleep(attempt * 2)
                else:
                    raise TelegramError("Request failed after " + str(self.max_retries) + " attempts: " + str(e))

    def get_updates(self, offset: Optional[int] = None, timeout: int = 30) -> list[dict]:
        data = {"timeout": timeout}
        if offset: data["offset"] = offset
        result = self._request("getUpdates", data=data)
        return result.get("result", [])

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> dict:
        return self._request("sendMessage", data={"chat_id": chat_id, "text": text, "parse_mode": parse_mode})

    def send_photo(self, chat_id: int, photo_path: Path, caption: str = "") -> dict:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": chat_id, "caption": caption}
            return self._request("sendPhoto", data=data, files=files)

    def send_document(self, chat_id: int, file_path: Path, caption: str = "") -> dict:
        with open(file_path, "rb") as f:
            files = {"document": (file_path.name, f)}
            data = {"chat_id": chat_id, "caption": caption}
            return self._request("sendDocument", data=data, files=files)

    def get_me(self) -> dict:
        return self._request("getMe")
