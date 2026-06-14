<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MEGASUS PRO — Android Operations Platform</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
      --cyan: #00f5ff;
      --emerald: #00ff9d;
      --amber: #ffcc00;
    }
    
    * { box-sizing: border-box; }
    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: #05060f;
      color: #e0f0ff;
      overflow-x: hidden;
    }
    
    .cyber-grid {
      background-image: 
        linear-gradient(rgba(0, 245, 255, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 245, 255, 0.08) 1px, transparent 1px);
      background-size: 40px 40px;
      animation: gridMove 25s linear infinite;
    }
    
    @keyframes gridMove {
      0% { background-position: 0 0; }
      100% { background-position: 40px 40px; }
    }
    
    .neon-text {
      text-shadow: 
        0 0 10px var(--cyan),
        0 0 20px var(--cyan),
        0 0 40px var(--cyan);
    }
    
    .hero {
      background: radial-gradient(circle at 30% 20%, rgba(0, 245, 255, 0.15) 0%, transparent 60%),
                  radial-gradient(circle at 70% 80%, rgba(0, 255, 157, 0.12) 0%, transparent 60%);
      border: 1px solid rgba(0, 245, 255, 0.3);
      box-shadow: 0 0 80px rgba(0, 245, 255, 0.15);
    }
    
    .module-card {
      transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
      backdrop-filter: blur(12px);
    }
    
    .module-card:hover {
      transform: translateY(-8px) scale(1.03);
      box-shadow: 0 0 40px rgba(0, 245, 255, 0.4);
      border-color: #00f5ff;
    }
    
    .terminal {
      font-family: 'JetBrains Mono', monospace;
      background: rgba(5, 6, 15, 0.95);
      border: 1px solid rgba(0, 245, 255, 0.4);
      box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.8);
    }
    
    .scanline {
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(transparent, rgba(0, 245, 255, 0.6), transparent);
      animation: scan 4s linear infinite;
      pointer-events: none;
      opacity: 0.15;
    }
    
    @keyframes scan { 0% { transform: translateY(-100%); } 100% { transform: translateY(800%); } }
    
    .glitch {
      animation: glitch 2s linear infinite;
    }
    
    @keyframes glitch {
      2%, 64% { transform: translate(2px,0) skew(0deg); }
      4%, 60% { transform: translate(-2px,0) skew(0deg); }
    }
  </style>
