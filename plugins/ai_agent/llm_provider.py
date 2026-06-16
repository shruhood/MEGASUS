"""MEGASUS AI Agent v2 — LLM Provider Bridge.

Supports 7 providers:
  - OpenRouter (multi-model gateway)
  - OpenAI (ChatGPT / GPT-4o)
  - Google Gemini
  - Anthropic Claude
  - Hermes (Nous Research — local gateway)
  - OpenClaw (local gateway)
  - Claude Code (Anthropic — local CLI)

Provider selection priority:
  1. Per-plugin config.json (runtime-editable via agent menu)
  2. Global config.yaml llm section
  3. Environment variables
"""
from __future__ import annotations
import os
import json
import logging
import urllib.request
import urllib.error
import subprocess
from typing import Optional

logger = logging.getLogger("ai_agent.llm")

# ── Provider configs ─────────────────────────────────────────

PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": "openrouter/owl-alpha",
        "models": [
            "openrouter/owl-alpha",
            "openrouter/auto",
            "anthropic/claude-sonnet-4-20250514",
            "google/gemini-2.5-flash",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "deepseek/deepseek-chat",
            "meta-llama/llama-4-maverick",
        ],
        "type": "api",
    },
    "openai": {
        "name": "OpenAI (ChatGPT)",
        "url": "https://api.openai.com/v1/chat/completions",
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini", "o3"],
        "type": "api",
    },
    "gemini": {
        "name": "Google Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.5-flash",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ],
        "type": "api",
    },
    "claude": {
        "name": "Anthropic Claude (API)",
        "url": "https://api.anthropic.com/v1/messages",
        "key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-20250514",
        "models": [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-haiku-4-20250514",
            "claude-3-5-sonnet-20241022",
        ],
        "type": "api",
    },
    "hermes": {
        "name": "Hermes (Nous Research)",
        "url": "http://localhost:11434/v1/chat/completions",
        "key_env": "",
        "default_model": "hermes-4-technical",
        "models": [
            "hermes-4-technical",
            "hermes-4",
            "hermes-3",
            "hermes-2-pro",
            "hermes-2",
            "hermes-1",
        ],
        "type": "local",
        "health_check": "http://localhost:11434/health",
        "setup_hint": "Run: hermes gateway start  (or install from hermes-agent.nousresearch.com)",
    },
    "openclaw": {
        "name": "OpenClaw (Local Gateway)",
        "url": "http://localhost:3000/v1/chat/completions",
        "key_env": "",
        "default_model": "openclaw-default",
        "models": ["openclaw-default", "openclaw-sonnet", "openclaw-opus"],
        "type": "local",
        "health_check": "http://localhost:3000/health",
        "setup_hint": "Run: openclaw gateway start  (or install from openclaw.dev)",
    },
    "claude-code": {
        "name": "Claude Code (Local CLI)",
        "url": "",
        "key_env": "",
        "default_model": "claude-sonnet-4-20250514",
        "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        "type": "cli",
        "setup_hint": "Install: npm install -g @anthropic-ai/claude-code",
    },
}


