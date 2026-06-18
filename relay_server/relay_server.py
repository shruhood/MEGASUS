#!/usr/bin/env python3
"""
MEGASUS Relay Server — WebSocket relay for remote device control.

Runs on any public server (VPS, Cloudflare Worker with Durable Objects, etc.).
Bridges MEGASUS clients to phone agents via named device channels.

Protocol:
  - Agents (phone) connect to   /agent/<device_id>
  - Clients (MEGASUS) connect to /client/<device_id>
  - Both authenticate with a shared token
  - Messages are relayed bidirectionally

Usage:
    python relay_server.py --host 0.0.0.0 --port 8765

    # With TLS (recommended for production):
    python relay_server.py --host 0.0.0.0 --port 8765 --cert cert.pem --key key.pem

    # With device token file:
    python relay_server.py --tokens tokens.json

tokens.json format:
{
    "DEVICE_ID": "hex_token_here",
    "another-device": "its_token"
}
"""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
import argparse
import os
import signal
import time
from collections import defaultdict
from typing import Dict, Optional

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("ERROR: websockets not installed. Run: pip install websockets")
    import sys
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Relay] %(message)s",
)
log = logging.getLogger("relay")

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class DeviceChannel:
    """Holds the connected agent and client for a device."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.agent_ws: Optional[WebSocketServerProtocol] = None
        self.client_ws: Optional[WebSocketServerProtocol] = None
        self.agent_authenticated = False
        self.client_authenticated = False
        self.created_at = time.time()
        self.last_activity = time.time()

    @property
    def agent_online(self) -> bool:
        return self.agent_ws is not None and self.agent_authenticated

    @property
    def client_online(self) -> bool:
        return self.client_ws is not None and self.client_authenticated

    @property
    def fully_connected(self) -> bool:
        return self.agent_online and self.client_online


class RelayServer:
    def __init__(self, host: str, port: int, tokens: Dict[str, str],
                 ssl_ctx: Optional[ssl.SSLContext] = None):
        self.host = host
        self.port = port
        self.tokens = tokens  # {device_id: token}
        self.ssl = ssl_ctx
        self.channels: Dict[str, DeviceChannel] = defaultdict(
            lambda key: DeviceChannel(key)
        )
        self._pending: Dict[str, asyncio.Queue] = {}  # device_id -> Queue for client->agent msgs

    def _get_channel(self, device_id: str) -> DeviceChannel:
        if device_id not in self.channels:
            self.channels[device_id] = DeviceChannel(device_id)
        return self.channels[device_id]

    def _validate_token(self, device_id: str, token: str) -> bool:
        """Check if token matches registered device."""
        if device_id in self.tokens:
            return self.tokens[device_id] == token
        # If no tokens file, accept any token (dev mode)
        return len(self.tokens) == 0

    async def _handle_agent(self, ws: WebSocketServerProtocol, device_id: str):
        """Handle a phone agent connection."""
        channel = self._get_channel(device_id)
        log.info(f"Agent connecting: {device_id} from {ws.remote_address}")

        # Check if agent already connected
        if channel.agent_online:
            await ws.send(json.dumps({"type": "error", "error": "Agent already connected"}))
            await ws.close()
            return

        channel.agent_ws = ws
        channel.agent_authenticated = False

        try:
            # Wait for auth
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
            msg = json.loads(raw)
            if msg.get("type") != "auth" or not self._validate_token(device_id, msg.get("token", "")):
                await ws.send(json.dumps({"type": "error", "error": "Auth failed"}))
                await ws.close()
                channel.agent_ws = None
                return

            channel.agent_authenticated = True
            channel.last_activity = time.time()
            await ws.send(json.dumps({"type": "auth_ok", "device_id": device_id}))
            log.info(f"Agent authenticated: {device_id}")

            # Notify client if connected
            if channel.client_online:
                try:
                    await channel.client_ws.send(json.dumps({
                        "type": "event",
                        "event": "agent_connected",
                        "device_id": device_id,
                    }))
                except Exception:
                    pass

            # Relay: client -> agent
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=300)
                    msg = json.loads(raw)
                    channel.last_activity = time.time()

                    if channel.client_online:
                        await channel.client_ws.send(json.dumps(msg))
                    else:
                        # Client not connected — send error back
                        await ws.send(json.dumps({
                            "type": "error",
                            "error": "No client connected",
                        }))
                except asyncio.TimeoutError:
                    # Send ping to keep alive
                    try:
                        await ws.send(json.dumps({"type": "ping"}))
                    except Exception:
                        break
                except websockets.exceptions.ConnectionClosed:
                    break

        except (asyncio.TimeoutError, json.JSONDecodeError):
            log.warning(f"Agent auth timeout or invalid: {device_id}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            log.info(f"Agent disconnected: {device_id}")
            channel.agent_ws = None
            channel.agent_authenticated = False
            if channel.client_online:
                try:
                    await channel.client_ws.send(json.dumps({
                        "type": "event",
                        "event": "agent_disconnected",
                        "device_id": device_id,
                    }))
                except Exception:
                    pass

    async def _handle_client(self, ws: WebSocketServerProtocol, device_id: str):
        """Handle a MEGASUS client connection."""
        channel = self._get_channel(device_id)
        log.info(f"Client connecting: {device_id} from {ws.remote_address}")

        if channel.client_online:
            await ws.send(json.dumps({"type": "error", "error": "Client already connected"}))
            await ws.close()
            return

        channel.client_ws = ws
        channel.client_authenticated = False

        try:
            # Auth
            raw = await asyncio.wait_for(ws.recv(), timeout=10)
            msg = json.loads(raw)
            if msg.get("type") != "auth" or not self._validate_token(device_id, msg.get("token", "")):
                await ws.send(json.dumps({"type": "error", "error": "Auth failed"}))
                await ws.close()
                channel.client_ws = None
                return

            channel.client_authenticated = True
            channel.last_activity = time.time()
            agent_status = "online" if channel.agent_online else "offline"
            await ws.send(json.dumps({
                "type": "auth_ok",
                "device_id": device_id,
                "agent_status": agent_status,
            }))
            log.info(f"Client authenticated: {device_id} (agent: {agent_status})")

            # Relay: client -> agent
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=300)
                    msg = json.loads(raw)
                    channel.last_activity = time.time()

                    if channel.agent_online:
                        await channel.agent_ws.send(json.dumps(msg))
                    else:
                        await ws.send(json.dumps({
                            "type": "error",
                            "error": "Agent offline — phone not connected",
                        }))
                except asyncio.TimeoutError:
                    try:
                        await ws.send(json.dumps({"type": "ping"}))
                    except Exception:
                        break
                except websockets.exceptions.ConnectionClosed:
                    break

        except (asyncio.TimeoutError, json.JSONDecodeError):
            log.warning(f"Client auth timeout: {device_id}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            log.info(f"Client disconnected: {device_id}")
            channel.client_ws = None
            channel.client_authenticated = False

    async def handler(self, ws: WebSocketServerProtocol, path: str):
        """Route connections based on path."""
        # Path format: /agent/<device_id> or /client/<device_id>
        parts = path.strip("/").split("/")
        if len(parts) != 2 or parts[0] not in ("agent", "client"):
            await ws.send(json.dumps({"type": "error", "error": "Invalid path. Use /agent/<id> or /client/<id>"}))
            await ws.close()
            return

        role, device_id = parts
        if role == "agent":
            await self._handle_agent(ws, device_id)
        else:
            await self._handle_client(ws, device_id)

    async def start(self):
        protocol = "wss" if self.ssl else "ws"
        log.info(f"Starting relay server on {protocol}://{self.host}:{self.port}")
        log.info(f"Registered devices: {list(self.tokens.keys()) or 'ANY (dev mode)'}")

        async with websockets.serve(
            self.handler,
            self.host,
            self.port,
            ssl=self.ssl,
            ping_interval=20,
            ping_timeout=10,
        ):
            await asyncio.Future()  # run forever


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def load_tokens(path: str) -> Dict[str, str]:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="MEGASUS Relay Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    parser.add_argument("--tokens", default="", help="Path to tokens JSON file")
    parser.add_argument("--cert", default="", help="TLS certificate file")
    parser.add_argument("--key", default="", help="TLS private key file")
    args = parser.parse_args()

    tokens = load_tokens(args.tokens)
    ssl_ctx = None
    if args.cert and args.key:
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.load_cert_chain(args.cert, args.key)
        log.info(f"TLS enabled with {args.cert}")

    server = RelayServer(
        host=args.host,
        port=args.port,
        tokens=tokens,
        ssl_ctx=ssl_ctx,
    )

    loop = asyncio.new_event_loop()

    def _shutdown(signum, frame):
        log.info("Shutting down relay...")
        loop.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(server.start())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
        log.info("Relay stopped")


if __name__ == "__main__":
    main()