</head>
<body class="min-h-screen pb-24">
  <div class="cyber-grid absolute inset-0 z-0"></div>
  
  <!-- HERO -->
  <div class="hero relative max-w-6xl mx-auto mt-12 rounded-3xl p-16 overflow-hidden border border-cyan-500/30">
    <div class="scanline"></div>
    
    <div class="flex items-center gap-3 mb-6">
      <div class="px-4 py-1.5 bg-cyan-950/70 border border-cyan-400/50 rounded-full text-xs font-mono tracking-[3px] flex items-center gap-2">
        <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
        ANDROID OPERATIONS PLATFORM
      </div>
    </div>
    
    <h1 class="text-7xl font-bold tracking-tighter neon-text mb-4">
      MEGASUS <span class="text-cyan-400">PRO</span>
    </h1>
    <p class="text-2xl text-cyan-300/90 font-light mb-2">v1.0.0 • STABLE</p>
    
    <p class="max-w-2xl text-lg text-slate-400 leading-relaxed">
      Next-generation Android fleet command center.<br>
      Deep automation • Real-time telemetry • Enterprise security
    </p>
    
    <div class="flex gap-8 mt-12 text-sm font-mono">
      <div><span class="text-cyan-400 text-4xl font-semibold">10</span><br><span class="text-slate-500">MODULES</span></div>
      <div><span class="text-emerald-400 text-4xl font-semibold">90+</span><br><span class="text-slate-500">OPERATIONS</span></div>
      <div><span class="text-amber-400 text-4xl font-semibold">USB+WiFi</span><br><span class="text-slate-500">CONNECTIVITY</span></div>
    </div>
    
    <div class="mt-16 flex gap-4">
      <button onclick="launchDemo()" class="px-10 py-5 bg-cyan-400 hover:bg-cyan-300 text-black font-semibold rounded-2xl flex items-center gap-3 transition-all hover:scale-105">
        <i class="fa-solid fa-bolt"></i> LAUNCH CONSOLE
      </button>
      <button class="px-8 py-5 border border-cyan-400/50 hover:border-cyan-400 text-cyan-400 rounded-2xl transition-all hover:scale-105">
        VIEW DOCUMENTATION →
      </button>
    </div>
  </div>

  <!-- MODULES GRID -->
  <div class="max-w-6xl mx-auto mt-20 px-6">
    <div class="text-xs uppercase tracking-[4px] text-cyan-400/70 mb-8 font-mono">OPERATIONAL MODULES</div>
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4" id="moduleGrid">
      <!-- Populated by JS below -->
    </div>
  </div>

  <!-- TERMINAL PREVIEW -->
  <div class="max-w-5xl mx-auto mt-20 px-6">
    <div class="terminal rounded-3xl p-8 relative">
      <div class="flex items-center gap-3 mb-6 border-b border-cyan-900 pb-6">
        <div class="flex gap-2">
          <div class="w-4 h-4 rounded-full bg-red-500"></div>
          <div class="w-4 h-4 rounded-full bg-yellow-500"></div>
          <div class="w-4 h-4 rounded-full bg-emerald-500"></div>
        </div>
        <div class="font-mono text-xs text-cyan-400/70 flex-1 text-center">megasus-pro • root@device-001</div>
      </div>
      <div id="previewContent" class="font-mono text-sm leading-relaxed text-emerald-300 min-h-[260px]"></div>
    </div>
  </div>

  <script>
    const modules = [
      {icon:"🔗", name:"Connection Manager", color:"cyan"},
      {icon:"📱", name:"Device Info", color:"emerald"},
      {icon:"📦", name:"App Management", color:"amber"},
      {icon:"📁", name:"File System", color:"cyan"},
      {icon:"💾", name:"Data Extraction", color:"emerald"},
      {icon:"🖥️", name:"Screen Control", color:"amber"},
      {icon:"🌐", name:"Network Tools", color:"cyan"},
      {icon:"🔒", name:"Security Audit", color:"emerald"},
      {icon:"👁️", name:"Surveillance", color:"amber"},
      {icon:"⚡", name:"Automation", color:"cyan"}
    ];

    const moduleGrid = document.getElementById('moduleGrid');
    modules.forEach((m, i) => {
      const card = document.createElement('div');
      card.className = `module-card group bg-zinc-950/70 border border-zinc-800 hover:border-cyan-400 rounded-2xl p-6 cursor-pointer`;
      card.innerHTML = `
        <div class="text-4xl mb-4 transition-transform group-hover:scale-110">${m.icon}</div>
        <div class="font-semibold text-lg">${m.name}</div>
        <div class="text-xs text-zinc-500 mt-1 font-mono">MODULE ${String(i+1).padStart(2,'0')}</div>
      `;
      card.onclick = () => showPreview(i);
      moduleGrid.appendChild(card);
    });

    function showPreview(i) {
      const previews = [
        `<span class="text-cyan-400">● CONNECTED</span> <span class="text-emerald-400">device-001</span>\n<span class="text-zinc-500">┌─</span> <span class="text-cyan-400">CONNECTION MANAGER ACTIVE</span>\n[1] Refresh fleet    [3] Enable WiFi ADB`,
        `<span class="text-emerald-400">DEVICE TELEMETRY LIVE</span>\nModel: SM-G998B    Battery: <span class="text-emerald-400">87%</span>\nCPU: 12%    SELinux: <span class="text-emerald-400">ENFORCING</span>`,
        // ... add more as needed
      ];
      document.getElementById('previewContent').innerHTML = previews[i % previews.length] || "Module preview loaded.";
    }

    function launchDemo() {
      alert("🚀 MEGASUS PRO Console Launched (Demo Mode)\n\nIn real version this would open the full TUI.");
    }

    // Auto start first module
    setTimeout(() => showPreview(0), 800);
  </script>
</body>
</html>
