"""MEGASUS Platform Tools Manager - Cross-platform ADB installer."""
import os, sys, hashlib, logging, platform, subprocess, shutil, time
from pathlib import Path
from urllib.request import urlopen, Request

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

log = logging.getLogger("platform_tools")

class PlatformToolsError(Exception):
    pass

class PlatformDetector:
    def __init__(self):
        self.system = platform.system()
        self.machine = platform.machine()
        self.is_termux = bool(os.environ.get("TERMUX_VERSION")) or \
                         Path("/data/data/com.termux/files/usr").exists()
    def get_platform(self):
        if self.is_termux: return "Termux"
        return self.system if self.system in ("Windows", "Linux", "Darwin") else None
    def get_adb_name(self):
        return "adb.exe" if self.system == "Windows" else "adb"

class Downloader:
    def __init__(self, retries=3, timeout=120):
        self.retries, self.timeout = retries, timeout
    def download(self, url, dest, sha256=None):
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        for i in range(1, self.retries + 1):
            try:
                log.info("Download attempt %d of %d", i, self.retries)
                self._dl(url, str(dest))
                if sha256: self._check(str(dest), sha256)
                return dest
            except Exception as e:
                log.warning("Attempt %d failed: %s", i, str(e))
                if i < self.retries: time.sleep(i * 5)
                else: raise PlatformToolsError("Download failed: " + str(e))
    def _dl(self, url, dest):
        if HAS_REQUESTS:
            r = requests.get(url, stream=True, timeout=self.timeout)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk); done += len(chunk); self._prog(done, total)
        else:
            req = Request(url, headers={"User-Agent": "MEGASUS/1.0"})
            r = urlopen(req, timeout=self.timeout)
            total = int(r.headers.get("Content-Length", 0))
            done = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(8192)
                    if not chunk: break
                    f.write(chunk); done += len(chunk); self._prog(done, total)
        print()
    def _prog(self, done, total):
        if total > 0:
            pct = min(done * 100 / total, 100)
            sys.stdout.write(chr(13) + "  " + str(round(pct, 1)) + "%  " +
                             str(round(done/1024/1024, 1)) + "/" +
                             str(round(total/1024/1024, 1)) + " MB  ")
            sys.stdout.flush()
    def _check(self, path, expected):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
        if h.hexdigest() != expected: raise PlatformToolsError("Checksum mismatch")

class PlatformToolsInstaller:
    URLS = {
        "Windows": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
        "Linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
        "Darwin": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
    }
    def __init__(self, root=None):
        self.root = Path(root) if root else Path.cwd()
        self.tools = self.root / "core" / "platform-tools"
        self.det = PlatformDetector()
        self.dl = Downloader()
        self.platform = self.det.get_platform()
        self.adb = self.det.get_adb_name()
    def is_installed(self):
        return self.tools.is_dir() and (self.tools / self.adb).exists()
    def verify_adb(self):
        ab = self.tools / self.adb
        if not ab.exists(): return False
        try:
            r = subprocess.run([str(ab), "version"], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                log.info("ADB: %s", r.stdout.strip().splitlines()[0])
                return True
        except Exception: pass
        return False
    def install(self):
        log.info("Platform: %s", self.platform)
        if not self.platform: raise PlatformToolsError("Unsupported platform")
        if self.is_installed() and self.verify_adb():
            log.info("Already installed."); return True
        if self.platform == "Termux": return self._termux()
        return self._zip()
    def _termux(self):
        log.info("Installing via Termux pkg...")
        try:
            r = subprocess.run(["pkg", "install", "android-tools", "-y"],
                               capture_output=True, text=True, timeout=180)
            log.info("pkg rc=%d", r.returncode)
            if r.stdout: log.info("stdout: %s", r.stdout[:200])
            if r.stderr: log.info("stderr: %s", r.stderr[:200])
        except FileNotFoundError:
            log.warning("pkg command not found")
        except subprocess.TimeoutExpired:
            log.warning("pkg timed out")
        adb_locs = []
        try:
            w = subprocess.run(["which", "adb"], capture_output=True, text=True, timeout=10)
            if w.returncode == 0 and w.stdout.strip():
                adb_locs.append(Path(w.stdout.strip()))
        except Exception: pass
        prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        for p in [Path(prefix) / "bin" / "adb",
                  Path("/data/data/com.termux/files/usr/bin/adb"),
                  Path("/usr/bin/adb"),
                  Path("/system/bin/adb")]:
            if p.exists(): adb_locs.append(p)
        if not adb_locs:
            log.warning("ADB not found. Run: pkg update && pkg install android-tools")
            return False
        src = adb_locs[0]
        log.info("Found ADB: %s", src)
        self.tools.mkdir(parents=True, exist_ok=True)
        dst = self.tools / "adb"
        if dst.exists(): dst.unlink()
        shutil.copy2(str(src), str(dst))
        for s in src.parent.iterdir():
            d = self.tools / s.name
            if not d.exists() and s.is_file():
                try: shutil.copy2(str(s), str(d))
                except OSError: pass
        for f in self.tools.iterdir():
            if f.is_file():
                try: f.chmod(0o755)
                except OSError: pass
        return self.verify_adb()
    def _zip(self):
        url = self.URLS[self.platform]
        zp = self.root / "platform-tools.zip"
        try:
            self.dl.download(url, zp)
            self._extract(zp)
            zp.unlink(missing_ok=True)
            return self.verify_adb()
        except Exception:
            zp.unlink(missing_ok=True); raise
    def _extract(self, zp):
        import zipfile
        tmp = self.root / "_ptmp"
        if tmp.exists(): shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        with zipfile.ZipFile(str(zp), "r") as z: z.extractall(str(tmp))
        ext = tmp / "platform-tools"
        if not ext.exists(): ext = tmp
        if self.tools.exists(): shutil.rmtree(self.tools)
        shutil.move(str(ext), str(self.tools))
        shutil.rmtree(tmp, ignore_errors=True)
        if self.platform != "Windows":
            for f in self.tools.iterdir():
                if f.is_file():
                    try: f.chmod(0o755)
                    except OSError: pass
    def update_config(self):
        import yaml
        cp = self.root / "config.yaml"
        cfg = {}
        if cp.exists():
            with open(cp) as f: cfg = yaml.safe_load(f) or {}
        cfg.setdefault("adb", {})["path"] = "core/platform-tools"
        cfg["adb"]["auto_start_server"] = True
        with open(cp, "w") as f: yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

def install_platform_tools(root=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    inst = PlatformToolsInstaller(root)
    ok = inst.install()
    if ok: inst.update_config()
    return ok
