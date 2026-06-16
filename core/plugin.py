"""MEGASUS Plugin System - Base class and loader."""
import os
import json
import importlib.util
import sys
import logging
from pathlib import Path

PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
logger = logging.getLogger("core.plugin")


class Plugin:
    """Base class for all MEGASUS plugins."""

    name = "base"
    version = "1.0.0"
    author = "MEGASUS"
    description = "Base plugin"

    def __init__(self) -> None:
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.PLUGIN_DIR = Path(__file__).parent
        self.config = {}
        self.log(self.name + " instance created")

    def initialize(self) -> None:
        """Called when plugin is loaded."""
        pass

    def shutdown(self) -> None:
        """Called when plugin is unloaded."""
        pass

    def run(self) -> None:
        """Main plugin loop (override in subclass)."""
        pass

    def log(self, msg: str) -> None:
        """Log a message."""
        logger.info(self.name + ": " + msg)

    def adb(self, cmd: list, timeout: int = 30):
        """Run an ADB command."""
        from core.engine import _run
        return _run(cmd, timeout=timeout)

    def adb_shell(self, cmd: str, timeout: int = 30) -> str:
        """Run a shell command on device."""
        out, err, rc = self.adb(["shell", cmd], timeout=timeout)
        return out


"""MEGASUS Plugin Loader - Drop-in module system with subfolder support."""
import os
import json
import importlib.util
import sys
from pathlib import Path

PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")


def load_plugins():
    """Load plugins from flat .py files and subfolder manifest.json entries."""
    plugins = {}
    if not os.path.isdir(PLUGINS_DIR):
        return plugins

    # Load flat .py files (legacy)
    for fname in sorted(os.listdir(PLUGINS_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        fpath = os.path.join(PLUGINS_DIR, fname)
        if os.path.isfile(fpath):
            _load_plugin_file(fpath, fname, plugins)

    # Load subfolder plugins (new)
    for item in sorted(os.listdir(PLUGINS_DIR)):
        plugin_dir = os.path.join(PLUGINS_DIR, item)
        if not os.path.isdir(plugin_dir):
            continue
        manifest_path = os.path.join(plugin_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            continue
        try:
            with open(manifest_path) as mf:
                manifest = json.load(mf)
            if not manifest.get("enabled", True):
                continue
            entry = manifest.get("entry", "plugin.py")
            entry_path = os.path.join(plugin_dir, entry)
            if os.path.exists(entry_path):
                _load_plugin_file(entry_path, item, plugins, manifest=manifest)
        except Exception as e:
            plugins[item] = {"error": str(e), "file": manifest_path}

    return plugins


def _load_plugin_file(fpath, name, plugins, manifest=None):
    """Load a single plugin file."""
    mod_name = "plugins." + name
    plugin_dir = os.path.dirname(fpath)
    if plugin_dir not in sys.path:
        sys.path.insert(0, plugin_dir)
    try:
        spec = importlib.util.spec_from_file_location(mod_name, fpath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "register"):
            info = mod.register()
            if manifest:
                info.update(manifest)
            plugins[info.get("name", name)] = {"module": mod, "info": info, "file": fpath}
    except Exception as e:
        plugins[name] = {"error": str(e), "file": fpath}


def list_plugins():
    """List available plugins."""
    return load_plugins()
