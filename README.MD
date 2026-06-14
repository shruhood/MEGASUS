<div align="center">


                          ███╗   ███╗███████╗ ██████╗  █████╗ ███████╗██╗   ██╗███████╗
                          ████╗ ████║██╔════╝██╔════╝ ██╔══██╗██╔════╝██║   ██║██╔════╝
                          ██╔████╔██║█████╗  ██║  ███╗███████║███████╗██║   ██║███████╗
                          ██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║╚════██║██║   ██║╚════██║
                          ██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║███████║╚██████╔╝███████║
                          ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝
                                                                              P R O
```

### Android Device Operations Platform

![Release](https://img.shields.io/badge/release-v1.0.0-1e40af?style=flat-square&labelColor=2d3748)
![Python](https://img.shields.io/badge/python-3.8+-1e40af?style=flat-square&labelColor=2d3748)
![License](https://img.shields.io/badge/license-MIT-065f46?style=flat-square&labelColor=2d3748)
![Platform](https://img.shields.io/badge/platform-Android%208+-92400e?style=flat-square&labelColor=2d3748)
![ADB](https://img.shields.io/badge/engine-ADB%20native-7c3aed?style=flat-square&labelColor=2d3748)
![Stars](https://img.shields.io/github/stars/shruhood/megasus-pro?style=flat-square&labelColor=2d3748&color=7c3aed)

**Fleet Management · Deep Automation · Device Telemetry · Security Audit**

*Enterprise-grade, open-source Android operations center — all from a single unified CLI.*

[Quick Start](#-quick-start) · [Modules](#-modules) · [Architecture](#-architecture) · [Roadmap](#-roadmap) · [Contributing](#-contributing)

</div>

---

## Overview

**MEGASUS PRO** is an enterprise-grade, open-source Android operations platform built on ADB. Manage single devices or entire fleets, automate repetitive workflows, audit device security posture, and extract comprehensive telemetry — all from a clean, unified terminal interface.

```
╔══════════════════════════════════════════════════════╗
║              MEGASUS PRO  v1.0.0                     ║
║          Android Operations Platform                 ║
╠══════════════════════════════════════════════════════╣
║  Device: SM-G991B (1 online)                         ║
║                                                      ║
║  [1]  Connection Manager      [6]  Screen Tools      ║
║  [2]  Device Info & Control   [7]  Network Tools     ║
║  [3]  App Management          [8]  Security Audit    ║
║  [4]  File Manager            [9]  Surveillance      ║
║  [5]  Data Extraction         [10] Automation        ║
║                                                      ║
║  Select module [1-10]: █                             ║
╚══════════════════════════════════════════════════════╝
```

---

## 📸 Screenshots

<div align="center">

### Main Menu
![MEGASUS PRO Main Menu](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/MagasusJPG.JPG)

### Login
![Login Screen](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/login.JPG)

</div>

---

### Module Previews

| Connection Manager | App Manager |
|:-:|:-:|
| ![Connection Manager](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/connection%20manager.JPG) | ![App Manager](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/app%20manager.JPG) |

| Data Extraction | Network Tools |
|:-:|:-:|
| ![Data Extraction](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/data%20extraction.JPG) | ![Network Tools](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/network%20tools.JPG) |

| Screen Tools | Security Audit |
|:-:|:-:|
| ![Screen Tools](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/screen%20tool.JPG) | ![Security Audit](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/sequrity%20audit.JPG) |

<div align="center">

### Automation & Scripts
![Automation & Scripts](https://raw.githubusercontent.com/shruhood/MEGASUS/main/screenshots/AUTOMATION%20%26%20SCRIPTS.JPG)

</div>


---

## ⚡ Quick Start

**Requirements:** Python 3.8+ · ADB in PATH · USB Debugging enabled on device

```bash
# 1. Clone
git clone https://github.com/shruhood/megasus-pro.git
cd megasus-pro

# 2. Install dependencies
pip install -r requirements.txt

# 3. Connect a device
adb devices                          # USB
adb tcpip 5555                       # OR go wireless:
adb connect 192.168.x.x:5555

