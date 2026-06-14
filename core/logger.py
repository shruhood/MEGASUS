"""MEGASUS Audit Logger"""
import os
from datetime import datetime

from core.engine import CONFIG

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def log(event_type, message, user="system"):
    """Write to audit log"""
    if not CONFIG.get("logging", {}).get("enabled", True):
        return
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(LOG_DIR, f"megasus_{datetime.now().strftime('%Y%m%d')}.log")
    entry = f"[{ts}] [{user}] [{event_type}] {message}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


def get_logs(date=None, lines=100):
    """Read recent log entries"""
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(LOG_DIR, f"megasus_{date}.log")
    if not os.path.exists(log_file):
        return []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        return all_lines[-lines:]
    except Exception:
        return []
