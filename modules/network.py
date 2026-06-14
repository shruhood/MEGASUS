"""
MEGASUS Module: NETWORK - WiFi, Port Scan, Connections, Firewall
"""
from core.engine import DeviceManager, ADB, _run_shell, _run, log_command
import re

MODULE_NAME = "Network Tools"
MODULE_ICON = "🌐"


def get_ip_info(device_manager, serial=None):
    """Get device IP addresses"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell("ip addr show", device=target)
    if not stdout:
        stdout, _, _ = _run_shell("ifconfig", device=target)

    interfaces = {}
    current_iface = None
    for line in stdout.splitlines():
        # Interface line
        m = re.match(r"^\d+:\s+(\w+):", line)
        if m:
            current_iface = m.group(1)
            interfaces[current_iface] = {"ipv4": [], "ipv6": [], "mac": ""}
        if current_iface:
            # IPv4
            m4 = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", line)
            if m4:
                interfaces[current_iface]["ipv4"].append(m4.group(1))
            # MAC
            m_mac = re.search(r"link/ether ([\da-fA-F:]+)", line)
            if m_mac:
                interfaces[current_iface]["mac"] = m_mac.group(1)
            # IPv6
            m6 = re.search(r"inet6 ([\da-fA-F:]+)", line)
            if m6:
                interfaces[current_iface]["ipv6"].append(m6.group(1))

    return interfaces, "OK"


def get_wifi_info(device_manager, serial=None):
    """Get detailed WiFi info"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell("dumpsys wifi | head -80", device=target)
    info = {}
    for line in stdout.splitlines():
        line = line.strip()
        if "SSID:" in line or "mWifiInfo" in line or "BSSID" in line or "RSSI" in line:
            info[line.split(":")[0].strip()] = ":".join(line.split(":")[1:]).strip()
    return info, "OK"


def scan_wifi(device_manager, serial=None):
    """Scan for available WiFi networks"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Start scan
    _run_shell("cmd wifi start-scan", device=target, timeout=10)
    import time
    time.sleep(3)

    stdout, _, _ = _run_shell("cmd wifi get-scan-results", device=target, timeout=15)
    networks = []
    for line in stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("Bssid"):
            parts = line.split()
            if len(parts) >= 5:
                networks.append({
                    "bssid": parts[0],
                    "ssid": parts[1] if len(parts) > 1 else "hidden",
                    "freq": parts[2] if len(parts) > 2 else "",
                    "level": parts[3] if len(parts) > 3 else "",
                    "caps": parts[4] if len(parts) > 4 else "",
                })
    return networks, f"Found {len(networks)} networks"


def toggle_data(device_manager, enable=True, serial=None):
    """Toggle mobile data"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    cmd = "svc data enable" if enable else "svc data disable"
    stdout, stderr, rc = _run_shell(cmd, device=target)
    state = "ON" if enable else "OFF"
    return rc == 0, f"Mobile data {state}"


def get_connections(device_manager, serial=None):
    """Get active network connections (netstat)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell("cat /proc/net/tcp /proc/net/tcp6 /proc/net/udp /proc/net/udp6 2>/dev/null", device=target, timeout=10)
    return stdout, "OK"


def get_connections_netstat(device_manager, serial=None):
    """Get connections via netstat (if available)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, rc = _run_shell("netstat -tunap 2>/dev/null || netstat -tuap 2>/dev/null || netstat -a", device=target, timeout=10)
    if rc != 0:
        # Fallback: parse /proc/net
        stdout, _, _ = _run_shell("cat /proc/net/tcp", device=target)

    connections = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or "Local" in line or "Proto" in line:
            continue
        parts = line.split()
        if len(parts) >= 4:
            connections.append({
                "proto": parts[0],
                "local": parts[1] if len(parts) > 1 else "",
                "remote": parts[2] if len(parts) else "",
                "state": parts[3] if len(parts) > 3 else "",
            })
    return connections, "OK"


def port_scan_local(device_manager, host="127.0.0.1", ports="22,80,443,5555,8080,8443,9090", serial=None):
    """Scan ports on device itself"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    results = []
    for port in ports.split(","):
        port = port.strip()
        stdout, _, _ = _run_shell(
            f"echo '' > /dev/tcp/{host}/{port} 2>&1 && echo OPEN || echo CLOSED",
            device=target, timeout=5
        )
        status = "OPEN" if "OPEN" in stdout or stdout.strip() == "" else "CLOSED/TIMEOUT"
        results.append({"port": port, "status": status})

    return results, "Scan complete"


def get_dns_info(device_manager, serial=None):
    """Get DNS configuration"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "getprop | grep dns && getprop | grep net.dns",
        device=target, timeout=10
    )
    dns_servers = [l.strip() for l in stdout.splitlines() if l.strip()]
    return dns_servers, "OK"


def get_firewall_rules(device_manager, serial=None):
    """Get iptables firewall rules (may need root)"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, stderr, rc = _run_shell("iptables -L -n -v 2>/dev/null", device=target, timeout=10)
    if rc != 0 or not stdout:
        return None, "iptables not available or needs root"
    return stdout, "OK"


def get_proxy_settings(device_manager, serial=None):
    """Get proxy settings"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "settings get global http_proxy && "
        "settings get global global_http_proxy_host && "
        "settings get global global_http_proxy_port",
        device=target, timeout=10
    )
    return stdout.strip(), "OK"


def set_proxy(device_manager, host, port, serial=None):
    """Set global proxy"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell(
        f"settings put global http_proxy {host}:{port}", device=target
    )
    return rc == 0, f"Proxy set to {host}:{port}"


def clear_proxy(device_manager, serial=None):
    """Clear proxy"""
    target = serial or device_manager.get_active()
    if not target:
        return False, "No device"
    stdout, stderr, rc = _run_shell("settings put global http_proxy :0", device=target)
    return rc == 0, "Proxy cleared"


def ping_test(device_manager, host="8.8.8.8", count=5, serial=None):
    """Ping test from device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"
    stdout, stderr, rc = _run_shell(f"ping -c {count} {host}", device=target, timeout=30)
    return stdout, "OK"


def traceroute(device_manager, host="8.8.8.8", serial=None):
    """Traceroute from device"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    # Try traceroute, then tracepath
    stdout, _, rc = _run_shell(f"traceroute {host} 2>/dev/null", device=target, timeout=30)
    if rc != 0:
        stdout, _, _ = _run_shell(f"tracepath {host} 2>/dev/null", device=target, timeout=30)
    return stdout, "OK"


def get_data_usage(device_manager, serial=None):
    """Get mobile data usage stats"""
    target = serial or device_manager.get_active()
    if not target:
        return None, "No device"

    stdout, _, _ = _run_shell(
        "dumpsys netstats | head -100", device=target, timeout=10
    )
    return stdout, "OK"
