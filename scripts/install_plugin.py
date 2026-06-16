"""MEGASUS Plugin Installer - Install plugins from ZIP packages."""
import os, sys, json, zipfile, shutil, argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
PLUGINS_DIR = PROJECT_ROOT / "plugins"


def validate_plugin(d):
    mp = d / "manifest.json"
    if not mp.exists():
        print("ERROR: manifest.json not found"); return False
    with open(mp) as f: m = json.load(f)
    for k in ("name", "version", "entry"):
        if k not in m: print("ERROR: missing", k); return False
    if not (d / m["entry"]).exists():
        print("ERROR: entry not found:", m["entry"]); return False
    return True


def install_from_zip(zp):
    zp = Path(zp)
    if not zp.exists(): print("ERROR: not found:", zp); return False
    tmp = PROJECT_ROOT / "_ptmp"
    if tmp.exists(): shutil.rmtree(tmp)
    with zipfile.ZipFile(str(zp), "r") as z: z.extractall(str(tmp))
    if not validate_plugin(tmp): shutil.rmtree(tmp); return False
    with open(tmp / "manifest.json") as f: name = json.load(f)["name"]
    dest = PLUGINS_DIR / name
    if dest.exists(): shutil.rmtree(dest)
    shutil.move(str(tmp), str(dest))
    print("Installed:", name); return True


def install_from_dir(src):
    src = Path(src)
    if not validate_plugin(src): return False
    with open(src / "manifest.json") as f: name = json.load(f)["name"]
    dest = PLUGINS_DIR / name
    if dest.exists(): shutil.rmtree(dest)
    shutil.copytree(str(src), str(dest))
    print("Installed:", name); return True


def list_plugins():
    for d in sorted(PLUGINS_DIR.iterdir()):
        mp = d / "manifest.json"
        if d.is_dir() and mp.exists():
            with open(mp) as f: m = json.load(f)
            print("  %s v%s (%s)" % (m.get("name","?"), m.get("version","?"),
                  "enabled" if m.get("enabled",True) else "disabled"))


def main():
    p = argparse.ArgumentParser(description="MEGASUS Plugin Installer")
    p.add_argument("action", choices=["install", "list"])
    p.add_argument("source", nargs="?")
    args = p.parse_args()
    if args.action == "list":
        list_plugins()
    elif args.action == "install":
        if not args.source: print("ERROR: provide ZIP or dir"); sys.exit(1)
        src = Path(args.source)
        if src.suffix == ".zip" and src.is_file():
            ok = install_from_zip(src)
        elif src.is_dir():
            ok = install_from_dir(src)
        else:
            print("ERROR: must be ZIP or dir"); sys.exit(1)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