# 4. Launch
python megasus.py
```

> **Android setup:** Settings → Developer Options → Enable USB Debugging

---

## 📦 Modules

MEGASUS PRO ships with **10 specialized modules** covering the full Android device lifecycle.

---

### 🔗 1 · Connection Manager
> Multi-device fleet orchestration over USB and wireless ADB.

```
┌─ CONNECTION MANAGER
│
│  [1]  Refresh device list
│  [2]  Set active device
│  [3]  Connect wireless (WiFi ADB)
│  [4]  Switch TCP/IP → USB
│  [5]  Restart ADB server
│  [6]  List all with details
│
└─ Choice: █
```

| Feature | Detail |
|---------|--------|
| Protocols | USB · WiFi ADB · TCP/IP |
| Fleet support | Multi-device session management |
| Health check | Connection status monitoring |

---

### 📱 2 · Device Info & Control
> Complete device telemetry dashboard.

```
▣  DEVICE INFO & CONTROL
   Model:    SM-G991B
   Battery:  76%  │  Temp: 31°C
   CPU load: 15.77
   SELinux:  Enforcing

   [1]  Full device info dump
   [2]  Battery details
   [3]  CPU / RAM stats
   [4]  Storage overview
   [5]  Screen info
   [6]  SELinux status
   [7]  Build properties
   [8]  Full hardware dump
```

**Telemetry covered:** Battery · CPU · RAM · Storage · Screen · SELinux · Build props · Hardware

---

### 📦 3 · App Management
> Full APK lifecycle management.

```
[1]   List all apps
[3]   List third-party apps
[6]   Install APK
[7]   Install all APKs from folder
[11]  Uninstall app
[12]  Freeze app (disable)
[13]  Unfreeze app (enable)
[14]  Clear app data
[15]  Get dangerous permissions
[16]  List running processes
```

**Key capabilities:** Bulk install · Freeze/Unfreeze · Permission audit · Sideload from folder · Background process control

---

### 📁 4 · File Manager
> Bidirectional file operations across device storage.

```
[1]  Browse device storage         Current path: /sdcard/
[2]  Push file to device
[3]  Pull file from device
[4]  Delete file on device
[5]  Create directory
[6]  List directory contents
```

---

### 💾 5 · Data Extraction
> Structured export of device data in machine-readable formats.

```
[1]   Extract contacts
[2]   Extract SMS messages
[3]   Extract call logs
[4]   Get running services
[5]   Get active notifications
[8]   Get media files list
[10]  Get registered accounts
```

**Output formats:** JSON · CSV · Plain text

---

### 🖥 6 · Screen Tools
> Remote display control and input simulation.

```
[1]   Take screenshot
[2]   Record screen
[3]   Start screen mirror (scrcpy)
[4]   Stop screen mirror
[9]   Tap at coordinates (x, y)
[10]  Swipe gesture
[11]  Type text on device
[12]  Simulate key press
```

**Integrations:** scrcpy · ADB input · Shell commands

---

### 🌐 7 · Network Tools
> Network diagnostics and configuration.

```
[1]   Get IP addresses
[3]   Scan WiFi networks
[6]   Port scan (device itself)
[8]   DNS query
[9]   Set proxy
[10]  Ping test
[11]  Traceroute
[12]  Data usage stats
```

---

### 🔒 8 · Security Audit
> Comprehensive device security posture assessment.

```
[1]   ● FULL SECURITY AUDIT
[2]   Root detection
[3]   Magisk / Frida detection
[4]   Check encryption status
[5]   Security patch level
[6]   Bootloader status
[7]   SELinux policy check
[12]  App permissions audit
```

**Detects:** Root · Magisk · Frida · Unencrypted storage · Outdated patches · Permissive SELinux · Dangerous app permissions

---

### 👁 9 · Surveillance & Monitoring
> Device observability suite.

```
[5]   Location services status
[6]   Start GPS tracking
[7]   Monitor notifications (real-time)
[9]   List device sensors
[10]  Full device dump to files
```

> **Note:** For authorised device monitoring, fleet management, and compliance use cases only.

---

### ⚡ 10 · Automation & Scripts
> Macro engine for repeatable workflows.

```
[1]   Run custom ADB shell command
[2]   Run batch commands from list
[4]   Create macro
[5]   Run macro
[6]   List saved macros
[8]   Simulate key events
[9]   Run script file
[11]  Create ADB backup
[12]  Restore ADB backup
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│                   CLI LAYER                      │
│          megasus.py · config.yaml · plugins/     │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                 MODULE LAYER                     │
│  connection · device_info · app_mgmt · file_mgr  │
│  data_extract · screen · network · security      │
│  surveillance · automation                       │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                  CORE LAYER                      │
│   ADB Engine · Shell Runner · Device Registry    │
│   Audit Logger                                   │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                   ANDROID                        │
│        ADB Daemon · Device Shell · USB/TCP       │
└─────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
megasus-pro/
├── core/                   # ADB engine, device registry, audit logger
├── modules/                # 10 operational modules
│   ├── connection_manager.py
│   ├── device_info.py
│   ├── app_management.py
│   ├── file_manager.py
│   ├── data_extraction.py
│   ├── screen_tools.py
│   ├── network_tools.py
│   ├── security_audit.py
│   ├── surveillance.py
│   └── automation.py
├── dashboard/              # Optional web dashboard (v1.1)
├── plugins/                # Community extensions
├── docs/                   # Full documentation
│   ├── quickstart.md
│   ├── modules/
│   └── api-reference.md
├── logs/                   # Audit trail (auto-generated)
├── screenshot/             # Demo assets
├── megasus.py              # Entry point
├── config.yaml             # Configuration
├── requirements.txt
└── README.md
```

---

## 📊 Feature Comparison

| Feature | MEGASUS PRO | Plain ADB CLI | Scrcpy | Vysor (paid) |
|---------|:-----------:|:-------------:|:------:|:------------:|
| Unified module system | ✅ | ❌ | ❌ | ❌ |
| Multi-device fleet | ✅ | ✅ | ❌ | ❌ |
| App freeze / lifecycle | ✅ | ❌ | ❌ | ❌ |
| Security audit | ✅ | ❌ | ❌ | ❌ |
| Macro automation | ✅ | ❌ | ❌ | ❌ |
| Screen mirror | ✅ | ❌ | ✅ | ✅ |
| GPS / sensor monitoring | ✅ | ❌ | ❌ | ❌ |
| Open source | ✅ | ✅ | ✅ | ❌ |
| Plugin system | ✅ | ❌ | ❌ | ❌ |
| Audit logging | ✅ | ❌ | ❌ | ❌ |

---

## 🗺 Roadmap

### v1.0 — Shipped ✅
- [x] 10 core modules complete
- [x] Audit logging system
- [x] Plugin architecture (`plugins/` directory)

### v1.1 — In Progress 🔵
- [ ] Web dashboard (optional browser UI wrapping all CLI modules)
- [ ] Config profiles per device (device-specific `config.yaml` overrides)

### v2.0 — Planned ⬜
- [ ] Docker deployment — containerised ADB server for CI/CD pipelines
- [ ] REST API mode — expose all modules as a local HTTP API
- [ ] Fleet scheduling — cron-style automation across multiple devices

---

## 🤝 Contributing

Contributions are welcome! Open issues or submit pull requests.

```bash
# 1. Fork the repo
# 2. Create your feature branch
git checkout -b feature/amazing-feature

