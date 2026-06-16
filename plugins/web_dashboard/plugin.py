"""MEGASUS Web Dashboard Plugin — Browser-based device control panel."""
from __future__ import annotations
import os
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("web_dashboard")
DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "static")


class WebDashboardPlugin(Plugin):
    """Web-based dashboard for MEGASUS."""

    name = "web_dashboard"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Web dashboard for browser-based device control"

    def __init__(self) -> None:
        super().__init__()
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self.port = 8899
        os.makedirs(DASHBOARD_DIR, exist_ok=True)
        self._ensure_static()

    def _ensure_static(self) -> None:
        """Create static HTML if not exists."""
        html_path = os.path.join(DASHBOARD_DIR, "index.html")
        if os.path.exists(html_path):
            return
        html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MEGASUS Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:'Segoe UI',monospace}
.header{background:#161b22;padding:16px 24px;border-bottom:1px solid #30363d}
.header h1{color:#58a6ff;font-size:1.4em}
.container{max-width:1200px;margin:0 auto;padding:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:20px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}
.card h3{color:#58a6ff;margin-bottom:12px;font-size:0.9em;text-transform:uppercase}
.stat{font-size:2em;font-weight:bold;color:#3fb950}
.label{color:#8b949e;font-size:0.8em}
pre{background:#0d1117;padding:12px;border-radius:4px;overflow-x:auto;font-size:0.85em;max-height:300px}
.btn{background:#238636;color:#fff;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;margin:4px;font-size:0.85em}
.btn:hover{background:#2ea043}
.btn.red{background:#da3633}
.btn.red:hover{background:#f85149}
input[type=text],input[type=number]{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;padding:6px 10px;border-radius:4px;width:100%;margin:4px 0}
.status{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.status.online{background:#3fb950}
.status.offline{background:#f85149}
</style>
</head>
<body>
<div class="header"><h1>🔧 MEGASUS Dashboard</h1></div>
<div class="container">
<div class="grid">
  <div class="card"><h3>Battery</h3><div class="stat" id="bat_level">--</div><div class="label" id="bat_status">Loading...</div></div>
  <div class="card"><h3>Device</h3><div class="label">Model</div><div id="dev_model" style="font-size:1.2em;color:#fff">--</div><div class="label" style="margin-top:8px">Android</div><div id="dev_android" style="color:#fff">--</div></div>
  <div class="card"><h3>Network</h3><div class="label">IP</div><div id="net_ip" style="color:#fff;font-size:1.1em">--</div><div class="label" style="margin-top:8px">WiFi</div><div id="net_wifi" style="color:#fff">--</div></div>
</div>
<div class="card" style="margin-bottom:16px"><h3>Quick Commands</h3>
  <button class="btn" onclick="runCmd('screenshot')">📸 Screenshot</button>
  <button class="btn" onclick="runCmd('reboot')">🔄 Reboot</button>
  <button class="btn red" onclick="runCmd('shutdown')">⏻ Shutdown</button>
  <button class="btn" onclick="runCmd('lock')">🔒 Lock</button>
  <button class="btn" onclick="runCmd('wake')">💡 Wake</button>
</div>
<div class="card" style="margin-bottom:16px"><h3>Custom ADB Shell</h3>
  <input type="text" id="cmdInput" placeholder="adb shell command..." onkeydown="if(event.key==='Enter')runCustom()">
  <button class="btn" onclick="runCustom()">Run</button>
</div>
<div class="card"><h3>Output</h3><pre id="output">Ready...</pre></div>
</div>
<script>
async function runCmd(cmd){
  document.getElementById('output').textContent='Running...';
  try{const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd})});const t=await r.text();document.getElementById('output').textContent=t}catch(e){document.getElementById('output').textContent='Error: '+e}
}
async function runCustom(){
  const c=document.getElementById('cmdInput').value;if(!c)return;
  document.getElementById('output').textContent='Running: '+c+'...';
  try{const r=await fetch('/api/shell',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:c})});const t=await r.text();document.getElementById('output').textContent=t}catch(e){document.getElementById('output').textContent='Error: '+e}
}
async function refresh(){
  try{const r=await fetch('/api/status');const d=await r.json();
    document.getElementById('bat_level').textContent=(d.battery?.level||'?')+'%';
    document.getElementById('bat_status').textContent=d.battery?.status||'?';
    document.getElementById('dev_model').textContent=d.device?.model||'?';
    document.getElementById('dev_android').textContent=d.device?.android||'?';
    document.getElementById('net_ip').textContent=d.network?.ip||'?';
    document.getElementById('net_wifi').textContent=d.network?.wifi||'?';
  }catch(e){}
}
setInterval(refresh,5000);refresh();
</script>
</body>
</html>"""
        with open(html_path, "w") as f:
            f.write(html)

    def _make_handler(self):
        """Create HTTP request handler."""
        plugin = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # suppress default logging

            def do_GET(self):
                if self.path == "/" or self.path == "/index.html":
                    html_path = os.path.join(DASHBOARD_DIR, "index.html")
                    with open(html_path) as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(content.encode())
                elif self.path == "/api/status":
                    status = plugin._get_status()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(status).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    data = json.loads(body)
                except Exception:
                    data = {}

                if self.path == "/api/run":
                    cmd = data.get("command", "")
                    out = plugin._quick_command(cmd)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(out.encode())
                elif self.path == "/api/shell":
                    cmd = data.get("cmd", "")
                    out, err, rc = plugin.adb_shell(cmd, timeout=30)
                    result = out if rc == 0 else err
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(result.encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        return Handler

    def _get_status(self) -> dict:
        """Get device status for API."""
        status = {"battery": {}, "device": {}, "network": {}}
        out, _, _ = self.adb_shell("dumpsys battery")
        if out:
            for line in out.splitlines():
                if "level:" in line:
                    status["battery"]["level"] = int(line.split(":")[-1].strip())
                elif "status:" in line:
                    status["battery"]["status"] = line.split(":")[-1].strip()
        out, _, _ = self.adb_shell("getprop ro.product.model")
        status["device"]["model"] = out.strip()
        out, _, _ = self.adb_shell("getprop ro.build.version.release")
        status["device"]["android"] = out.strip()
        out, _, _ = self.adb_shell("ip route get 8.8.8.8")
        if out:
            parts = out.split()
            if "src" in parts:
                status["network"]["ip"] = parts[parts.index("src") + 1]
        out, _, _ = self.adb_shell("dumpsys wifi | grep 'mWifiInfo'")
        if out and "SSID" in out:
            status["network"]["wifi"] = out.strip()
        return status

    def _quick_command(self, cmd: str) -> str:
        """Execute quick commands."""
        commands = {
            "screenshot": lambda: self._do_screenshot(),
            "reboot": lambda: self.adb_shell("reboot")[:2] and "Rebooting...",
            "shutdown": lambda: self.adb_shell("reboot -p")[:2] and "Shutting down...",
            "lock": lambda: self.adb_shell("input keyevent 26")[:2] and "Locked",
            "wake": lambda: self.adb_shell("input keyevent 26")[:2] and "Woke",
        }
        fn = commands.get(cmd)
        if fn:
            try:
                return fn()
            except Exception as e:
                return f"Error: {e}"
        return f"Unknown command: {cmd}"

    def _do_screenshot(self) -> str:
        import time
        ts = str(int(time.time()))
        remote = f"/sdcard/dash_{ts}.png"
        local = os.path.join(self.PROJECT_ROOT, "screenshots", f"dash_{ts}.png")
        self.adb_shell(f"screencap -p {remote}")
        self.adb(["pull", remote, local])
        self.adb_shell(f"rm {remote}")
        return f"Screenshot saved: {local}" if os.path.exists(local) else "Failed"

    def run(self) -> None:
        """Start web dashboard."""
        print(f"\n  === WEB DASHBOARD ===")
        print(f"  Starting on http://localhost:{self.port}")
        print(f"  Press Ctrl+C to stop")

        handler = self._make_handler()
        self._server = HTTPServer(("0.0.0.0", self.port), handler)
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            self.log("Dashboard stopped")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            self.log("Dashboard already running")
            return
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
        self.log(f"Dashboard started on port {self.port}")

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
        self.log("Dashboard stopped")

    def shutdown(self) -> None:
        self.log("Shutting down Web Dashboard")
        self.stop()


def register() -> dict[str, Any]:
    plugin = WebDashboardPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
