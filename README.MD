
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font-mono), monospace; }

.hero {
  background: #0a0e17;
  border-radius: var(--border-radius-lg);
  padding: 40px 32px 32px;
  position: relative;
  overflow: hidden;
  border: 0.5px solid #1e2d45;
}
.hero-grid {
  position: absolute; inset: 0;
  background-image: linear-gradient(rgba(0,212,255,0.04) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0,212,255,0.04) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
}
.hero-glow {
  position: absolute; top: -60px; right: -60px;
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(0,212,255,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.hero-glow2 {
  position: absolute; bottom: -40px; left: 100px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(16,185,129,0.06) 0%, transparent 70%);
  pointer-events: none;
}

.badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(0,212,255,0.1); border: 0.5px solid rgba(0,212,255,0.3);
  color: #00d4ff; font-size: 11px; font-family: var(--font-mono);
  padding: 3px 10px; border-radius: 20px; margin-bottom: 16px;
  letter-spacing: 0.05em;
}
.badge-dot { width: 6px; height: 6px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

.hero-title {
  font-size: 36px; font-weight: 700; letter-spacing: -0.02em;
  color: #ffffff; line-height: 1.1; margin-bottom: 6px;
  font-family: var(--font-sans);
}
.hero-title span { color: #00d4ff; }
.hero-version { color: #10b981; font-size: 12px; font-family: var(--font-mono); margin-bottom: 12px; letter-spacing: 0.08em; }
.hero-tagline { color: #8892a4; font-size: 14px; font-family: var(--font-sans); line-height: 1.6; max-width: 480px; margin-bottom: 24px; }

.hero-stats {
  display: flex; gap: 24px; margin-bottom: 28px; flex-wrap: wrap;
}
.stat { display: flex; flex-direction: column; }
.stat-val { color: #ffffff; font-size: 18px; font-weight: 600; font-family: var(--font-sans); }
.stat-label { color: #4a5568; font-size: 11px; letter-spacing: 0.06em; font-family: var(--font-mono); }

.module-grid {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 28px;
}
.module-card {
  background: rgba(255,255,255,0.03); border: 0.5px solid rgba(255,255,255,0.08);
  border-radius: 8px; padding: 10px 8px; cursor: pointer; transition: all 0.2s;
}
.module-card:hover { background: rgba(0,212,255,0.06); border-color: rgba(0,212,255,0.25); }
.module-card.active { background: rgba(0,212,255,0.1); border-color: rgba(0,212,255,0.4); }
.module-icon { font-size: 16px; margin-bottom: 4px; }
.module-name { color: #8892a4; font-size: 10px; font-family: var(--font-sans); line-height: 1.3; }

.preview-area {
  background: #06090f; border-radius: 8px; border: 0.5px solid #1a2332;
  overflow: hidden; min-height: 200px;
}
.preview-topbar {
  background: #0d1521; padding: 8px 14px; display: flex; align-items: center; gap: 8px;
  border-bottom: 0.5px solid #1a2332;
}
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.red { background: #ff5f57; }
.dot.yellow { background: #febc2e; }
.dot.green { background: #28c840; }
.preview-title { color: #4a5568; font-size: 11px; font-family: var(--font-mono); margin-left: 8px; }
.preview-content { padding: 16px; font-family: var(--font-mono); font-size: 12px; line-height: 1.8; }

.section { margin-top: 28px; }
.section-label { color: #4a5568; font-size: 10px; letter-spacing: 0.1em; font-family: var(--font-mono); margin-bottom: 12px; text-transform: uppercase; }

.feature-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.feature-card {
  background: rgba(255,255,255,0.02); border: 0.5px solid rgba(255,255,255,0.07);
  border-radius: 8px; padding: 14px;
}
.feature-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.feature-icon { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
.feature-name { color: #c8d3e0; font-size: 13px; font-family: var(--font-sans); font-weight: 500; }
.feature-desc { color: #4a5568; font-size: 11px; font-family: var(--font-sans); line-height: 1.5; }
.feature-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 8px; }
.tag { background: rgba(0,212,255,0.08); color: #00d4ff; font-size: 10px; padding: 2px 7px; border-radius: 10px; font-family: var(--font-mono); }
.tag.green { background: rgba(16,185,129,0.08); color: #10b981; }
.tag.amber { background: rgba(245,158,11,0.08); color: #f59e0b; }

.readme-section {
  background: #0a0e17; border: 0.5px solid #1e2d45; border-radius: var(--border-radius-lg);
  overflow: hidden; margin-top: 16px;
}
.readme-tab-bar {
  background: #06090f; border-bottom: 0.5px solid #1a2332;
  padding: 0 16px; display: flex; gap: 0;
}
.readme-tab {
  color: #4a5568; font-size: 12px; padding: 10px 14px; cursor: pointer;
  border-bottom: 2px solid transparent; transition: all 0.15s; font-family: var(--font-sans);
}
.readme-tab.active { color: #00d4ff; border-bottom-color: #00d4ff; }
.readme-body { padding: 20px; font-family: var(--font-sans); }

.readme-h1 { color: #ffffff; font-size: 22px; font-weight: 600; margin-bottom: 6px; }
.readme-h2 { color: #c8d3e0; font-size: 16px; font-weight: 500; margin: 20px 0 10px; border-bottom: 0.5px solid #1a2332; padding-bottom: 8px; }
.readme-h3 { color: #8892a4; font-size: 13px; font-weight: 500; margin: 14px 0 6px; }
.readme-p { color: #6b7280; font-size: 13px; line-height: 1.7; margin-bottom: 10px; }
.readme-code {
  background: #06090f; border: 0.5px solid #1a2332; border-radius: 6px;
  padding: 12px 14px; font-family: var(--font-mono); font-size: 11px;
  color: #10b981; margin: 10px 0; line-height: 1.7;
}
.readme-badge-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
.readme-badge { border-radius: 4px; overflow: hidden; display: inline-flex; font-size: 10px; font-family: var(--font-mono); }
.rb-label { background: #2d3748; color: #9ca3af; padding: 3px 7px; }
.rb-val { padding: 3px 7px; }
.rb-blue { background: #1e40af; color: #93c5fd; }
.rb-green { background: #065f46; color: #6ee7b7; }
.rb-amber { background: #92400e; color: #fcd34d; }

.arch-section { margin-top: 16px; }
.arch-box {
  border: 0.5px solid #1a2332; border-radius: 8px; padding: 12px 14px;
  background: rgba(255,255,255,0.02); margin-bottom: 8px;
}
.arch-row { display: flex; align-items: center; gap: 10px; }
.arch-label { color: #4a5568; font-size: 10px; font-family: var(--font-mono); min-width: 90px; }
.arch-items { display: flex; gap: 6px; flex-wrap: wrap; }
.arch-item {
  background: rgba(0,212,255,0.07); border: 0.5px solid rgba(0,212,255,0.2);
  color: #00d4ff; font-size: 10px; font-family: var(--font-mono);
  padding: 3px 9px; border-radius: 4px;
}
.arch-item.g { background: rgba(16,185,129,0.07); border-color: rgba(16,185,129,0.2); color: #10b981; }
.arch-item.a { background: rgba(245,158,11,0.07); border-color: rgba(245,158,11,0.2); color: #f59e0b; }
.arch-arrow { color: #2d3748; font-size: 16px; text-align: center; margin: 2px 0; }

.folder-tree { font-family: var(--font-mono); font-size: 11px; line-height: 1.9; color: #4a5568; }
.folder-tree .dir { color: #00d4ff; }
.folder-tree .file { color: #6b7280; }
.folder-tree .comment { color: #2d3748; }

.compare-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.compare-table th { color: #4a5568; font-family: var(--font-mono); padding: 8px 10px; text-align: left; border-bottom: 0.5px solid #1a2332; font-weight: 500; }
.compare-table td { color: #6b7280; font-family: var(--font-sans); padding: 8px 10px; border-bottom: 0.5px solid #0d1521; }
.compare-table td.check { color: #10b981; text-align: center; font-size: 14px; }
.compare-table td.cross { color: #ef4444; text-align: center; font-size: 14px; }
.compare-table td.name { color: #c8d3e0; font-weight: 500; }
.compare-table tr:last-child td { border-bottom: none; }

.cta-row { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
.btn {
  padding: 9px 18px; border-radius: 6px; font-size: 12px; font-family: var(--font-sans);
  cursor: pointer; border: none; font-weight: 500; transition: opacity 0.15s;
}
.btn:hover { opacity: 0.85; }
.btn-primary { background: #00d4ff; color: #06090f; }
.btn-secondary { background: transparent; color: #00d4ff; border: 0.5px solid #00d4ff; }
.btn-ghost { background: rgba(255,255,255,0.05); color: #8892a4; border: 0.5px solid #1a2332; }

.tabs { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 16px; }
.tab-btn {
  background: rgba(255,255,255,0.03); border: 0.5px solid #1a2332;
  color: #4a5568; font-size: 11px; padding: 5px 12px; border-radius: 4px;
  cursor: pointer; transition: all 0.15s; font-family: var(--font-mono);
}
.tab-btn:hover { color: #8892a4; }
.tab-btn.active { background: rgba(0,212,255,0.1); border-color: rgba(0,212,255,0.3); color: #00d4ff; }

.panel { display: none; }
.panel.active { display: block; }

.roadmap-item { display: flex; gap: 12px; margin-bottom: 12px; align-items: flex-start; }
.roadmap-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
.roadmap-content { flex: 1; }
.roadmap-title { color: #c8d3e0; font-size: 12px; font-family: var(--font-sans); font-weight: 500; }
.roadmap-sub { color: #4a5568; font-size: 11px; font-family: var(--font-sans); }

.divider { border: none; border-top: 0.5px solid #1a2332; margin: 24px 0; }
</style>

<div class="hero">
  <div class="hero-grid"></div>
  <div class="hero-glow"></div>
  <div class="hero-glow2"></div>

  <div class="badge">
    <span class="badge-dot"></span>
    ANDROID OPERATIONS PLATFORM
  </div>

  <div class="hero-title">MEGA<span>SUS</span> PRO</div>
  <div class="hero-version">v1.0.0 — STABLE</div>
  <div class="hero-tagline">Enterprise-grade Android device operations center. Fleet management, deep automation, and full device telemetry — from a single unified CLI.</div>

  <div class="hero-stats">
    <div class="stat"><span class="stat-val">10</span><span class="stat-label">MODULES</span></div>
    <div class="stat"><span class="stat-val">90+</span><span class="stat-label">OPERATIONS</span></div>
    <div class="stat"><span class="stat-val">USB+WiFi</span><span class="stat-label">CONNECTIVITY</span></div>
    <div class="stat"><span class="stat-val">ADB</span><span class="stat-label">NATIVE ENGINE</span></div>
  </div>

  <div class="section-label">// MODULES</div>
  <div class="module-grid" id="moduleGrid">
    <div class="module-card active" onclick="selectModule(0)" data-module="0">
      <div class="module-icon">🔗</div>
      <div class="module-name">Connection Manager</div>
    </div>
    <div class="module-card" onclick="selectModule(1)" data-module="1">
      <div class="module-icon">📱</div>
      <div class="module-name">Device Info & Control</div>
    </div>
    <div class="module-card" onclick="selectModule(2)" data-module="2">
      <div class="module-icon">📦</div>
      <div class="module-name">App Management</div>
    </div>
    <div class="module-card" onclick="selectModule(3)" data-module="3">
      <div class="module-icon">📁</div>
      <div class="module-name">File Manager</div>
    </div>
    <div class="module-card" onclick="selectModule(4)" data-module="4">
      <div class="module-icon">💾</div>
      <div class="module-name">Data Extraction</div>
    </div>
    <div class="module-card" onclick="selectModule(5)" data-module="5">
      <div class="module-icon">🖥</div>
      <div class="module-name">Screen Tools</div>
    </div>
    <div class="module-card" onclick="selectModule(6)" data-module="6">
      <div class="module-icon">🌐</div>
      <div class="module-name">Network Tools</div>
    </div>
    <div class="module-card" onclick="selectModule(7)" data-module="7">
      <div class="module-icon">🔒</div>
      <div class="module-name">Security Audit</div>
    </div>
    <div class="module-card" onclick="selectModule(8)" data-module="8">
      <div class="module-icon">👁</div>
      <div class="module-name">Surveillance</div>
    </div>
    <div class="module-card" onclick="selectModule(9)" data-module="9">
      <div class="module-icon">⚡</div>
      <div class="module-name">Automation</div>
    </div>
  </div>

  <div class="preview-area">
    <div class="preview-topbar">
      <div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div>
      <div class="preview-title" id="previewTitle">megasus — connection_manager</div>
    </div>
    <div class="preview-content" id="previewContent">
      <span style="color:#00d4ff">●</span> <span style="color:#10b981">CONNECTED</span> <span style="color:#4a5568">—</span> <span style="color:#8892a4">1 device active</span><br>
      <span style="color:#4a5568">┌─</span> <span style="color:#00d4ff">CONNECTION MANAGER</span><br>
      <span style="color:#4a5568">│</span><br>
      <span style="color:#4a5568">│ </span><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">Refresh device list</span><br>
      <span style="color:#4a5568">│ </span><span style="color:#10b981">[2]</span> <span style="color:#c8d3e0">Set active device</span><br>
      <span style="color:#4a5568">│ </span><span style="color:#10b981">[3]</span> <span style="color:#c8d3e0">Connect wireless (WiFi ADB)</span><br>
      <span style="color:#4a5568">│ </span><span style="color:#10b981">[4]</span> <span style="color:#c8d3e0">Switch TCP/IP → USB</span><br>
      <span style="color:#4a5568">│ </span><span style="color:#10b981">[5]</span> <span style="color:#c8d3e0">Restart ADB server</span><br>
      <span style="color:#4a5568">│ </span><span style="color:#10b981">[6]</span> <span style="color:#c8d3e0">List all with details</span><br>
      <span style="color:#4a5568">│</span><br>
      <span style="color:#4a5568">└─ </span><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>
    </div>
  </div>
</div>

<div style="margin-top: 20px;">
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('readme')">README</button>
    <button class="tab-btn" onclick="switchTab('modules')">Module Cards</button>
    <button class="tab-btn" onclick="switchTab('arch')">Architecture</button>
    <button class="tab-btn" onclick="switchTab('folder')">Folder Structure</button>
    <button class="tab-btn" onclick="switchTab('compare')">Feature Compare</button>
    <button class="tab-btn" onclick="switchTab('roadmap')">Roadmap</button>
    <button class="tab-btn" onclick="switchTab('branding')">Brand Guidelines</button>
  </div>

  <div id="tab-readme" class="panel active">
    <div class="readme-section">
      <div class="readme-tab-bar">
        <span class="readme-tab active">README.md</span>
        <span class="readme-tab" style="cursor:default">Code</span>
        <span class="readme-tab" style="cursor:default">Wiki</span>
      </div>
      <div class="readme-body">
        <div class="readme-badge-row">
          <span class="readme-badge"><span class="rb-label">release</span><span class="rb-val rb-blue">v1.0.0</span></span>
          <span class="readme-badge"><span class="rb-label">python</span><span class="rb-val rb-blue">3.8+</span></span>
          <span class="readme-badge"><span class="rb-label">license</span><span class="rb-val rb-green">MIT</span></span>
          <span class="readme-badge"><span class="rb-label">platform</span><span class="rb-val rb-amber">Android 8+</span></span>
          <span class="readme-badge"><span class="rb-label">stars</span><span class="rb-val" style="background:#7c3aed;color:#c4b5fd">⭐ give us one</span></span>
        </div>

        <div class="readme-h1">MEGASUS PRO</div>
        <div class="readme-p" style="color:#8892a4; font-family:var(--font-mono); font-size:12px; margin-bottom:14px;">Android Device Operations Platform · Fleet Management · Deep Automation · Device Telemetry</div>
        <div class="readme-p">MEGASUS PRO is an enterprise-grade, open-source Android operations platform built on ADB. Manage single devices or entire fleets, automate repetitive workflows, audit device security posture, and extract comprehensive telemetry — all from a clean, unified terminal interface.</div>

        <div class="readme-h2">Quick Start</div>
        <div class="readme-code">
# Clone the repository<br>
git clone https://github.com/yourusername/megasus-pro.git<br>
cd megasus-pro<br><br>
# Install dependencies<br>
pip install -r requirements.txt<br><br>
# Launch<br>
python megasus.py
        </div>

        <div class="readme-h2">Requirements</div>
        <div class="readme-p">Python 3.8+ · ADB installed and in PATH · Android Debug Bridge enabled on target device(s)</div>

        <div class="readme-h2">Modules</div>
        <div class="readme-p">10 specialized operations modules covering the full Android device lifecycle — from connection and fleet management to deep automation and security compliance auditing.</div>

        <div class="readme-h2">Documentation</div>
        <div class="readme-p">Full documentation available in the <span style="color:#00d4ff; font-family:var(--font-mono)">docs/</span> directory. See the <span style="color:#00d4ff; font-family:var(--font-mono)">wiki</span> for module-specific guides, advanced configuration, and plugin development.</div>

        <div class="cta-row">
          <button class="btn btn-primary" onclick="sendPrompt('Give me the full README.md content for MEGASUS PRO in markdown format')">Generate full README.md ↗</button>
          <button class="btn btn-secondary" onclick="sendPrompt('Write the MEGASUS PRO wiki documentation structure')">Wiki structure ↗</button>
        </div>
      </div>
    </div>
  </div>

  <div id="tab-modules" class="panel">
    <div class="feature-grid">
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(0,212,255,0.1)">🔗</div>
          <div class="feature-name">Connection Manager</div>
        </div>
        <div class="feature-desc">Multi-device fleet orchestration over USB and wireless ADB. Auto-discovery, session persistence, and connection health monitoring.</div>
        <div class="feature-tags">
          <span class="tag">USB</span><span class="tag">WiFi ADB</span><span class="tag">TCP/IP</span><span class="tag green">Fleet</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(16,185,129,0.1)">📱</div>
          <div class="feature-name">Device Info & Control</div>
        </div>
        <div class="feature-desc">Complete device telemetry dashboard. Battery, CPU, RAM, storage, screen, SELinux posture, build properties, and full hardware dump.</div>
        <div class="feature-tags">
          <span class="tag green">Telemetry</span><span class="tag">CPU/RAM</span><span class="tag">SELinux</span><span class="tag amber">Control</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(245,158,11,0.1)">📦</div>
          <div class="feature-name">App Management</div>
        </div>
        <div class="feature-desc">Full APK lifecycle management. Bulk install, freeze/unfreeze, permission auditing, sideload from folder, and background process control.</div>
        <div class="feature-tags">
          <span class="tag">APK deploy</span><span class="tag amber">Freeze/Thaw</span><span class="tag">Permissions</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(139,92,246,0.1)">📁</div>
          <div class="feature-name">File Manager</div>
        </div>
        <div class="feature-desc">Bidirectional file operations across device storage. Push, pull, browse, and manage files with path-aware navigation for Android's full filesystem.</div>
        <div class="feature-tags">
          <span class="tag">Push/Pull</span><span class="tag">Browse</span><span class="tag">SDCARD</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(236,72,153,0.1)">💾</div>
          <div class="feature-name">Data Extraction</div>
        </div>
        <div class="feature-desc">Structured export of device data — contacts, SMS, call logs, media inventory, active notifications, and registered accounts in machine-readable formats.</div>
        <div class="feature-tags">
          <span class="tag">Contacts</span><span class="tag">SMS</span><span class="tag amber">Backup</span><span class="tag">Accounts</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(0,212,255,0.1)">🖥</div>
          <div class="feature-name">Screen Tools</div>
        </div>
        <div class="feature-desc">Remote display control and input simulation. Screenshot, screen record, mirror via scrcpy, coordinate-based tap/swipe, and remote text injection.</div>
        <div class="feature-tags">
          <span class="tag">scrcpy</span><span class="tag">Record</span><span class="tag green">Mirror</span><span class="tag">Input</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(16,185,129,0.1)">🌐</div>
          <div class="feature-name">Network Tools</div>
        </div>
        <div class="feature-desc">Network diagnostics and configuration. IP inspection, WiFi scanning, port analysis, DNS queries, proxy management, traceroute, and data usage stats.</div>
        <div class="feature-tags">
          <span class="tag green">Network</span><span class="tag">Port scan</span><span class="tag">DNS</span><span class="tag">Proxy</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(245,158,11,0.1)">🔒</div>
          <div class="feature-name">Security Audit</div>
        </div>
        <div class="feature-desc">Comprehensive device security posture assessment. Root detection, Magisk/Frida detection, encryption status, SELinux, patch level, and permission compliance audit.</div>
        <div class="feature-tags">
          <span class="tag amber">Audit</span><span class="tag">Root detect</span><span class="tag">SELinux</span><span class="tag">Compliance</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(239,68,68,0.1)">👁</div>
          <div class="feature-name">Surveillance & Monitoring</div>
        </div>
        <div class="feature-desc">Device observability suite. GPS tracking, sensor enumeration, notification monitoring, location services inspection, and full device state dump to file.</div>
        <div class="feature-tags">
          <span class="tag">GPS</span><span class="tag">Sensors</span><span class="tag amber">Notifications</span>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-card-header">
          <div class="feature-icon" style="background:rgba(16,185,129,0.1)">⚡</div>
          <div class="feature-name">Automation & Scripts</div>
        </div>
        <div class="feature-desc">Macro engine for repeatable workflows. Custom ADB shell commands, batch execution, script files, key simulation, macro library, and ADB backup/restore.</div>
        <div class="feature-tags">
          <span class="tag green">Macros</span><span class="tag">Batch</span><span class="tag">Scripting</span><span class="tag">Backup</span>
        </div>
      </div>
    </div>
    <div class="cta-row" style="margin-top:16px">
      <button class="btn btn-primary" onclick="sendPrompt('Write detailed GitHub wiki documentation for all 10 MEGASUS PRO modules with usage examples')">Generate module docs ↗</button>
    </div>
  </div>

  <div id="tab-arch" class="panel">
    <div class="arch-section">
      <div class="section-label">// SYSTEM ARCHITECTURE</div>
      <div class="arch-box">
        <div class="arch-row">
          <div class="arch-label">CLI LAYER</div>
          <div class="arch-items">
            <span class="arch-item">megasus.py</span>
            <span class="arch-item">config.yaml</span>
            <span class="arch-item">plugins/</span>
          </div>
        </div>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-box">
        <div class="arch-row">
          <div class="arch-label">MODULE LAYER</div>
          <div class="arch-items">
            <span class="arch-item">connection</span>
            <span class="arch-item">device_info</span>
            <span class="arch-item">app_mgmt</span>
            <span class="arch-item">file_mgr</span>
            <span class="arch-item">data_extract</span>
            <span class="arch-item">screen</span>
            <span class="arch-item">network</span>
            <span class="arch-item">security</span>
            <span class="arch-item">surveillance</span>
            <span class="arch-item">automation</span>
          </div>
        </div>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-box">
        <div class="arch-row">
          <div class="arch-label">CORE LAYER</div>
          <div class="arch-items">
            <span class="arch-item g">ADB Engine</span>
            <span class="arch-item g">Shell Runner</span>
            <span class="arch-item g">Device Registry</span>
            <span class="arch-item g">Audit Logger</span>
          </div>
        </div>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-box">
        <div class="arch-row">
          <div class="arch-label">ANDROID</div>
          <div class="arch-items">
            <span class="arch-item a">ADB Daemon</span>
            <span class="arch-item a">Device Shell</span>
            <span class="arch-item a">USB / TCP</span>
          </div>
        </div>
      </div>

      <div class="cta-row" style="margin-top:16px">
        <button class="btn btn-primary" onclick="sendPrompt('Create a detailed SVG architecture diagram for MEGASUS PRO showing the full system layers')">Render full arch diagram ↗</button>
      </div>
    </div>
  </div>

  <div id="tab-folder" class="panel">
    <div class="preview-area">
      <div class="preview-topbar">
        <div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div>
        <div class="preview-title">megasus-pro/ — repository structure</div>
      </div>
      <div class="preview-content">
        <div class="folder-tree">
<span class="dir">megasus-pro/</span><br>
<span class="dir">├── core/</span>          <span class="comment"># Engine: ADB runner, registry, logger</span><br>
<span class="dir">├── modules/</span>       <span class="comment"># 10 operational modules</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">connection_manager.py</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">device_info.py</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">app_management.py</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">file_manager.py</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">data_extraction.py</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">screen_tools.py</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">network_tools.py</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">security_audit.py</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">surveillance.py</span><br>
<span style="color:#4a5568">│   └── </span><span class="file">automation.py</span><br>
<span class="dir">├── dashboard/</span>     <span class="comment"># Optional web dashboard</span><br>
<span class="dir">├── plugins/</span>       <span class="comment"># Community extensions</span><br>
<span class="dir">├── docs/</span>          <span class="comment"># Full documentation</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">quickstart.md</span><br>
<span style="color:#4a5568">│   ├── </span><span class="file">modules/</span><br>
<span style="color:#4a5568">│   └── </span><span class="file">api-reference.md</span><br>
<span class="dir">├── logs/</span>          <span class="comment"># Audit trail</span><br>
<span class="dir">├── screenshot/</span>    <span class="comment"># Demo assets</span><br>
<span class="file">├── megasus.py</span>     <span class="comment"># Entry point</span><br>
<span class="file">├── config.yaml</span>    <span class="comment"># Configuration</span><br>
<span class="file">├── requirements.txt</span><br>
<span class="file">└── README.md</span>
        </div>
      </div>
    </div>
  </div>

  <div id="tab-compare" class="panel">
    <div class="preview-area" style="min-height:auto">
      <div class="preview-topbar">
        <div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div>
        <div class="preview-title">feature comparison</div>
      </div>
      <div style="padding:16px;overflow-x:auto">
        <table class="compare-table">
          <tr>
            <th>Feature</th>
            <th>MEGASUS PRO</th>
            <th>Plain ADB CLI</th>
            <th>Scrcpy</th>
            <th>Vysor (paid)</th>
          </tr>
          <tr><td class="name">Unified module system</td><td class="check">✓</td><td class="cross">✗</td><td class="cross">✗</td><td class="cross">✗</td></tr>
          <tr><td class="name">Multi-device fleet</td><td class="check">✓</td><td class="check">✓</td><td class="cross">✗</td><td class="cross">✗</td></tr>
          <tr><td class="name">App freeze / lifecycle</td><td class="check">✓</td><td class="cross">✗</td><td class="cross">✗</td><td class="cross">✗</td></tr>
          <tr><td class="name">Security audit</td><td class="check">✓</td><td class="cross">✗</td><td class="cross">✗</td><td class="cross">✗</td></tr>
          <tr><td class="name">Macro automation</td><td class="check">✓</td><td class="cross">✗</td><td class="cross">✗</td><td class="cross">✗</td></tr>
          <tr><td class="name">Screen mirror</td><td class="check">✓</td><td class="cross">✗</td><td class="check">✓</td><td class="check">✓</td></tr>
          <tr><td class="name">GPS / sensor monitoring</td><td class="check">✓</td><td class="cross">✗</td><td class="cross">✗</td><td class="cross">✗</td></tr>
          <tr><td class="name">Open source</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td><td class="cross">✗</td></tr>
          <tr><td class="name">Plugin system</td><td class="check">✓</td><td class="cross">✗</td><td class="cross">✗</td><td class="cross">✗</td></tr>
          <tr><td class="name">Audit logging</td><td class="check">✓</td><td class="cross">✗</td><td class="cross">✗</td><td class="cross">✗</td></tr>
        </table>
      </div>
    </div>
  </div>

  <div id="tab-roadmap" class="panel">
    <div class="section-label">// v1.0 — SHIPPED</div>
    <div class="roadmap-item"><div class="roadmap-dot" style="background:#10b981"></div><div class="roadmap-content"><div class="roadmap-title">10 core modules — complete</div><div class="roadmap-sub">Connection, Device, Apps, Files, Data, Screen, Network, Security, Surveillance, Automation</div></div></div>
    <div class="roadmap-item"><div class="roadmap-dot" style="background:#10b981"></div><div class="roadmap-content"><div class="roadmap-title">Audit logging system</div><div class="roadmap-sub">All operations logged with timestamp and device ID</div></div></div>
    <div class="roadmap-item"><div class="roadmap-dot" style="background:#10b981"></div><div class="roadmap-content"><div class="roadmap-title">Plugin architecture</div><div class="roadmap-sub">Community modules via plugins/ directory</div></div></div>

    <div class="section-label" style="margin-top:20px">// v1.1 — IN PROGRESS</div>
    <div class="roadmap-item"><div class="roadmap-dot" style="background:#00d4ff"></div><div class="roadmap-content"><div class="roadmap-title">Web dashboard (optional)</div><div class="roadmap-sub">Browser-based UI via dashboard/ — wraps the CLI modules</div></div></div>
    <div class="roadmap-item"><div class="roadmap-dot" style="background:#00d4ff"></div><div class="roadmap-content"><div class="roadmap-title">Config profiles per device</div><div class="roadmap-sub">Device-specific config.yaml overrides</div></div></div>

    <div class="section-label" style="margin-top:20px">// v2.0 — PLANNED</div>
    <div class="roadmap-item"><div class="roadmap-dot" style="background:#4a5568"></div><div class="roadmap-content"><div class="roadmap-title">Docker deployment</div><div class="roadmap-sub">Containerised ADB server + MEGASUS for CI/CD pipelines</div></div></div>
    <div class="roadmap-item"><div class="roadmap-dot" style="background:#4a5568"></div><div class="roadmap-content"><div class="roadmap-title">REST API mode</div><div class="roadmap-sub">Expose all modules as a local HTTP API for integration</div></div></div>
    <div class="roadmap-item"><div class="roadmap-dot" style="background:#4a5568"></div><div class="roadmap-content"><div class="roadmap-title">Fleet scheduling</div><div class="roadmap-sub">Cron-style automation across multiple connected devices</div></div></div>

    <div class="cta-row" style="margin-top:16px">
      <button class="btn btn-primary" onclick="sendPrompt('Write a detailed MEGASUS PRO GitHub roadmap in markdown format with milestones and issue labels')">Generate roadmap.md ↗</button>
    </div>
  </div>

  <div id="tab-branding" class="panel">
    <div class="section-label">// COLOR PALETTE</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px">
      <div style="text-align:center"><div style="width:56px;height:56px;background:#00d4ff;border-radius:8px;margin-bottom:4px"></div><div style="color:#4a5568;font-size:10px;font-family:var(--font-mono)">#00d4ff<br>Cyber Blue</div></div>
      <div style="text-align:center"><div style="width:56px;height:56px;background:#10b981;border-radius:8px;margin-bottom:4px"></div><div style="color:#4a5568;font-size:10px;font-family:var(--font-mono)">#10b981<br>Emerald</div></div>
      <div style="text-align:center"><div style="width:56px;height:56px;background:#f59e0b;border-radius:8px;margin-bottom:4px"></div><div style="color:#4a5568;font-size:10px;font-family:var(--font-mono)">#f59e0b<br>Amber Alert</div></div>
      <div style="text-align:center"><div style="width:56px;height:56px;background:#0a0e17;border-radius:8px;margin-bottom:4px;border:0.5px solid #1a2332"></div><div style="color:#4a5568;font-size:10px;font-family:var(--font-mono)">#0a0e17<br>Void Black</div></div>
      <div style="text-align:center"><div style="width:56px;height:56px;background:#06090f;border-radius:8px;margin-bottom:4px;border:0.5px solid #1a2332"></div><div style="color:#4a5568;font-size:10px;font-family:var(--font-mono)">#06090f<br>Deep Space</div></div>
      <div style="text-align:center"><div style="width:56px;height:56px;background:#c8d3e0;border-radius:8px;margin-bottom:4px"></div><div style="color:#4a5568;font-size:10px;font-family:var(--font-mono)">#c8d3e0<br>Terminal White</div></div>
    </div>

    <div class="section-label">// TYPOGRAPHY</div>
    <div class="readme-p">Display: <span style="color:#00d4ff;font-family:var(--font-mono)">var(--font-sans) bold 700</span> — MEGASUS wordmark, hero titles</div>
    <div class="readme-p">Body: <span style="color:#00d4ff;font-family:var(--font-mono)">var(--font-sans) regular 400</span> — Descriptions, documentation</div>
    <div class="readme-p">Code/Terminal: <span style="color:#00d4ff;font-family:var(--font-mono)">var(--font-mono)</span> — All CLI output, labels, badges</div>

    <div class="section-label" style="margin-top:16px">// HERO BANNER PROMPT (for AI image generation)</div>
    <div class="readme-code" style="font-size:10px;color:#8892a4;line-height:1.9">
      Ultra-wide enterprise software hero banner, 16:9, cinematic dark theme.<br>
      Deep space background #0a0e17 with subtle cyan grid overlay.<br>
      Center: sleek floating terminal window showing green/cyan ADB output.<br>
      Android device silhouettes (phones/tablets) connected by glowing data streams.<br>
      Left panel: device fleet topology with node-and-edge network graph.<br>
      Right panel: scrolling telemetry — battery, CPU, network stats in monospace.<br>
      Accent colors: #00d4ff cyan, #10b981 emerald, #f59e0b amber for alerts.<br>
      Style: Cloudflare dashboard meets Grafana operations center.<br>
      NO skulls, NO hacker aesthetics, NO red attack graphics.<br>
      Professional, enterprise, open-source SaaS quality.<br>
      Text overlay: "MEGASUS PRO" in bold geometric sans-serif.
    </div>

    <div class="section-label" style="margin-top:16px">// DO / DON'T</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="feature-card">
        <div style="color:#10b981;font-size:11px;font-family:var(--font-mono);margin-bottom:8px">✓ DO</div>
        <div class="readme-p">Use "Android Operations Platform"</div>
        <div class="readme-p">Use "Device Fleet Management"</div>
        <div class="readme-p">Use "Security Audit & Compliance"</div>
        <div class="readme-p">Dark terminal mockups in screenshots</div>
        <div class="readme-p">MacBook + terminal frame for showcase</div>
      </div>
      <div class="feature-card">
        <div style="color:#ef4444;font-size:11px;font-family:var(--font-mono);margin-bottom:8px">✗ DON'T</div>
        <div class="readme-p">Call it an "ADB tool" or "hacking tool"</div>
        <div class="readme-p">Use hacker skulls or red attack graphics</div>
        <div class="readme-p">Say "spyware" or "RAT" or "pentest kit"</div>
        <div class="readme-p">Use Anonymous masks in any visual</div>
        <div class="readme-p">Position "Surveillance" as primary feature</div>
      </div>
    </div>

    <div class="cta-row" style="margin-top:16px">
      <button class="btn btn-primary" onclick="sendPrompt('Write GitHub social preview image design specs and a landing page wireframe for MEGASUS PRO')">Landing page wireframe ↗</button>
      <button class="btn btn-ghost" onclick="sendPrompt('Write CONTRIBUTING.md and CODE_OF_CONDUCT.md for MEGASUS PRO open source project')">Contributing docs ↗</button>
    </div>
  </div>
</div>

<script>
const moduleData = [
  { name:'connection_manager', preview: `<span style="color:#00d4ff">●</span> <span style="color:#10b981">CONNECTED</span> <span style="color:#4a5568">—</span> <span style="color:#8892a4">1 device active</span><br><span style="color:#4a5568">┌─</span> <span style="color:#00d4ff">CONNECTION MANAGER</span><br><span style="color:#4a5568">│ </span><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">Refresh device list</span><br><span style="color:#4a5568">│ </span><span style="color:#10b981">[2]</span> <span style="color:#c8d3e0">Set active device</span><br><span style="color:#4a5568">│ </span><span style="color:#10b981">[3]</span> <span style="color:#c8d3e0">Connect wireless (WiFi ADB)</span><br><span style="color:#4a5568">└─ </span><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'device_info', preview: `<span style="color:#00d4ff">▣</span> <span style="color:#00d4ff">DEVICE INFO & CONTROL</span><br><span style="color:#4a5568">Model:</span> <span style="color:#c8d3e0">SM-G991B</span><br><span style="color:#4a5568">Battery:</span> <span style="color:#10b981">76%</span> <span style="color:#4a5568">│ Temp:</span> <span style="color:#f59e0b">31°C</span><br><span style="color:#4a5568">CPU load:</span> <span style="color:#c8d3e0">15.77</span><br><span style="color:#4a5568">SELinux:</span> <span style="color:#10b981">Enforcing</span><br><br><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">Full device info</span> <span style="color:#10b981">[2]</span> <span style="color:#c8d3e0">Battery details</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'app_management', preview: `<span style="color:#f59e0b">📦</span> <span style="color:#00d4ff">APP MANAGEMENT</span><br><br><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">List all apps</span><br><span style="color:#10b981">[3]</span> <span style="color:#c8d3e0">List third-party apps</span><br><span style="color:#10b981">[6]</span> <span style="color:#c8d3e0">Install APK</span><br><span style="color:#10b981">[7]</span> <span style="color:#c8d3e0">Install all APKs from folder</span><br><span style="color:#10b981">[12]</span> <span style="color:#c8d3e0">Freeze app (disable)</span><br><span style="color:#10b981">[15]</span> <span style="color:#c8d3e0">Get dangerous permissions</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'file_manager', preview: `<span style="color:#f59e0b">📁</span> <span style="color:#00d4ff">FILE MANAGER</span><br><br><span style="color:#4a5568">Current path: /sdcard/</span><br><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">Browse device storage</span><br><span style="color:#10b981">[2]</span> <span style="color:#c8d3e0">Push file to device</span><br><span style="color:#10b981">[3]</span> <span style="color:#c8d3e0">Pull file from device</span><br><span style="color:#10b981">[4]</span> <span style="color:#c8d3e0">Delete file</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'data_extraction', preview: `<span style="color:#f59e0b">💾</span> <span style="color:#00d4ff">DATA EXTRACTION</span><br><br><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">Extract contacts</span><br><span style="color:#10b981">[2]</span> <span style="color:#c8d3e0">Extract SMS messages</span><br><span style="color:#10b981">[3]</span> <span style="color:#c8d3e0">Extract call logs</span><br><span style="color:#10b981">[8]</span> <span style="color:#c8d3e0">Get media files list</span><br><span style="color:#10b981">[10]</span> <span style="color:#c8d3e0">Get registered accounts</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'screen_tools', preview: `<span style="color:#f59e0b">🖥</span> <span style="color:#00d4ff">SCREEN TOOLS</span><br><br><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">Take screenshot</span><br><span style="color:#10b981">[2]</span> <span style="color:#c8d3e0">Record screen</span><br><span style="color:#10b981">[3]</span> <span style="color:#c8d3e0">Start screen mirror (scrcpy)</span><br><span style="color:#10b981">[9]</span> <span style="color:#c8d3e0">Tap at coordinates</span><br><span style="color:#10b981">[11]</span> <span style="color:#c8d3e0">Type text on device</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'network_tools', preview: `<span style="color:#10b981">🌐</span> <span style="color:#00d4ff">NETWORK TOOLS</span><br><br><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">Get IP addresses</span><br><span style="color:#10b981">[3]</span> <span style="color:#c8d3e0">Scan WiFi networks</span><br><span style="color:#10b981">[6]</span> <span style="color:#c8d3e0">Port scan (device itself)</span><br><span style="color:#10b981">[10]</span> <span style="color:#c8d3e0">Ping test</span><br><span style="color:#10b981">[11]</span> <span style="color:#c8d3e0">Traceroute</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'security_audit', preview: `<span style="color:#f59e0b">🔒</span> <span style="color:#00d4ff">SECURITY AUDIT</span><br><br><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">● FULL SECURITY AUDIT</span><br><span style="color:#10b981">[2]</span> <span style="color:#c8d3e0">Root detection</span><br><span style="color:#10b981">[4]</span> <span style="color:#c8d3e0">Check encryption status</span><br><span style="color:#10b981">[5]</span> <span style="color:#c8d3e0">Check security patch level</span><br><span style="color:#10b981">[12]</span> <span style="color:#c8d3e0">App permissions audit</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'surveillance_monitoring', preview: `<span style="color:#4a5568">👁</span> <span style="color:#00d4ff">SURVEILLANCE & MONITORING</span><br><br><span style="color:#10b981">[5]</span> <span style="color:#c8d3e0">Location services status</span><br><span style="color:#10b981">[6]</span> <span style="color:#c8d3e0">Start GPS tracking</span><br><span style="color:#10b981">[7]</span> <span style="color:#c8d3e0">Monitor notifications (real-time)</span><br><span style="color:#10b981">[9]</span> <span style="color:#c8d3e0">List device sensors</span><br><span style="color:#10b981">[10]</span> <span style="color:#c8d3e0">Full device dump to files</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` },
  { name:'automation_scripts', preview: `<span style="color:#10b981">⚡</span> <span style="color:#00d4ff">AUTOMATION & SCRIPTS</span><br><br><span style="color:#10b981">[1]</span> <span style="color:#c8d3e0">Run custom ADB shell command</span><br><span style="color:#10b981">[2]</span> <span style="color:#c8d3e0">Run batch commands</span><br><span style="color:#10b981">[4]</span> <span style="color:#c8d3e0">Create macro</span><br><span style="color:#10b981">[5]</span> <span style="color:#c8d3e0">Run macro</span><br><span style="color:#10b981">[11]</span> <span style="color:#c8d3e0">Create ADB backup</span><br><span style="color:#f59e0b">Choice:</span> <span style="color:#ffffff">█</span>` }
];

function selectModule(i) {
  document.querySelectorAll('.module-card').forEach((c,idx) => c.classList.toggle('active', idx===i));
  document.getElementById('previewTitle').textContent = 'megasus — ' + moduleData[i].name;
  document.getElementById('previewContent').innerHTML = moduleData[i].preview;
}

function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach((b,i) => {
    const panels = ['readme','modules','arch','folder','compare','roadmap','branding'];
    b.classList.toggle('active', panels[i]===name);
  });
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
}
</script>

## Contributors

### Core Team

| Name | Role | GitHub | Email |
|------|------|--------|-------|
| Suraj Singh | Founder & Lead Developer | [@shruhood](https://github.com/shruhood) | shruhood@gmail.com · ibakeweb@gmail.com |

### Organizations

MEGASUS is built by **Suraj Singh** across multiple ventures:

- **Bakweb** — [hello@bakeweb.in](mailto:hello@bakeweb.in) · [ibakeweb@gmail.com](mailto:ibakeweb@gmail.com) · [bakeweb.in](https://bakeweb.in)
- **SunDial Technologies** — [shruhood@gmail.com](mailto:shruhood@gmail.com)
- **Cyber SunDial** — [shruhood@gmail.com](mailto:shruhood@gmail.com)

### Links

- **GitHub:** [@shruhood](https://github.com/shruhood)
- **WhatsApp Channel:** [Join](https://whatsapp.com/channel/0029Vb7eYJP5PO0vRy786z46)

### Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

*Built with love by Suraj Singh — Bakweb · SunDial Technologies · Cyber SunDial*
