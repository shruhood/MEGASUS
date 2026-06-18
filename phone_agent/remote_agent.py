#!/usr/bin/env python3
"""
MEGASUS Phone Agent — Runs on Android via Termux.

Connects OUTBOUND to the relay server (works through CGNAT / any network).
Receives shell commands from MEGASUS via the relay, executes locally, returns output.

Install in Termux:
    pkg install python
    pip install websockets requests
    python remote_agent.py --device-id MY_PHONE --token <token> --relay wss://your-relay.com

Auto-start on boot (Termux:Boot):
    Create ~/.termux/boot/megasusus with:
        #!/data/data/com.termux/files/usr/bin/sh
        python /path/to/remote_agent.py --device-id MY_PHONE --token <token> --relay wss://your-relay.com &
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import os
import time
import base64
import argparse
import signal
import logging

try:
    import websockets
except ImportError:
    print("ERROR: websockets not installed. Run: pip install websockets")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MEGASUS-Agent] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("agent")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_imei() -> str:
    """Try to read device IMEI via Termux API or getprop."""
    # Try termux-api first
    try:
        r = subprocess.run(
            ["termux-telephony-deviceinfo"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            imei = data.get("device_id") or data.get("imei")
            if imei:
                return imei
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
        pass

    # Fallback: getprop (may not give real IMEI on all devices)
    for prop in ["ro.gsm.imei", "ro.ril.oem.imei", "persist.radio.imei"]:
        try:
            r = subprocess.run(
                ["getprop", prop],
                capture_output=True, text=True, timeout=3,
            )
            val = r.stdout.strip()
            if val and val != "unknown":
                return val
        except Exception:
            pass

    # Last resort: generate stable ID from device properties
    try:
        r = subprocess.run(
            ["getprop", "ro.serialno"],
            capture_output=True, text=True, timeout=3,
        )
        serial = r.stdout.strip()
        if serial:
            return f"serial-{serial}"
    except Exception:
        pass

    return "unknown-device"


def run_shell(cmd: str, timeout: int = 30) -> tuple[str, str, int]:
    """Execute a shell command and return (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            executable="/data/data/com.termux/files/usr/bin/bash",
        )
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 124
    except Exception as e:
        return "", str(e), -1


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------
class PhoneAgent:
    def __init__(self, relay_url: str, device_id: str, token: str):
        self.relay_url = relay_url.rstrip("/")
        self.device_id = device_id
        self.token = token
        self.ws = None
        self.running = False
        self.reconnect_delay = 5  # seconds

    async def connect(self):
        from urllib.parse import quote
        device_enc = quote(self.device_id, safe="")
        uri = f"{self.relay_url}/agent/{device_enc}?token={self.token}"
        log.info(f"Connecting to relay: {uri}")
        self.ws = await websockets.connect(uri, ping_interval=20, ping_timeout=10)
        # Send auth message (for standalone relay; Cloudflare Worker validates from query param)
        auth_msg = json.dumps({"type": "auth", "token": self.token})
        await self.ws.send(auth_msg)
        resp = await asyncio.wait_for(self.ws.recv(), timeout=10)
        data = json.loads(resp)
        if data.get("type") != "auth_ok":
            raise ConnectionError(f"Auth failed: {data.get('error', 'unknown')}")
        log.info("Authenticated with relay server")

    async def handle_command(self, msg: dict) -> dict:
        """Process an incoming command from MEGASUS via relay."""
        cmd_type = msg.get("type")

        if cmd_type == "cmd":
            command = msg.get("command", "")
            timeout = msg.get("timeout", 30)
            log.info(f"Executing: {command[:80]}")
            stdout, stderr, rc = run_shell(command, timeout=timeout)
            return {
                "type": "result",
                "stdout": stdout[:50000],  # cap at 50KB
                "stderr": stderr[:10000],
                "rc": rc,
            }

        elif cmd_type == "push":
            # Receive a file and write to device
            remote_path = msg.get("remote_path", "/sdcard/remote_file")
            data_b64 = msg.get("data", "")
            try:
                raw = base64.b64decode(data_b64)
                os.makedirs(os.path.dirname(remote_path) or "/sdcard", exist_ok=True)
                with open(remote_path, "wb") as f:
                    f.write(raw)
                return {"type": "ok", "path": remote_path, "size": len(raw)}
            except Exception as e:
                return {"type": "error", "error": str(e)}

        elif cmd_type == "pull":
            # Read a file and send back
            remote_path = msg.get("remote_path", "")
            try:
                with open(remote_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                return {"type": "file", "data": data}
            except Exception as e:
                return {"type": "error", "error": str(e)}

        elif cmd_type == "ping":
            return {"type": "pong", "ts": time.time()}

        else:
            return {"type": "error", "error": f"Unknown command type: {cmd_type}"}

    async def run(self):
        """Main loop: connect, handle messages, auto-reconnect."""
        self.running = True
        while self.running:
            try:
                await self.connect()
                self.reconnect_delay = 5  # reset on successful connect

                async for raw in self.ws:
                    try:
                        msg = json.loads(raw)
                        response = await self.handle_command(msg)
                        await self.ws.send(json.dumps(response))
                    except json.JSONDecodeError:
                        await self.ws.send(json.dumps({"type": "error", "error": "Invalid JSON"}))
                    except Exception as e:
                        log.error(f"Handler error: {e}")
                        try:
                            await self.ws.send(json.dumps({"type": "error", "error": str(e)}))
                        except Exception:
                            break

            except websockets.exceptions.ConnectionClosed as e:
                log.warning(f"Connection closed: {e}. Reconnecting in {self.reconnect_delay}s...")
            except ConnectionRefusedError:
                log.warning(f"Relay unreachable. Reconnecting in {self.reconnect_delay}s...")
            except Exception as e:
                log.error(f"Error: {e}. Reconnecting in {self.reconnect_delay}s...")

            if self.running:
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 120)  # exponential backoff, max 2min

    def stop(self):
        self.running = False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="MEGASUS Phone Agent — Remote device control")
    parser.add_argument("--relay", required=True, help="Relay server URL (ws:// or wss://)")
    parser.add_argument("--device-id", help="Device ID (default: auto-detect IMEI)")
    parser.add_argument("--token", required=True, help="Auth token from registration")
    parser.add_argument("--timeout", type=int, default=30, help="Default command timeout")
    args = parser.parse_args()

    device_id = args.device_id or get_imei()
    log.info(f"Device ID: {device_id}")
    log.info(f"Relay: {args.relay}")

    agent = PhoneAgent(
        relay_url=args.relay,
        device_id=device_id,
        token=args.token,
    )

    loop = asyncio.new_event_loop()

    def _shutdown(signum, frame):
        log.info("Shutting down agent...")
        agent.stop()
        loop.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(agent.run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
        log.info("Agent stopped")


if __name__ == "__main__":
    main()