class LLMProvider:
    """Unified LLM API caller. Selects provider, sends request, returns response."""

    def __init__(self, provider: str = "", api_key: str = "", model: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self._load_from_env()

    def _load_from_env(self):
        """Fall back to env vars if no explicit key."""
        p = PROVIDERS.get(self.provider, {})
        if not self.api_key and p.get("key_env"):
            self.api_key = os.environ.get(p["key_env"], "")
        if not self.model and p:
            self.model = p.get("default_model", "")

    def _is_configured(self) -> bool:
        if self.provider not in PROVIDERS:
            return False
        p = PROVIDERS[self.provider]
        if p.get("type") == "api":
            return bool(self.api_key)
        if p.get("type") in ("local", "cli"):
            return True  # will check health at call time
        return bool(self.api_key)

    def is_local(self) -> bool:
        p = PROVIDERS.get(self.provider, {})
        return p.get("type") in ("local", "cli")

    def chat(self, user_message: str, system_prompt: str = "",
             max_tokens: int = 500) -> tuple[str, str]:
        """Send a chat message. Returns (response_text, error)."""
        if not self._is_configured():
            return "", "No LLM provider configured. Use 'llm setup' in agent menu."

        if self.provider == "openrouter":
            return self._chat_openrouter(user_message, system_prompt, max_tokens)
        elif self.provider == "openai":
            return self._chat_openai(user_message, system_prompt, max_tokens)
        elif self.provider == "gemini":
            return self._chat_gemini(user_message, system_prompt, max_tokens)
        elif self.provider == "claude":
            return self._chat_claude(user_message, system_prompt, max_tokens)
        elif self.provider == "hermes":
            return self._chat_hermes(user_message, system_prompt, max_tokens)
        elif self.provider == "openclaw":
            return self._chat_openclaw(user_message, system_prompt, max_tokens)
        elif self.provider == "claude-code":
            return self._chat_claude_code(user_message, system_prompt, max_tokens)
        return "", f"Unknown provider: {self.provider}"

    # ── OpenRouter ─────────────────────────────────────────────

    def _chat_openrouter(self, user_msg: str, system: str, max_tokens: int) -> tuple[str, str]:
        url = PROVIDERS["openrouter"]["url"]
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_msg})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://megasus.local",
            "X-Title": "MEGASUS AI Agent",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"], ""
        except Exception as e:
            return "", f"OpenRouter error: {e}"

    # ── OpenAI ─────────────────────────────────────────────────

    def _chat_openai(self, user_msg: str, system: str, max_tokens: int) -> tuple[str, str]:
        url = PROVIDERS["openai"]["url"]
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_msg})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"], ""
        except Exception as e:
            return "", f"OpenAI error: {e}"

    # ── Gemini ─────────────────────────────────────────────────

    def _chat_gemini(self, user_msg: str, system: str, max_tokens: int) -> tuple[str, str]:
        model = self.model
        url = PROVIDERS["gemini"]["url"].format(model=model) + f"?key={self.api_key}"

        parts = []
        if system:
            parts.append({"text": system})
        parts.append({"text": user_msg})

        payload = json.dumps({
            "contents": [{"parts": parts}],
            "generationConfig": {"maxOutputTokens": max_tokens},
        }).encode()

        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text, ""
        except Exception as e:
            return "", f"Gemini error: {e}"

    # ── Claude API ──────────────────────────────────────────────

    def _chat_claude(self, user_msg: str, system: str, max_tokens: int) -> tuple[str, str]:
        url = PROVIDERS["claude"]["url"]
        messages = [{"role": "user", "content": user_msg}]

        req_headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-dangerous-direct-browser-access": "true",
        }
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            body["system"] = system

        payload = json.dumps(body).encode()
        req = urllib.request.Request(url, data=payload, headers=req_headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data["content"][0]["text"], ""
        except Exception as e:
            return "", f"Claude error: {e}"

    # ── Hermes (Nous Research) ──────────────────────────────────

    def _chat_hermes(self, user_msg: str, system: str, max_tokens: int) -> tuple[str, str]:
        """Connect to Hermes local gateway (OpenAI-compatible /v1/chat/completions)."""
        url = PROVIDERS["hermes"]["url"]
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_msg})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"], ""
        except Exception as e:
            return "", f"Hermes error: {e} — is the gateway running? {PROVIDERS['hermes']['setup_hint']}"

    # ── OpenClaw ───────────────────────────────────────────────

    def _chat_openclaw(self, user_msg: str, system: str, max_tokens: int) -> tuple[str, str]:
        """Connect to OpenClaw local gateway (OpenAI-compatible)."""
        url = PROVIDERS["openclaw"]["url"]
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_msg})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }).encode()

        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"], ""
        except Exception as e:
            return "", f"OpenClaw error: {e} — is the gateway running? {PROVIDERS['openclaw']['setup_hint']}"

    # ── Claude Code (CLI) ───────────────────────────────────────

    def _chat_claude_code(self, user_msg: str, system: str, max_tokens: int) -> tuple[str, str]:
        """Call Claude Code CLI via subprocess."""
        try:
            cmd = ["claude", "--print", "--no-stream"]
            if system:
                cmd.extend(["--system-prompt", system])
            cmd.append(user_msg)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return result.stdout.strip(), ""
            return "", f"Claude Code error: {result.stderr[:300]}"
        except FileNotFoundError:
            return "", f"Claude Code CLI not found. {PROVIDERS['claude-code']['setup_hint']}"
        except subprocess.TimeoutExpired:
            return "", "Claude Code timed out (60s limit)"
        except Exception as e:
            return "", f"Claude Code error: {e}"

    # ── Helpers ────────────────────────────────────────────────

    def health_check(self) -> tuple[bool, str]:
        """Quick connectivity test."""
        if not self._is_configured():
            return False, "Not configured"

        p = PROVIDERS.get(self.provider, {})
        ptype = p.get("type", "api")

        if ptype == "local" and p.get("health_check"):
            try:
                req = urllib.request.Request(p["health_check"])
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return True, f"{p['name']} is running"
            except Exception:
                return False, f"{p['name']} not reachable — {p.get('setup_hint', '')}"

        if ptype == "cli":
            try:
                result = subprocess.run(
                    ["claude", "--version"] if self.provider == "claude-code" else ["echo", "ok"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    return True, f"{p['name']} CLI found"
                return False, f"{p['name']} CLI returned error"
            except FileNotFoundError:
                return False, f"{p['name']} CLI not installed — {p.get('setup_hint', '')}"

        # API type — try a minimal request
        text, err = self.chat("Say 'ok'.", max_tokens=10)
        if err:
            return False, err
        return True, f"{p['name']} connected — {text[:50]}"

    @staticmethod
    def test_key(provider: str, api_key: str, model: str = "") -> tuple[bool, str]:
        """Quick test if an API key works."""
        ll = LLMProvider(provider, api_key, model)
        return ll.health_check()

    @staticmethod
    def list_providers() -> list[dict]:
        result = []
        for pid, p in PROVIDERS.items():
            has_key = True
            if p.get("key_env"):
                has_key = bool(os.environ.get(p["key_env"], ""))
            elif p.get("type") == "local":
                # Check if local gateway is reachable
                hc = p.get("health_check", "")
                if hc:
                    try:
                        req = urllib.request.Request(hc)
                        with urllib.request.urlopen(req, timeout=2) as resp:
                            has_key = True
                    except Exception:
                        has_key = False
                else:
                    has_key = False
            elif p.get("type") == "cli":
                try:
                    subprocess.run(["claude", "--version"], capture_output=True, timeout=5)
                    has_key = True
                except Exception:
                    has_key = False

            result.append({
                "id": pid,
                "name": p["name"],
                "type": p.get("type", "api"),
                "default_model": p.get("default_model", ""),
                "models": p.get("models", []),
                "key_env": p.get("key_env", ""),
                "has_key": has_key,
                "setup_hint": p.get("setup_hint", ""),
            })
        return result
