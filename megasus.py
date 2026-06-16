"""
MEGASUS - Ultimate Android Device Control Toolkit
Main entry point - Interactive menu system

Author: Suraj Singh (@shruhood)
Organizations: Bakweb, SunDial Technologies, Cyber SunDial
Emails: shruhood@gmail.com, hello@bakeweb.in, ibakeweb@gmail.com
Website: https://bakeweb.in
GitHub: https://github.com/shruhood/MEGASUS
WhatsApp: https://whatsapp.com/channel/0029Vb7eYJP5PO0vRy786z46
"""
import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import Fore, Style, init
init(autoreset=True)

from core.engine import (
    DeviceManager, check_adb, check_device_connected,
    human_size, _run_shell, _run
)
from core.auth import AuthManager, ROLES
from core.logger import log, get_logs
from core.plugin import load_plugins, list_plugins
from modules import device, apps, files, connection
from modules import data, screen, network, security, surveillance, automation


# ── Banner ──────────────────────────────────────────────────────
BANNER = f"""
{Fore.RED}╔══════════════════════════════════════════════════════════╗
{Fore.RED}║  {Fore.WHITE}███╗   ███╗███████╗ ██████╗  █████╗ ███████╗██╗   ██╗███████╗{Fore.RED}  ║
{Fore.RED}║  {Fore.WHITE}████╗ ║████║██╔════╝██╔════╝ ██╔══██╗██╔════╝██║   ██║██╔════╝{Fore.RED}  ║
{Fore.RED}║  {Fore.WHITE}██╔████╔██║█████╗  ██║  ███╗███████║███████╗██║   ██║███████╗{Fore.RED}  ║
{Fore.RED}║  {Fore.WHITE}██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║╚════██║██║   ██║╚════██║{Fore.RED}  ║
{Fore.RED}║  {Fore.WHITE}██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║███████║╚██████╔╝███████║{Fore.RED}  ║
{Fore.RED}║  {Fore.WHITE}╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝{Fore.RED}  ║
{Fore.RED}║                                          {Fore.YELLOW}v1.0 PRO{Fore.RED}           ║
{Fore.RED}║  {Fore.WHITE}Ultimate Android Device Control & Security Toolkit{Fore.RED}      ║
{Fore.RED}╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

device_mgr = DeviceManager()
auth_mgr = AuthManager()
session_token = None


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input(f"\n{Fore.YELLOW}[Press Enter to continue...]{Style.RESET_ALL}")


def print_header(title):
    print(f"\n{Fore.CYAN}{'═' * 55}")
    print(f"  {Fore.WHITE}{Style.BRIGHT}{title}")
    print(f"{Fore.CYAN}{'═' * 55}{Style.RESET_ALL}")


def print_menu(options):
    for key, desc in options.items():
        print(f"  {Fore.GREEN}[{key}]{Style.RESET_ALL} {desc}")
    print()


def print_result(success, message):
    icon = f"{Fore.GREEN}[OK]" if success else f"{Fore.RED}[FAIL]"
    print(f"  {icon} {message}{Style.RESET_ALL}")


def print_table(headers, rows):
    """Simple table printer"""
    if not rows:
        print(f"  {Fore.YELLOW}(no data){Style.RESET_ALL}")
        return
    # Calculate widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    # Print header
    header_line = "  ".join(f"{h:<{widths[i]}}" for i, h in enumerate(headers))
    print(f"  {Fore.CYAN}{header_line}{Style.RESET_ALL}")
    print(f"  {'─' * (sum(widths) + 2 * (len(widths) - 1))}")
    # Print rows
    for row in rows:
        row_line = "  ".join(f"{str(cell):<{widths[i]}}" if i < len(widths) else str(cell) for i, cell in enumerate(row))
        print(f"  {row_line}")


# ── Auth ────────────────────────────────────────────────────────
def login():
    global session_token
    print(f"\n{Fore.RED}{'═' * 40}")
    print(f"  🔐 MEGASUS AUTHENTICATION")
    print(f"{'═' * 40}{Style.RESET_ALL}")
    print(f"\n  Default: admin / megasus2026")
    print(f"  Default: operator / operator2026\n")

    username = input(f"  {Fore.YELLOW}Username: {Style.RESET_ALL}").strip()
    password = input(f"  {Fore.YELLOW}Password: {Style.RESET_ALL}").strip()

    session, msg = auth_mgr.authenticate(username, password)
    if session:
        session_token = session.token
        log("LOGIN", f"User '{username}' logged in as {session.role}", username)
        print(f"\n  {Fore.GREEN}[OK] Welcome {username}! Role: {session.role}{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}[OK] Session token: {session.token[:16]}...{Style.RESET_ALL}")
        time.sleep(1)
        return True
    else:
        print(f"\n  {Fore.RED}[FAIL] {msg}{Style.RESET_ALL}")
        time.sleep(2)
        return False


# ── Module Menu Functions ──────────────────────────────────────
def menu_connection():
    """Connection Manager Menu"""
    while True:
        print_header(f"{connection.MODULE_ICON} CONNECTION MANAGER")
        devices = device_mgr.list_devices()
        active = device_mgr.get_active()

        print(f"  Active device: {Fore.GREEN if active else Fore.RED}{active or 'NONE'}{Style.RESET_ALL}")
        print(f"  Connected: {len(devices)} device(s)\n")

        for serial, info in devices.items():
            status_color = Fore.GREEN if info["status"] == "device" else Fore.RED
            active_marker = f" {Fore.YELLOW}[ACTIVE]{Style.RESET_ALL}" if serial == active else ""
            print(f"  {status_color}● {serial}{Style.RESET_ALL} - {info.get('model', '?')} "
                  f"(Android {info.get('device', '?')}){active_marker}")

        print()
        print_menu({
            "1": "Refresh device list",
            "2": "Set active device",
            "3": "Connect wireless (WiFi ADB)",
            "4": "Disconnect device",
            "5": "Switch to TCP/IP mode (USB→WiFi)",
            "6": "Switch back to USB mode",
            "7": "Restart ADB server",
            "8": "Troubleshoot",
            "9": "List all with details",
            "0": "Back to main menu",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "1":
            device_mgr._refresh()
        elif choice == "2":
            serial = input("  Enter device serial: ").strip()
            if device_mgr.set_active(serial):
                print_result(True, f"Active device: {serial}")
            else:
                print_result(False, "Device not found")
            pause()
        elif choice == "3":
            ip = input("  Enter device IP: ").strip()
            port = input("  Port [5555]: ").strip() or "5555"
            ok, msg = connection.connect_wireless(device_mgr, ip, int(port))
            print_result(ok, msg)
            pause()
        elif choice == "4":
            serial = input("  Serial (Enter=all): ").strip() or None
            ok, msg = connection.disconnect_device(device_mgr, serial)
            print_result(ok, msg)
            pause()
        elif choice == "5":
            port = input("  Port [5555]: ").strip() or "5555"
            ok, msg = connection.tcpip_mode(device_mgr, int(port))
            print_result(ok, msg)
            pause()
        elif choice == "6":
            ok, msg = connection.usb_mode(device_mgr)
            print_result(ok, msg)
            pause()
        elif choice == "7":
            ok, msg = connection.restart_adb_server(device_mgr)
            print_result(ok, "ADB server restarted")
            pause()
        elif choice == "8":
            results = connection.troubleshoot(device_mgr)
            for r in results:
                print(f"  {r}")
            pause()
        elif choice == "9":
            all_devs = connection.list_all(device_mgr)
            for d in all_devs:
                print(f"  {Fore.CYAN}{d['serial']}{Style.RESET_ALL}")
                for k, v in d.items():
                    if k != "serial":
                        print(f"    {k}: {v}")
            pause()
        elif choice == "0":
            break


def menu_device():
    """Device Info & Control Menu"""
    while True:
        print_header(f"{device.MODULE_ICON} DEVICE INFO & CONTROL")

        # Quick status
        devices = device_mgr.list_devices()
        active = device_mgr.get_active()
        if not active:
            print(f"  {Fore.RED}No active device! Go to Connection menu first.{Style.RESET_ALL}")
            pause()
            break

        info, msg = device.get_device_info(device_mgr)
        if info and active in info:
            summary = info[active].get("summary", {})
            battery = info[active].get("battery", {})
            print(f"  Model: {Fore.GREEN}{summary.get('Model', '?')} ({summary.get('Brand', '?')}){Style.RESET_ALL}")
            print(f"  Android: {summary.get('AndroidVersion', '?')} | SDK: {summary.get('SDK Level', '?')}")
            print(f"  Build: {summary.get('Build', '?')} | Type: {summary.get('Build Type', '?')}")
            print(f"  Battery: {battery.get('level', '?')}% | Status: {battery.get('status', '?')} | Temp: {battery.get('temperature', '?')}C")
            print(f"  Screen: {info[active].get('screen_size', '?')} | {info[active].get('screen_density', '?')}")
            print(f"  SELinux: {info[active].get('selinux', '?')} | Uptime: {info[active].get('uptime', '?')}")
            print()

        print_menu({
            "1": "Full device information",
            "2": "Battery details",
            "3": "Storage usage",
            "4": "CPU info",
            "5": "RAM info",
            "6": "Screen info (resolution, density)",
            "7": "Reboot device",
            "8": "Reboot to recovery",
            "9": "Reboot to bootloader",
            "10": "Power off",
            "11": "Toggle WiFi",
            "12": "Toggle airplane mode",
            "13": "Set screen brightness",
            "14": "Set screen timeout",
            "15": "Change hostname",
            "16": "Dump build.prop to file",
            "17": "Get connected WiFi network",
            "18": "Get installed users/profiles",
            "19": "Full device dump (all info to files)",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice == "1":
            info, _ = device.get_device_info(device_mgr)
            if info and active in info:
                summary = info[active].get("summary", {})
                for k, v in summary.items():
                    print(f"  {Fore.CYAN}{k}:{Style.RESET_ALL} {v}")
                print(f"\n  {Fore.CYAN}Battery:{Style.RESET_ALL}")
                for k, v in info[active].get("battery", {}).items():
                    print(f"    {k}: {v}")
            pause()
        elif choice == "2":
            bat, _ = device.get_battery_info(device_mgr)
            if bat:
                for k, v in bat.items():
                    print(f"  {Fore.CYAN}{k}:{Style.RESET_ALL} {v}")
            pause()
        elif choice == "3":
            storage, _ = device.get_storage_info(device_mgr)
            if storage:
                for mount, info in storage.items():
                    print(f"  {Fore.CYAN}{mount}{Style.RESET_ALL}: {info['used']}/{info['size']} ({info['use_percent']})")
            pause()
        elif choice == "4":
            cpu, _ = device.get_cpu_info(device_mgr)
            if cpu:
                for k, v in list(cpu.items())[:15]:
                    print(f"  {Fore.CYAN}{k}:{Style.RESET_ALL} {v}")
            pause()
        elif choice == "5":
            ram, _ = device.get_ram_info(device_mgr)
            if ram:
                for k, v in ram.items():
                    print(f"  {Fore.CYAN}{k}:{Style.RESET_ALL} {v}")
            pause()
        elif choice == "6":
            info, _ = device.get_device_info(device_mgr)
            if info and active in info:
                print(f"  Screen: {info[active].get('screen_size', '?')}")
                print(f"  Density: {info[active].get('screen_density', '?')}")
            pause()
        elif choice == "7":
            ok, msg = device.reboot(device_mgr)
            print_result(ok, msg)
            pause()
        elif choice == "8":
            ok, msg = device.reboot(device_mgr, mode="recovery")
            print_result(ok, msg)
            pause()
        elif choice == "9":
            ok, msg = device.reboot(device_mgr, mode="bootloader")
            print_result(ok, msg)
            pause()
        elif choice == "10":
            confirm = input(f"  {Fore.RED}Confirm power off? (y/n): {Style.RESET_ALL}").strip()
            if confirm.lower() == "y":
                ok, msg = device.power_off(device_mgr)
                print_result(ok, msg)
            pause()
        elif choice == "11":
            action = input("  Enable or Disable? (e/d): ").strip().lower()
            ok, msg = device.toggle_wifi(device_mgr, enable=(action == "e"))
            print_result(ok, msg)
            pause()
        elif choice == "12":
            action = input("  Enable or Disable? (e/d): ").strip().lower()
            ok, msg = device.toggle_airplane(device_mgr, enable=(action == "e"))
            print_result(ok, msg)
            pause()
        elif choice == "13":
            level = input("  Brightness (0-255): ").strip()
            ok, msg = device.set_screen_brightness(device_mgr, int(level))
            print_result(ok, msg)
            pause()
        elif choice == "14":
            seconds = input("  Timeout (seconds): ").strip()
            ok, msg = device.set_screen_timeout(device_mgr, int(seconds))
            print_result(ok, msg)
            pause()
        elif choice == "15":
            hostname = input("  New hostname: ").strip()
            ok, msg = device.change_hostname(device_mgr, hostname)
            print_result(ok, msg)
            pause()
        elif choice == "16":
            ok, msg = device.dump_build_prop(device_mgr, output_file="build_prop_dump.txt")
            print_result(ok, msg)
            pause()
        elif choice == "17":
            wifi, _ = device.get_connected_wifi(device_mgr)
            print(f"  {wifi or 'Not connected'}")
            pause()
        elif choice == "18":
            users, _ = device.get_installed_users(device_mgr)
            print(f"  {users}")
            pause()
        elif choice == "19":
            # Delegate to surveillance module's full dump
            files_created, msg = surveillance.dump_device_info_full(device_mgr, output_dir="logs/dumps")
            print_result(len(files_created) > 0, msg)
            pause()


def menu_apps():
    """App Management Menu"""
    while True:
        print_header(f"{apps.MODULE_ICON} APP MANAGEMENT")
        print_menu({
            "1": "List all apps",
            "2": "List system apps",
            "3": "List third-party apps (user installed)",
            "4": "List disabled apps",
            "5": "App info & permissions",
            "6": "Install APK",
            "7": "Install all APKs from folder",
            "8": "Uninstall app",
            "9": "Force stop app",
            "10": "Start/launch app",
            "11": "Clear app data",
            "12": "Freeze app (disable)",
            "13": "Unfreeze app (enable)",
            "14": "Extract APK from device",
            "15": "Get dangerous permissions for app",
            "16": "Get running processes",
            "17": "Get current foreground app",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice in ("1", "2", "3", "4"):
            ft = {"1": "all", "2": "system", "3": "third_party", "4": "disabled"}[choice]
            app_list, msg = apps.list_apps(device_mgr, filter_type=ft)
            if app_list:
                for i, pkg in enumerate(app_list):
                    print(f"  {Fore.CYAN}{i+1:4d}.{Style.RESET_ALL} {pkg}")
                print(f"\n  Total: {len(app_list)} packages")
            else:
                print_result(False, msg)
            pause()
        elif choice == "5":
            pkg = input("  Package name: ").strip()
            info, msg = apps.get_app_info(device_mgr, pkg)
            if info:
                for k, v in info.items():
                    if k == "permissions":
                        print(f"  {Fore.CYAN}Permissions ({len(v)}):{Style.RESET_ALL}")
                        for p in v:
                            print(f"    {p}")
                    else:
                        print(f"  {Fore.CYAN}{k}:{Style.RESET_ALL} {v}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "6":
            path = input("  APK file path: ").strip().strip('"')
            ok, msg = apps.install_apk(device_mgr, path)
            print_result(ok, msg)
            pause()
        elif choice == "7":
            d = input("  APK folder path: ").strip().strip('"')
            results, msg = apps.install_multiple(device_mgr, d)
            if results:
                for r in results:
                    icon = "OK" if r["success"] else "FAIL"
                    print(f"  [{icon}] {r['file']}: {r['message']}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "8":
            pkg = input("  Package name: ").strip()
            ok, msg = apps.uninstall_app(device_mgr, pkg)
            print_result(ok, msg)
            pause()
        elif choice == "9":
            pkg = input("  Package name: ").strip()
            ok, msg = apps.force_stop(device_mgr, pkg)
            print_result(ok, msg)
            pause()
        elif choice == "10":
            pkg = input("  Package name: ").strip()
            ok, msg = apps.start_app(device_mgr, pkg)
            print_result(ok, msg)
            pause()
        elif choice == "11":
            pkg = input("  Package name: ").strip()
            ok, msg = apps.clear_app_data(device_mgr, pkg)
            print_result(ok, msg)
            pause()
        elif choice == "12":
            pkg = input("  Package name: ").strip()
            ok, msg = apps.freeze_app(device_mgr, pkg)
            print_result(ok, msg)
            pause()
        elif choice == "13":
            pkg = input("  Package name: ").strip()
            ok, msg = apps.unfreeze_app(device_mgr, pkg)
            print_result(ok, msg)
            pause()
        elif choice == "14":
            pkg = input("  Package name: ").strip()
            ok, msg = apps.extract_apk(device_mgr, pkg, output_dir=".")
            print_result(ok, msg)
            pause()
        elif choice == "15":
            pkg = input("  Package name: ").strip()
            perms, msg = apps.get_app_permissions(device_mgr, pkg)
            if perms:
                for p in perms:
                    print(f"  {p}")
            else:
                print_result(False, msg or "No dangerous permissions found")
            pause()
        elif choice == "16":
            stdout, msg = apps.get_running_apps(device_mgr)
            if stdout:
                lines = stdout.splitlines()
                print(f"  {'PID':<8} {'USER':<12} {'NAME'}")
                print(f"  {'─' * 50}")
                for line in lines[:50]:
                    parts = line.split(None, 4)
                    if len(parts) >= 3:
                        print(f"  {parts[0]:<8} {parts[1]:<2} {parts[2]}")
                if len(lines) > 50:
                    print(f"  ... and {len(lines) - 50} more")
            pause()
        elif choice == "17":
            stdout, _ = apps.get_top_activity(device_mgr)
            print(f"  Current: {stdout or 'Unknown'}")
            pause()


def menu_files():
    """File Manager Menu"""
    current_path = "/sdcard"

    while True:
        print_header(f"{files.MODULE_ICON} FILE MANAGER")
        print(f"  Current: {Fore.CYAN}{current_path}{Style.RESET_ALL}\n")

        print_menu({
            "1": "Browse directory",
            "2": "Go to path",
            "3": "Go up (parent dir)",
            "4": "Push file (PC → Device)",
            "5": "Pull file (Device → PC)",
            "6": "Pull entire directory",
            "7": "Create directory",
            "8": "Delete file/directory",
            "9": "Search files by name",
            "10": "View file content (cat)",
            "11": "Disk usage",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice == "1":
            entries, path = files.browse(device_mgr, current_path)
            if entries is not None:
                for e in entries:
                    icon = "📁" if e["is_dir"] else "  "
                    name_color = Fore.CYAN if e["is_dir"] else Fore.WHITE
                    print(f"  {icon} {name_color}{e['name']}{Style.RESET_ALL} "
                          f"({e['size']}) {e['permissions']}")
            else:
                print_result(False, path)
            pause()
        elif choice == "2":
            p = input("  Path: ").strip()
            if p:
                current_path = p
        elif choice == "3":
            current_path = os.path.dirname(current_path.rstrip("/"))
            if not current_path:
                current_path = "/"
        elif choice == "4":
            local = input("  Local file path: ").strip().strip('"')
            remote = input(f"  Remote path [{current_path}/]: ").strip().strip('"')
            if not remote:
                remote = current_path + "/" + os.path.basename(local)
            ok, msg = files.push_file(device_mgr, local, remote)
            print_result(ok, msg)
            pause()
        elif choice == "5":
            remote = input("  Remote file path: ").strip().strip('"')
            local = input("  Local path (Enter=auto): ").strip().strip('"') or None
            ok, msg = files.pull_file(device_mgr, remote, local)
            print_result(ok, msg)
            pause()
        elif choice == "6":
            remote = input("  Remote dir: ").strip().strip('"')
            local = input("  Local dir (Enter=auto): ").strip().strip('"') or None
            ok, msg = files.pull_directory(device_mgr, remote, local)
            print_result(ok, msg)
            pause()
        elif choice == "7":
            name = input("  Directory name: ").strip()
            ok, msg = files.create_directory(device_mgr, current_path + "/" + name)
            print_result(ok, msg)
            pause()
        elif choice == "8":
            path = input("  Path to delete: ").strip().strip('"')
            confirm = input(f"  {Fore.RED}Confirm delete {path}? (y/n): {Style.RESET_ALL}")
            if confirm.lower() == "y":
                ok, msg = files.delete_file(device_mgr, path)
                print_result(ok, msg)
            pause()
        elif choice == "9":
            pattern = input("  Search pattern (e.g., *.jpg): ").strip()
            path = input(f"  Search in [{current_path}]: ").strip() or current_path
            results, msg = files.search_files(device_mgr, pattern, path)
            if results:
                for r in results[:50]:
                    print(f"  {r}")
                if len(results) > 50:
                    print(f"  ... and {len(results) - 50} more")
            else:
                print_result(False, msg)
            pause()
        elif choice == "10":
            path = input("  File path: ").strip().strip('"')
            content, msg = files.cat_file(device_mgr, path)
            if content:
                print(content[:2000])
                if len(content) > 2000:
                    print(f"\n  ... ({len(content)} chars total)")
            else:
                print_result(False, msg)
            pause()
        elif choice == "11":
            stdout, _ = files.get_disk_usage(device_mgr)
            print(stdout)
            pause()


def menu_data():
    """Data Extraction Menu"""
    while True:
        print_header(f"{data.MODULE_ICON} DATA EXTRACTION")
        print_menu({
            "1": "Extract contacts",
            "2": "Extract SMS messages",
            "3": "Extract call logs",
            "4": "Get clipboard content",
            "5": "Set clipboard content",
            "6": "Send SMS (via intent)",
            "7": "Make phone call (via intent)",
            "8": "Get media files list (photos, videos)",
            "9": "Get active notifications",
            "10": "Get registered accounts",
            "11": "Get WiFi passwords (root required)",
            "12": "Get Chrome browser history",
            "13": "Get cell tower location",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice == "1":
            out = input("  Output file (Enter=contacts.json): ").strip() or "contacts.json"
            contacts, msg = data.get_contacts(device_mgr, output_file=out)
            if contacts:
                for c in contacts[:20]:
                    name = c.get("display_name", c.get("name", "?"))
                    number = c.get("number", "?")
                    print(f"  {Fore.GREEN}{name}{Style.RESET_ALL}: {number}")
                print(f"\n  Total: {len(contacts)} contacts → {out}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "2":
            out = input("  Output file (Enter=sms.json): ").strip() or "sms.json"
            msgs, msg = data.get_sms(device_mgr, output_file=out)
            if msgs:
                for m in msgs[:20]:
                    addr = m.get("address", "?")
                    body = m.get("body", "")
                    typ = "IN" if m.get("type") == "1" else "OUT"
                    print(f"  [{typ}] {Fore.CYAN}{addr}{Style.RESET_ALL}: {body[:60]}")
                print(f"\n  Total: {len(msgs)} messages → {out}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "3":
            out = input("  Output file (Enter=calls.json): ").strip() or "calls.json"
            calls, msg = data.get_call_logs(device_mgr, output_file=out)
            if calls:
                for c in calls[:20]:
                    name = c.get("name", "?")
                    number = c.get("number", "?")
                    dur = c.get("duration", "?")
                    typ_map = {"1": "IN", "2": "OUT", "3": "MISSED"}
                    typ = typ_map.get(c.get("type", ""), "?")
                    print(f"  [{typ}] {Fore.CYAN}{number}{Style.RESET_ALL} ({name}) {dur}s")
                print(f"\n  Total: {len(calls)} calls → {out}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "4":
            clip, msg = data.get_clipboard(device_mgr)
            print(f"  Clipboard: {clip or '(empty or restricted)'}")
            pause()
        elif choice == "5":
            text = input("  Text: ").strip()
            ok, msg = data.set_clipboard(device_mgr, text)
            print_result(ok, msg)
            pause()
        elif choice == "6":
            number = input("  Phone number: ").strip()
            message = input("  Message: ").strip()
            ok, msg = data.send_sms(device_mgr, number, message)
            print_result(ok, msg)
            pause()
        elif choice == "7":
            number = input("  Phone number: ").strip()
            ok, msg = data.make_call(device_mgr, number)
            print_result(ok, msg)
            pause()
        elif choice == "8":
            mtype = input("  Type (photos/videos/audio/downloads/all) [all]: ").strip() or "all"
            files_list, msg = data.get_media_files(device_mgr, media_type=mtype)
            if files_list:
                for f in files_list[:30]:
                    print(f"  {f}")
                print(f"\n  Total: {len(files_list)} files")
            else:
                print_result(False, msg)
            pause()
        elif choice == "9":
            notifs, msg = data.get_notifications(device_mgr)
            print(f"  {notifs[:500] if notifs else 'None'}")
            pause()
        elif choice == "10":
            accounts, msg = data.get_accounts(device_mgr)
            print(f"  {accounts[:500] if accounts else 'None'}")
            pause()
        elif choice == "11":
            pwds, msg = data.get_wifi_passwords(device_mgr)
            if pwds:
                print(pwds[:1000])
            else:
                print_result(False, msg)
            pause()
        elif choice == "12":
            history, msg = data.get_browser_history(device_mgr)
            if history:
                for h in history[:30]:
                    print(f"  {Fore.CYAN}{h.get('url', '?')[:80]}{Style.RESET_ALL} - {h.get('title', '')[:40]}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "13":
            loc, msg = data.get_cell_location(device_mgr)
            print(f"  {loc or 'N/A'}")
            pause()


def menu_screen():
    """Screen Tools Menu"""
    while True:
        print_header(f"{screen.MODULE_ICON} SCREEN TOOLS")
        print_menu({
            "1": "Take screenshot",
            "2": "Record screen",
            "3": "Start screen mirror (scrcpy)",
            "4": "Set screen orientation",
            "5": "Keep screen awake",
            "6": "Check screen state",
            "7": "Wake screen",
            "8": "Lock screen",
            "9": "Tap at coordinates",
            "10": "Swipe gesture",
            "11": "Type text on device",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice == "1":
            ok, msg = screen.screenshot(device_mgr)
            print_result(ok, msg)
            pause()
        elif choice == "2":
            dur = input("  Duration seconds [30]: ").strip() or "30"
            ok, msg = screen.screen_record(device_mgr, duration=int(dur))
            print_result(ok, msg)
            pause()
        elif choice == "3":
            ok, msg = screen.start_mirror(device_mgr)
            print_result(ok, msg)
            pause()
        elif choice == "4":
            print("  0=portrait, 1=landscape, 2=portrait-rev, 3=landscape-rev, auto=auto-rotate")
            orient = input("  Orientation: ").strip()
            ok, msg = screen.set_orientation(device_mgr, orient)
            print_result(ok, msg)
            pause()
        elif choice == "5":
            action = input("  Enable? (y/n): ").strip().lower()
            ok, msg = screen.stay_awake(device_mgr, enable=(action == "y"))
            print_result(ok, msg)
            pause()
        elif choice == "6":
            state, msg = screen.get_screen_state(device_mgr)
            print(f"  Screen: {state}")
            pause()
        elif choice == "7":
            ok, msg = screen.wake_screen(device_mgr)
            print_result(ok, msg)
            pause()
        elif choice == "8":
            ok, msg = screen.lock_screen(device_mgr)
            print_result(ok, msg)
            pause()
        elif choice == "9":
            x = input("  X: ").strip()
            y = input("  Y: ").strip()
            ok, msg = screen.tap(device_mgr, x, y)
            print_result(ok, msg)
            pause()
        elif choice == "10":
            x1 = input("  X1: ").strip()
            y1 = input("  Y1: ").strip()
            x2 = input("  X2: ").strip()
            y2 = input("  Y2: ").strip()
            dur = input("  Duration ms [300]: ").strip() or "300"
            ok, msg = screen.swipe(device_mgr, x1, y1, x2, y2, int(dur))
            print_result(ok, msg)
            pause()
        elif choice == "11":
            text = input("  Text: ").strip()
            ok, msg = screen.type_text(device_mgr, text)
            print_result(ok, msg)
            pause()


def menu_network():
    """Network Tools Menu"""
    while True:
        print_header(f"{network.MODULE_ICON} NETWORK TOOLS")
        print_menu({
            "1": "Get IP addresses",
            "2": "Get WiFi info",
            "3": "Scan WiFi networks",
            "4": "Toggle mobile data",
            "5": "Get active connections",
            "6": "Port scan (device itself)",
            "7": "Get DNS info",
            "8": "Get firewall rules (root)",
            "9": "Get/set proxy",
            "10": "Ping test",
            "11": "Traceroute",
            "12": "Get data usage stats",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice == "1":
            info, _ = network.get_ip_info(device_mgr)
            if info:
                for iface, data in info.items():
                    print(f"  {Fore.CYAN}{iface}{Style.RESET_ALL}")
                    print(f"    IPv4: {', '.join(data['ipv4']) or 'none'}")
                    print(f"    MAC: {data['mac'] or 'N/A'}")
            pause()
        elif choice == "2":
            info, _ = network.get_wifi_info(device_mgr)
            if info:
                for k, v in list(info.items())[:15]:
                    print(f"  {Fore.CYAN}{k}:{Style.RESET_ALL} {v}")
            pause()
        elif choice == "3":
            nets, msg = network.scan_wifi(device_mgr)
            if nets:
                for n in nets:
                    print(f"  {Fore.CYAN}{n.get('ssid', '?')}{Style.RESET_ALL} "
                          f"[{n.get('caps', '')}] Signal: {n.get('level', '?')}dBm")
            else:
                print_result(False, msg)
            pause()
        elif choice == "4":
            action = input("  Enable or Disable? (e/d): ").strip().lower()
            ok, msg = network.toggle_data(device_mgr, enable=(action == "e"))
            print_result(ok, msg)
            pause()
        elif choice == "5":
            conns, msg = network.get_connections_netstat(device_mgr)
            if conns:
                for c in conns[:30]:
                    print(f"  {c.get('proto', '?'):6} {c.get('local', '?'):25} → {c.get('remote', '?'):25} {c.get('state', '')}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "6":
            results, msg = network.port_scan_local(device_mgr)
            for r in results:
                color = Fore.GREEN if r["status"] == "OPEN" else Fore.RED
                print(f"  Port {r['port']}: {color}{r['status']}{Style.RESET_ALL}")
            pause()
        elif choice == "7":
            dns, _ = network.get_dns_info(device_mgr)
            for d in dns:
                print(f"  {d}")
            pause()
        elif choice == "8":
            rules, msg = network.get_firewall_rules(device_mgr)
            if rules:
                print(rules[:2000])
            else:
                print_result(False, msg)
            pause()
        elif choice == "9":
            action = input("  Get, Set, or Clear? (g/s/c): ").strip().lower()
            if action == "g":
                proxy, _ = network.get_proxy_settings(device_mgr)
                print(f"  Proxy: {proxy or 'Not set'}")
            elif action == "s":
                host = input("  Host: ").strip()
                port = input("  Port: ").strip()
                ok, msg = network.set_proxy(device_mgr, host, port)
                print_result(ok, msg)
            elif action == "c":
                ok, msg = network.clear_proxy(device_mgr)
                print_result(ok, msg)
            pause()
        elif choice == "10":
            host = input("  Host [8.8.8.8]: ").strip() or "8.8.8.8"
            count = input("  Count [5]: ").strip() or "5"
            stdout, _ = network.ping_test(device_mgr, host, int(count))
            print(stdout)
            pause()
        elif choice == "11":
            host = input("  Host [8.8.8.8]: ").strip() or "8.8.8.8"
            stdout, _ = network.traceroute(device_mgr, host)
            print(stdout[:2000] if stdout else "No output")
            pause()
        elif choice == "12":
            stdout, _ = network.get_data_usage(device_mgr)
            print(stdout[:1000] if stdout else "N/A")
            pause()


def menu_security():
    """Security Audit Menu"""
    while True:
        print_header(f"{security.MODULE_ICON} SECURITY AUDIT")
        print_menu({
            "1": "🔴 FULL SECURITY AUDIT (all checks)",
            "2": "Root detection (multi-method)",
            "3": "Magisk detection",
            "4": "Check encryption status",
            "5": "Check security patch level",
            "6": "Scan open ports",
            "7": "Find dangerous app permissions",
            "8": "Find debuggable apps",
            "9": "SELinux status",
            "10": "Frida detection",
            "11": "List all permission groups",
            "12": "App permissions audit",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice == "1":
            print(f"\n  {Fore.YELLOW}[*] Running full audit... (30-60s){Style.RESET_ALL}")
            results, msg = security.full_audit(device_mgr)
            if results:
                # Root
                root = results.get("root", {})
                root_status = f"{Fore.RED}ROOTED ({root.get('checks', {}).get('rooted', False)}){Style.RESET_ALL}" if root.get("rooted") else f"{Fore.GREEN}CLEAN{Style.RESET_ALL}"
                print(f"\n  Root status: {root_status}")
                print(f"  Confidence: {root.get('confidence', 'N/A')}")

                # Encryption
                enc = results.get("encryption", {})
                enc_status = f"{Fore.GREEN}ENCRYPTED{Style.RESET_ALL}" if enc.get("encrypted") else f"{Fore.RED}NOT ENCRYPTED{Style.RESET_ALL}"
                print(f"  Encryption: {enc_status}")

                # Patch level
                print(f"  Security patch: {results.get('security_patch', '?')}")
                print(f"  SELinux: {results.get('selinux', '?')}")
                print(f"  Build tags: {results.get('build_tags', '?')}")
                print(f"  Debuggable: {results.get('debuggable', '?')}")
                print(f"  ADB over network: {results.get('adb_over_network', '?')}")

                # Dangerous apps
                dangerous = results.get("dangerous_apps", [])
                if dangerous:
                    print(f"\n  {Fore.RED}⚠ Dangerous permissions found in {len(dangerous)} apps:{Style.RESET_ALL}")
                    for d in dangerous[:10]:
                        print(f"    {Fore.YELLOW}{d['package']}{Style.RESET_ALL}")
                        for p in d["dangerous_permissions"][:3]:
                            print(f"      - {p}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "2":
            result = security.check_root(device_mgr)
            if result:
                rooted = result.get("rooted", False)
                status = f"{Fore.RED}ROOTED{Style.RESET_ALL}" if rooted else f"{Fore.GREEN}NOT ROOTED{Style.RESET_ALL}"
                print(f"\n  Status: {status} (confidence: {result.get('confidence', 'N/A')})")
                checks = result.get("checks", {})
                su = checks.get("su_binary", {})
                print(f"  su binary: {'FOUND at ' + str(su.get('paths', [])) if su.get('found') else 'Not found'}")
                print(f"  Magisk: {'DETECTED' if checks.get('magisk') else 'Not found'}")
                print(f"  Test keys: {'YES (dangerous)' if checks.get('test_keys') else 'No'}")
                print(f"  RW /system: {'YES' if checks.get('rw_system') else 'No'}")
                root_apps = checks.get("root_apps", [])
                if root_apps:
                    print(f"  Root apps: {', '.join(root_apps)}")
            pause()
        elif choice == "3":
            result, msg = security.check_magisk(device_mgr)
            if result:
                status = f"{Fore.RED}DETECTED{Style.RESET_ALL}" if result.get("detected") else f"{Fore.GREEN}NOT FOUND{Style.RESET_ALL}"
                print(f"  Magisk: {status}")
                print(f"  Magisk app: {result.get('magisk_app', '?')}")
                print(f"  Files: {result.get('magisk_files', [])}")
                print(f"  Version: {result.get('magisk_version', '?')}")
            pause()
        elif choice == "4":
            result = security.check_encryption(device_mgr)
            if result:
                enc = f"{Fore.GREEN}ENCRYPTED{Style.RESET_ALL}" if result.get("encrypted") else f"{Fore.RED}NOT ENCRYPTED{Style.RESET_ALL}"
                print(f"  Encryption: {enc}")
                print(f"  Crypto state: {result.get('crypto_state', '?')}")
                print(f"  Crypto type: {result.get('crypto_type', '?')}")
            pause()
        elif choice == "5":
            result, msg = security.check_vulnerability_patch_level(device_mgr)
            if result:
                risk_color = Fore.RED if result["risk"] == "HIGH" else (Fore.YELLOW if result["risk"] == "MEDIUM" else Fore.GREEN)
                print(f"  Patch date: {result['patch_date']}")
                print(f"  Days old: {result['days_old']}")
                print(f"  Risk level: {risk_color}{result['risk']}{Style.RESET_ALL}")
                print(f"  Outdated: {result['outdated']}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "6":
            listeners, msg = security.scan_open_ports(device_mgr)
            if listeners:
                for l in listeners:
                    print(f"  Port {l['port']} on {l['ip']} - {l['state']}")
            else:
                print("  No listening ports found")
            pause()
        elif choice == "7":
            dangerous = security.get_dangerous_apps(device_mgr)
            if dangerous:
                for d in dangerous:
                    print(f"  {Fore.YELLOW}{d['package']}{Style.RESET_ALL}")
                    for p in d["dangerous_permissions"][:5]:
                        print(f"    {p}")
            else:
                print("  No highly dangerous permissions in top 50 apps")
            pause()
        elif choice == "8":
            apps, msg = security.check_debuggable_apps(device_mgr)
            if apps:
                for a in apps:
                    print(f"  {Fore.RED}{a}{Style.RESET_ALL}")
            else:
                print_result(False, msg or "No debuggable apps found in sampled apps")
            pause()
        elif choice == "9":
            result, _ = security.get_selinux_status(device_mgr)
            if result:
                print(f"  Mode: {result.get('mode', '?')}")
                print(f"  Policy loaded: {result.get('policy_loaded', '?')}")
            pause()
        elif choice == "10":
            result, msg = security.check_frida(device_mgr)
            if result:
                print(f"  Frida running: {result.get('frida_running', '?')}")
                print(f"  Processes: {result.get('frida_processes', '?')}")
                print(f"  Files: {result.get('frida_files', '?')}")
            pause()
        elif choice == "11":
            stdout, _ = security.list_all_permissions(device_mgr)
            print(stdout[:3000] if stdout else "N/A")
            pause()
        elif choice == "12":
            stdout, _ = security.audit_apk_permissions(device_mgr)
            print(stdout[:3000] if stdout else "N/A")
            pause()


def menu_surveillance():
    """Surveillance Menu"""
    while True:
        print_header(f"{surveillance.MODULE_ICON} SURVEILLANCE & MONITORING")
        print_menu({
            "1": "Take photo (camera snap)",
            "2": "Record video (front camera via screenrecord)",
            "3": "Get GPS location",
            "4": "Get cell tower location",
            "5": "Location services status",
            "6": "Start GPS tracking",
            "7": "Monitor notifications (real-time)",
            "8": "Get active notifications",
            "9": "List device sensors",
            "10": "Full device dump to files",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice == "1":
            cam = input("  Camera (back/front) [back]: ").strip() or "back"
            ok, msg = surveillance.take_photo(device_mgr, camera=cam)
            print_result(ok, msg)
            pause()
        elif choice == "2":
            dur = input("  Duration [10]: ").strip() or "10"
            ok, msg = surveillance.record_video_front(device_mgr, duration=int(dur))
            print_result(ok, msg)
            pause()
        elif choice == "3":
            loc, msg = surveillance.get_gps_location(device_mgr)
            print(f"  {loc or 'No GPS data'}")
            pause()
        elif choice == "4":
            loc, msg = surveillance.get_cell_location(device_mgr)
            print(f"  {loc or 'No cell data'}")
            pause()
        elif choice == "5":
            status, _ = surveillance.get_location_services_status(device_mgr)
            if status:
                for k, v in status.items():
                    print(f"  {Fore.CYAN}{k}:{Style.RESET_ALL} {v}")
            pause()
        elif choice == "6":
            interval = input("  Interval seconds [10]: ").strip() or "10"
            dur = input("  Duration seconds [60]: ").strip() or "60"
            out = input("  Output file (Enter=gps_track.json): ").strip() or "gps_track.json"
            locations, msg = surveillance.start_location_tracking(
                device_mgr, interval=int(interval), duration=int(dur), output_file=out
            )
            print(f"  {msg}")
            pause()
        elif choice == "7":
            dur = input("  Monitor duration [30]: ").strip() or "30"
            notifs, msg = surveillance.monitor_notifications(device_mgr, duration=int(dur))
            print(f"  {msg}")
            pause()
        elif choice == "8":
            notifs, msg = surveillance.get_active_notifications(device_mgr)
            print(f"  {notifs[:500] if notifs else 'None'}")
            pause()
        elif choice == "9":
            sensors, msg = surveillance.get_sensor_list(device_mgr)
            print(f"  {sensors or 'N/A'}")
            pause()
        elif choice == "10":
            out_dir = input("  Output dir [logs/dumps]: ").strip() or "logs/dumps"
            files_created, msg = surveillance.dump_device_info_full(device_mgr, output_dir=out_dir)
            print_result(len(files_created) > 0, msg)
            pause()


def menu_automation():
    """Automation Menu"""
    while True:
        print_header(f"{automation.MODULE_ICON} AUTOMATION & SCRIPTS")
        print_menu({
            "1": "Run custom ADB shell command",
            "2": "Run batch commands",
            "3": "Execute script file",
            "4": "Create macro",
            "5": "Run macro",
            "6": "List macros",
            "7": "Simulate key press",
            "8": "Open URL on device",
            "9": "Monitor input events",
            "10": "Bulk uninstall apps",
            "11": "Create ADB backup",
            "12": "Restore ADB backup",
            "0": "Back",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip()

        if choice == "0":
            break
        elif choice == "1":
            cmd = input("  Shell command: ").strip()
            result, msg = automation.run_adb_shell_command(device_mgr, cmd)
            if result:
                if result["stdout"]:
                    print(result["stdout"])
                if result["stderr"]:
                    print(f"  {Fore.RED}{result['stderr']}{Style.RESET_ALL}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "2":
            print("  Enter commands (empty line to finish):")
            cmds = []
            while True:
                c = input("  > ").strip()
                if not c:
                    break
                cmds.append(c)
            if cmds:
                delay = input("  Delay between commands (seconds) [1]: ").strip() or "1"
                results, msg = automation.batch_command(device_mgr, cmds, delay=float(delay))
                for r in results:
                    icon = "OK" if r["rc"] == 0 else "FAIL"
                    print(f"  [{icon}] {r['command']}: {r['output'][:80]}")
            pause()
        elif choice == "3":
            path = input("  Script file path: ").strip().strip('"')
            results, msg = automation.execute_script_file(device_mgr, path)
            if results:
                for r in results:
                    icon = "OK" if r["rc"] == 0 else "FAIL"
                    print(f"  [{icon}] Line {r['line']}: {r['output'][:80]}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "4":
            name = input("  Macro name: ").strip()
            print("  Enter commands (empty line to finish):")
            cmds = []
            while True:
                c = input("  > ").strip()
                if not c:
                    break
                cmds.append(c)
            if cmds:
                ok, msg = automation.create_macro(name, cmds)
                print_result(ok, msg)
            pause()
        elif choice == "5":
            name = input("  Macro name: ").strip()
            results, msg = automation.run_macro(device_mgr, name)
            if results:
                for r in results:
                    icon = "OK" if r["rc"] == 0 else "FAIL"
                    print(f"  [{icon}] {r['command']}: {r['output'][:80]}")
            else:
                print_result(False, msg)
            pause()
        elif choice == "6":
            macros = automation.list_macros()
            if macros:
                for m in macros:
                    print(f"  {Fore.CYAN}{m['name']}{Style.RESET_ALL} ({m['commands']} commands)")
            else:
                print("  No macros saved")
            pause()
        elif choice == "7":
            keycode = input("  Keycode (e.g., 26=POWER, 3=HOME, 4=BACK): ").strip()
            ok, msg = automation.simulate_keyevent(device_mgr, keycode)
            print_result(ok, msg)
            pause()
        elif choice == "8":
            url = input("  URL: ").strip()
            ok, msg = automation.launch_url(device_mgr, url)
            print_result(ok, msg)
            pause()
        elif choice == "9":
            events, msg = automation.get_input_events(device_mgr)
            print(f"  {events or 'N/A'}")
            pause()
        elif choice == "10":
            print("  Enter package names (empty line to finish):")
            pkgs = []
            while True:
                p = input("  > ").strip()
                if not p:
                    break
                pkgs.append(p)
            if pkgs:
                results, msg = automation.bulk_install_from_list(device_mgr, pkgs)
                for r in results:
                    icon = "OK" if r["success"] else "FAIL"
                    print(f"  [{icon}] {r['package']}")
            pause()
        elif choice == "11":
            out = input("  Output file [backup.ab]: ").strip() or "backup.ab"
            ok, msg = automation.create_backup(device_mgr, out)
            print_result(ok, msg)
            pause()
        elif choice == "12":
            path = input("  Backup file path: ").strip().strip('"')
            ok, msg = automation.restore_backup(device_mgr, path)
            print_result(ok, msg)
            pause()


# ── Main Menu ──────────────────────────────────────────────────


def menu_plugins():
    """Plugin Manager Menu"""
    while True:
        print_header("🔌 PLUGIN MANAGER")
        plugins = list_plugins()
        if not plugins:
            print(f"  {Fore.YELLOW}No plugins found.{Style.RESET_ALL}")
            pause()
            break
        print("  Installed plugins: " + str(len(plugins)))
        print()
        plugin_list = []
        for name, p in sorted(plugins.items()):
            info = p.get("info", {})
            error = p.get("error")
            version = info.get("version", "?")
            desc = info.get("description", "")[:50]
            if error:
                status = f"{Fore.RED}ERROR{Style.RESET_ALL}"
            else:
                status = f"{Fore.GREEN}OK{Style.RESET_ALL}"
            idx = len(plugin_list) + 1
            plugin_list.append((name, p))
            print(f"  {Fore.CYAN}{idx:2d}.{Style.RESET_ALL} {name} v{version} ({status}) - {desc}")
        print()
        print_menu({"S": "Start a plugin", "R": "Reload plugins", "0": "Back to main menu"})
        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip().upper()
        if choice == "0":
            break
        elif choice == "R":
            continue
        elif choice == "S":
            if not plugin_list:
                continue
            idx_str = input("  Enter plugin number: ").strip()
            try:
                idx = int(idx_str) - 1
                if 0 <= idx < len(plugin_list):
                    name, p = plugin_list[idx]
                    info = p.get("info", {})
                    plugin_obj = info.get("plugin")
                    if plugin_obj and hasattr(plugin_obj, "run"):
                        print(f"  Starting {name}... (Ctrl+C to stop)")
                        try:
                            plugin_obj.run()
                        except KeyboardInterrupt:
                            print(f"\n  {name} stopped.")
                            if hasattr(plugin_obj, "stop"):
                                plugin_obj.stop()
                    else:
                        print(f"  {Fore.YELLOW}{name} has no run() method.{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.RED}Invalid number.{Style.RESET_ALL}")
            except ValueError:
                print(f"  {Fore.RED}Invalid input.{Style.RESET_ALL}")
            pause()



def main_menu():
    """Main interactive menu"""
    global session_token

    clear_screen()
    print(BANNER)

    # Check ADB
    adb_ok, adb_msg = check_adb()
    if not adb_ok:
        print(f"  {Fore.RED}[FAIL] ADB not found: {adb_msg}{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Install Android Platform Tools first{Style.RESET_ALL}")
        pause()
        return

    print(f"  {Fore.GREEN}[OK] ADB ready: {adb_msg}{Style.RESET_ALL}")

    # Check device
    dev_ok, dev_msg = check_device_connected(device_mgr)
    if dev_ok:
        print(f"  {Fore.GREEN}[OK] Device: {dev_msg}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}[WARN] {dev_msg}{Style.RESET_ALL}")

    # Login
    logged_in = False
    for _ in range(3):
        if login():
            logged_in = True
            break

    if not logged_in:
        print(f"\n  {Fore.RED}Too many failed attempts. Exiting.{Style.RESET_ALL}")
        return

    # Main loop
    while True:
        clear_screen()
        print(BANNER)

        # Status bar
        devices = device_mgr.list_devices()
        active = device_mgr.get_active()
        dev_count = len(devices)
        status = f"{Fore.GREEN}●{Style.RESET_ALL}" if active else f"{Fore.RED}●{Style.RESET_ALL}"
        sess_username = "?"
        if session_token and session_token in auth_mgr.sessions:
            sess = auth_mgr.sessions[session_token]
            sess_username = getattr(sess, "username", "?")
        print(f"  {status} Device: {active or 'None'} | Connected: {dev_count} | "
              f"User: {Fore.CYAN}{sess_username}{Style.RESET_ALL}")
        print()

        print_menu({
            "1": f"{connection.MODULE_ICON} Connection Manager (USB/WiFi/Multi-device)",
            "2": f"{device.MODULE_ICON} Device Info & Control",
            "3": f"{apps.MODULE_ICON} App Management",
            "4": f"{files.MODULE_ICON} File Manager",
            "5": f"{data.MODULE_ICON} Data Extraction",
            "6": f"{screen.MODULE_ICON} Screen Tools",
            "7": f"{network.MODULE_ICON} Network Tools",
            "8": f"{security.MODULE_ICON} Security Audit",
            "9": f"{surveillance.MODULE_ICON} Surveillance & Monitoring",
            "10": f"{automation.MODULE_ICON} Automation & Scripts",
            "P": "Plugin Manager",
            "L": "View audit logs",
            "Q": "Quit MEGASUS",
        })

        choice = input(f"  {Fore.YELLOW}Choice: {Style.RESET_ALL}").strip().upper()

        if choice == "Q":
            print(f"\n  {Fore.CYAN}MEGASUS shutting down. Stay sharp.{Style.RESET_ALL}")
            log("LOGOUT", "User quit")
            break
        elif choice == "1":
            menu_connection()
        elif choice == "2":
            menu_device()
        elif choice == "3":
            menu_apps()
        elif choice == "4":
            menu_files()
        elif choice == "5":
            menu_data()
        elif choice == "6":
            menu_screen()
        elif choice == "7":
            menu_network()
        elif choice == "8":
            menu_security()
        elif choice == "9":
            menu_surveillance()
        elif choice == "10":
            menu_automation()
        elif choice == "P":
            menu_plugins()
        elif choice == "P":
            menu_plugins()
        elif choice == "P":
            menu_plugins()
        elif choice == "P":
            menu_plugins()
        elif choice == "L":
            logs = get_logs(lines=50)
            if logs:
                print(f"\n  {Fore.CYAN}── Recent Audit Logs ──{Style.RESET_ALL}")
                for line in logs:
                    print(f"  {line.rstrip()}")
            else:
                print("  No logs yet")
            pause()


# ── Entry Point ────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n  {Fore.CYAN}MEGASUS interrupted. Goodbye.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n  {Fore.RED}FATAL ERROR: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
