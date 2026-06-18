"""
MEGASUS Module: REMOTE CONNECTION — Universal connectivity over cellular/any network.

Uses a WebSocket relay server to tunnel ADB commands to a phone agent.
The phone agent initiates an outbound connection (works through CGNAT/firewall),
so no public IP or port forwarding is needed on the phone side.

Architecture:
  MEGASUS (this module) <--WebSocket--> Relay Server <--WebSocket--> Phone Agent
                                                                     (Termux)
                                                                      adb shell

Device identity: IMEI or user-defined device alias.
Auth: Per-device token (generated at registration time).
"""
from __future__ import annotations

import json
import hashlib
import os
import sys
import time
import threading
import secrets
from datetime import datetime

from core.engine import log_command

MODULE_NAME = "Remote Connection"
MODULE_ICON = "🌍"

# ---------------------------------------------------------------------------
# Config paths
# ---------------------------------------------------------------------------
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "remote")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "remote_config.json")
_HOSTS_FILE = os.path.join(_CONFIG_DIR, "known_hosts.json")

os.makedirs(_CONFIG_DIR, exist_ok=True)


def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Relay client (sync wrapper around websockets)
# ---------------------------------------------------------------------------
class RelayClient:
    """Synchronous wrapper for WebSocket relay communication.

    Usage:
        client = RelayClient(relay_url, device_id, token)
        client.connect()
        response = client.send_command("dumpsys battery")
        client.disconnect()
    """

    def __init__(self, relay_url: str, device_id: str, token: str, timeout: int = 30):
        self.relay_url = relay_url.rstrip("/")
        self.device_id = device_id
        self.token = token
        self.timeout = timeout
        self._ws = None
        self._connected = False
        self._error: str | None = None

    # -- low-level websocket ops -------------------------------------------
    def _ws_connect(self) -> None:
        import asyncio
        import websockets
        from urllib.parse import quote

        async def _connect():
            # Token passed as query param (Cloudflare Worker) + first message (standalone relay)
            device_enc = quote(self.device_id, safe="")
            uri = f"{self.relay_url}/client/{device_enc}?token={self.token}"
            self._ws = await websockets.connect(uri, ping_interval=20, ping_timeout=10)
            # Send auth message (for standalone relay server; Cloudflare Worker ignores this)
            auth_msg = json.dumps({"type": "auth", "token": self.token})
            await self._ws.send(auth_msg)
            resp = await asyncio.wait_for(self._ws.recv(), timeout=10)
            data = json.loads(resp)
            if data.get("type") != "auth_ok":
                raise ConnectionError(f"Auth failed: {data.get('error', 'unknown')}")
            self._connected = True

        asyncio.get_event_loop().run_until_complete(_connect())

    def _ws_send(self, msg: dict) -> dict:
        import asyncio
        import websockets

        async def _send():
            await self._ws.send(json.dumps(msg))
            resp = await asyncio.wait_for(self._ws.recv(), timeout=self.timeout)
            return json.loads(resp)

        return asyncio.get_event_loop().run_until_complete(_send())

    def _ws_close(self) -> None:
        import asyncio

        async def _close():
            if self._ws:
                await self._ws.close()

        try:
            asyncio.get_event_loop().run_until_complete(_close())
        except Exception:
            pass
        self._connected = False
        self._ws = None

    # -- public API ---------------------------------------------------------
    def connect(self) -> tuple[bool, str]:
        """Establish WebSocket connection to relay + authenticate."""
        try:
            import websockets  # noqa: F401 — import check
        except ImportError:
            self._error = "websockets package missing. Run: pip install websockets"
            return False, self._error
        try:
            self._ws_connect()
            log_command(f"remote_connect {self.device_id}", "connected")
            return True, f"Connected to relay | Device: {self.device_id}"
        except ImportError:
            self._error = "websockets package missing. pip install websockets"
            return False, self._error
        except ConnectionError as e:
            self._error = str(e)
            return False, str(e)
        except Exception as e:
            self._error = str(e)
            return False, f"Connection failed: {e}"

    def send_command(self, command: str) -> tuple[str, str, int]:
        """Send a shell command to the phone via relay.

        Returns (stdout, stderr_or_error, returncode).
        """
        if not self._connected or not self._ws:
            return "", "Not connected", -1
        try:
            resp = self._ws_send({"type": "cmd", "command": command})
            if resp.get("type") == "result":
                return (
                    resp.get("stdout", ""),
                    resp.get("stderr", ""),
                    resp.get("rc", 0),
                )
            return "", resp.get("error", "Unknown relay error"), -1
        except Exception as e:
            return "", str(e), -1

    def disconnect(self) -> None:
        self._ws_close()
        log_command(f"remote_disconnect {self.device_id}", "disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def error(self) -> str | None:
        return self._error

    # -- convenience wrappers -----------------------------------------------
    def shell(self, cmd: str, timeout: int | None = None) -> tuple[str, str, int]:
        """Alias for send_command — matches same interface as _run_shell."""
        old = self.timeout
        if timeout:
            self.timeout = timeout
        try:
            return self.send_command(cmd)
        finally:
            self.timeout = old

    def push_file(self, local_path: str, remote_path: str) -> tuple[bool, str]:
        """Send a small file to the phone via relay (base64 encoded)."""
        import base64
        try:
            with open(local_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            resp = self._ws_send({
                "type": "push",
                "remote_path": remote_path,
                "data": data,
            })
            if resp.get("type") == "ok":
                return True, f"Pushed to {remote_path}"
            return False, resp.get("error", "push failed")
        except Exception as e:
            return False, str(e)

    def pull_file(self, remote_path: str, local_path: str) -> tuple[bool, str]:
        """Pull a small file from the phone via relay."""
        import base64
        try:
            resp = self._ws_send({"type": "pull", "remote_path": remote_path})
            if resp.get("type") == "file":
                raw = base64.b64decode(resp["data"])
                os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(raw)
                return True, f"Saved to {local_path}"
            return False, resp.get("error", "pull failed")
        except Exception as e:
            return False, str(e)

    def screenshot(self, save_dir: str = "screenshots") -> tuple[bool, str]:
        """Take a screenshot via relay."""
        import base64
        ts = int(time.time())
        remote = f"/sdcard/remote_{ts}.png"
        # screencap on device
        out, err, rc = self.shell(f"screencap -p {remote}")
        if rc != 0:
            return False, f"screencap failed: {err}"
        # pull
        local = os.path.join(save_dir, f"remote_{ts}.png")
        ok, msg = self.pull_file(remote, local)
        # cleanup
        self.shell(f"rm -f {remote}")
        return ok, msg if ok else msg


# ---------------------------------------------------------------------------
# Registration helpers (device setup)
# ---------------------------------------------------------------------------
def _generate_token() -> str:
    return secrets.token_hex(16)


def register_device(device_id: str, relay_url: str, *, label: str | None = None) -> dict:
    """Register a new device — generates token and saves locally.

    The same token must be configured on the phone agent side.
    """
    token = _generate_token()
    config = _load_json(_CONFIG_FILE, {})
    hosts = _load_json(_HOSTS_FILE, {})

    config[device_id] = {
        "relay_url": relay_url,
        "token": token,
        "label": label or device_id,
        "registered_at": datetime.now().isoformat(),
    }
    hosts[device_id] = {"label": label or device_id, "relay_url": relay_url}

    _save_json(_CONFIG_FILE, config)
    _save_json(_HOSTS_FILE, hosts)
    log_command("remote_register", f"device={device_id}")
    return {"device_id": device_id, "token": token, "relay_url": relay_url, "label": label or device_id}


def list_devices() -> list[dict]:
    """List all registered remote devices."""
    hosts = _load_json(_HOSTS_FILE, {})
    config = _load_json(_CONFIG_FILE, [])
    result = []
    for device_id, info in hosts.items():
        cfg = _load_json(_CONFIG_FILE, {}).get(device_id, {})
        result.append({
            "device_id": device_id,
            "label": info.get("label", device_id),
            "relay_url": info.get("relay_url", ""),
            "registered_at": cfg.get("registered_at", ""),
        })
    return result


def get_device_config(device_id: str) -> dict | None:
    config = _load_json(_CONFIG_FILE, {})
    return config.get(device_id)


def remove_device(device_id: str) -> bool:
    config = _load_json(_CONFIG_FILE, {})
    hosts = _load_json(_HOSTS_FILE, {})
    if device_id in config:
        del config[device_id]
        _save_json(_CONFIG_FILE, config)
    if device_id in hosts:
        del hosts[device_id]
        _save_json(_HOSTS_FILE, hosts)
    log_command("remote_remove", f"device={device_id}")
    return True


# ---------------------------------------------------------------------------
# Connection presets — save/load
# ---------------------------------------------------------------------------
def save_preset(name: str, relay_url: str, device_id: str) -> None:
    presets = _load_json(os.path.join(_CONFIG_DIR, "presets.json"), {})
    presets[name] = {"relay_url": relay_url, "device_id": device_id}
    _save_json(os.path.join(_CONFIG_DIR, "presets.json"), presets)


def get_presets() -> dict:
    return _load_json(os.path.join(_CONFIG_DIR, "presets.json"), {})
