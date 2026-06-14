"""MEGASUS Plugin Loader - Drop-in module system"""
import os
import importlib.util
import sys

PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")


def load_plugins():
    """Load all .py files from plugins/ directory"""
    plugins = {}
    if not os.path.isdir(PLUGINS_DIR):
        return plugins
    for fname in sorted(os.listdir(PLUGINS_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        fpath = os.path.join(PLUGINS_DIR, fname)
        mod_name = f"plugins.{fname[:-3]}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, fpath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "register"):
                info = mod.register()
                plugins[info.get("name", fname[:-3])] = {
                    "module": mod,
                    "info": info,
                    "file": fname,
                }
        except Exception as e:
            plugins[fname[:-3]] = {"error": str(e), "file": fname}
    return plugins


def list_plugins():
    """List available plugins"""
    return load_plugins()
