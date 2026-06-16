#!/usr/bin/env python3
"""MEGASUS Master Installer - Cross-platform installation script."""
import os, sys, platform, subprocess, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("install")
ROOT = Path(__file__).parent.resolve()


def check_python():
    ver = sys.version_info
    log.info("Python %d.%d.%d", ver.major, ver.minor, ver.micro)
    if ver < (3, 8):
        log.error("Python 3.8+ required")
        return False
    return True


def install_dependencies():
    reqs = ROOT / "requirements.txt"
    if not reqs.exists():
        return True
    log.info("Installing Python dependencies...")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(reqs)],
                       capture_output=True, text=True, timeout=300)
    return r.returncode == 0


def install_platform_tools():
    log.info("Installing Android Platform Tools...")
    sys.path.insert(0, str(ROOT))
    from scripts.platform_tools import PlatformToolsInstaller
    inst = PlatformToolsInstaller(str(ROOT))
    if inst.install():
        inst.update_config_yaml()
        return True
    return False


def verify():
    tools = ROOT / "core" / "platform-tools"
    adb = tools / ("adb.exe" if platform.system() == "Windows" else "adb")
    if not adb.exists():
        log.error("ADB not found")
        return False
    r = subprocess.run([str(adb), "version"], capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        log.info("ADB OK: %s", r.stdout.strip().splitlines()[0])
        return True
    return False


def main():
    print("\n" + "=" * 50)
    print("  MEGASUS Installer  |  %s (%s)" % (platform.system(), platform.machine()))
    print("=" * 50 + "\n")
    for name, fn in [("Python check", check_python), ("Dependencies", install_dependencies),
                     ("Platform tools", install_platform_tools), ("Verify", verify)]:
        print("  [%s]" % name)
        try:
            if not fn():
                print("  FAILED:", name)
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n  Interrupted."); sys.exit(130)
        except Exception as e:
            print("  ERROR:", e); sys.exit(1)
        print()
    print("=" * 50)
    print("  Done! Run: python megasus.py")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
