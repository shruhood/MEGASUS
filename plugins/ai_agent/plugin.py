"""MEGASUS AI Agent Plugin — On-device AI via Termux for LLM inference and chat."""
from __future__ import annotations
import os
import json
import logging
import subprocess
from typing import Any, Optional

from core.plugin import Plugin

logger = logging.getLogger("ai_agent")


class AIAgentPlugin(Plugin):
    """On-device AI via Termux — Ollama, llama.cpp, and AI automation."""

    name = "ai_agent"
    version = "1.0.0"
    author = "MEGASUS"
    description = "On-device AI via Termux for LLM inference and chat"

    def __init__(self) -> None:
        super().__init__()
        self._termux_prefix = "/data/data/com.termux/files/usr"
        self._models_dir = f"{self._termux_prefix}/share/ollama/models"

    def _termux(self, cmd: str, timeout: int = 30) -> tuple[str, str, int]:
        """Run command in Termux environment."""
        full = f"su -c 'PATH={self._termux_prefix}/bin:$PATH {cmd}'"
        out, err, rc = self.adb_shell(full, timeout=timeout)
        return out, err, rc

    def check_termux(self) -> bool:
        """Check if Termux is installed."""
        out, _, rc = self.adb_shell("pm list packages | grep termux")
        return rc == 0 and "termux" in out.lower()

    def check_ollama(self) -> bool:
        """Check if Ollama is installed in Termux."""
        out, err, rc = self._termux("which ollama")
        return rc == 0 and "ollama" in out

    def install_ollama(self) -> bool:
        """Install Ollama in Termux."""
        self.log("Installing Ollama in Termux...")
        cmds = [
            "pkg update -y",
            "pkg install -y curl",
            "curl -fsSL https://ollama.com/install.sh | sh",
        ]
        for cmd in cmds:
            out, err, rc = self._termux(cmd, timeout=120)
            if rc != 0:
                self.log(f"Install step failed: {cmd} -> {err}")
                return False
        self.log("Ollama installed")
        return True

    def list_models(self) -> list[str]:
        """List available Ollama models."""
        out, err, rc = self._termux("ollama list")
        if rc == 0 and out:
            return [l.strip() for l in out.splitlines() if l.strip()]
        return []

    def pull_model(self, model: str) -> bool:
        """Pull an Ollama model."""
        self.log(f"Pulling model: {model}")
        out, err, rc = self._termux(f"ollama pull {model}", timeout=600)
        return rc == 0

    def chat(self, prompt: str, model: str = "llama3.2") -> str:
        """Run a chat completion."""
        out, err, rc = self._termux(
            f"ollama run {model} '{prompt}'", timeout=120
        )
        if rc == 0:
            return out
        return f"Error: {err}"

    def run_server(self) -> bool:
        """Start Ollama server in background."""
        out, err, rc = self._termux("ollama serve &")
        return rc == 0

    def stop_server(self) -> bool:
        """Stop Ollama server."""
        out, err, rc = self._termux("pkill ollama")
        return rc == 0

    def run(self) -> None:
        """Interactive AI menu."""
        print("\n  === AI AGENT ===")
        print("  1. Check Termux installation")
        print("  2. Install Ollama")
        print("  3. List models")
        print("  4. Pull model")
        print("  5. Chat with model")
        print("  6. Start Ollama server")
        print("  7. Stop Ollama server")
        print("  0. Back")

        choice = input("\n  Choice: ").strip()
        if choice == "0":
            return
        elif choice == "1":
            if self.check_termux():
                print("  Termux: INSTALLED")
            else:
                print("  Termux: NOT FOUND — install from F-Droid")
        elif choice == "2":
            if self.install_ollama():
                print("  Ollama installed")
            else:
                print("  Install failed")
        elif choice == "3":
            models = self.list_models()
            if models:
                for m in models:
                    print(f"  {m}")
            else:
                print("  No models — pull one first")
        elif choice == "4":
            model = input("  Model name [llama3.2]: ").strip() or "llama3.2"
            print(f"  Pulling {model}...")
            if self.pull_model(model):
                print("  Done")
            else:
                print("  Failed")
        elif choice == "5":
            model = input("  Model [llama3.2]: ").strip() or "llama3.2"
            prompt = input("  Prompt: ").strip()
            if prompt:
                print("  Thinking...")
                resp = self.chat(prompt, model)
                print(f"\n  {resp}")
        elif choice == "6":
            if self.run_server():
                print("  Server started")
            else:
                print("  Failed")
        elif choice == "7":
            if self.stop_server():
                print("  Server stopped")
            else:
                print("  Failed")

    def shutdown(self) -> None:
        self.log("Shutting down AI Agent plugin")


def register() -> dict[str, Any]:
    plugin = AIAgentPlugin()
    plugin.initialize()
    return {
        "name": plugin.name,
        "version": plugin.version,
        "author": plugin.author,
        "description": plugin.description,
        "plugin": plugin,
    }