# 3. Commit your changes
git commit -m 'Add amazing feature'

# 4. Push to the branch
git push origin feature/amazing-feature

# 5. Open a Pull Request
```

---

## 👤 About

**MEGASUS PRO** is built and maintained by **Suraj Singh** across multiple ventures.

| | |
|---|---|
| **GitHub** | [@shruhood](https://github.com/shruhood) |
| **Email** | shruhood@gmail.com · ibakeweb@gmail.com |
| **WhatsApp** | [Join the channel](https://whatsapp.com/channel/0029Vb7eYJP5PO0vRy786z46) |

### Organizations

| Organization | Contact | Website |
|---|---|---|
| **Bakweb** | hello@bakeweb.in | [bakeweb.in](https://bakeweb.in) |
| **SunDial Technologies** | shruhood@gmail.com | — |
| **Cyber SunDial** | shruhood@gmail.com | — |

---

## 📄 License

```
MIT License — Copyright (c) 2024 Suraj Singh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">

*Built with ❤️ by Suraj Singh — Bakweb · SunDial Technologies · Cyber SunDial*

**[⭐ Star this repo](https://github.com/shruhood/megasus-pro) · [🐛 Report Bug](https://github.com/shruhood/megasus-pro/issues) · [💡 Request Feature](https://github.com/shruhood/megasus-pro/issues)**

</div>
