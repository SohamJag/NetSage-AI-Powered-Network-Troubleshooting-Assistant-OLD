import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, AlertTriangle, CheckCircle, Terminal, Cpu, HardDrive, 
  Download, Play, RefreshCw, Server, Database, TrendingUp, BarChart2, 
  ShieldAlert, Award, FileText, ChevronRight, X, Sparkles, Send, PlayCircle
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('noc'); // 'noc' or 'analytics'
  const [devices, setDevices] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [topology, setTopology] = useState({ nodes: [], links: [], impact_analysis: { affected_networks: [], affected_devices: [] } });
  const [simState, setSimState] = useState({ current_scenario: 0, scenario_name: 'Baseline' });
  const [analytics, setAnalytics] = useState(null);
  const [collecting, setCollecting] = useState(false);
  const [simulatingId, setSimulatingId] = useState(null);

  // Advanced features
  const [toasts, setToasts] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null); // Clicked node details
  const [cliDevice, setCliDevice] = useState('R1');
  const [cliCommand, setCliCommand] = useState('show ip route');
  const [cliOutput, setCliOutput] = useState('R1# show ip route\n(Select a device and command, then click "Execute CLI Command")');
  const [cliExecuting, setCliExecuting] = useState(false);
  
  const terminalEndRef = useRef(null);

  // Helper to add toast notifications
  const showToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4500);
  };

  // Poll database on load and refresh
  const fetchData = async (silent = false) => {
    if (!silent) setCollecting(true);
    try {
      // 1. Fetch devices
      const devRes = await fetch(`${API_BASE}/devices`);
      if (devRes.ok) setDevices(await devRes.json());

      // 2. Fetch incidents
      const incRes = await fetch(`${API_BASE}/incidents`);
      if (incRes.ok) {
        const incData = await incRes.json();
        setIncidents(incData);
        // Default select first open incident if none selected
        const firstOpen = incData.find(i => i.status === 'Open');
        if (firstOpen && !selectedIncident) {
          fetchIncidentDetail(firstOpen.incident_id);
        }
      }

      // 3. Fetch topology
      const topoRes = await fetch(`${API_BASE}/topology`);
      if (topoRes.ok) setTopology(await topoRes.json());

      // 4. Fetch simulation state
      const simRes = await fetch(`${API_BASE}/simulation/state`);
      if (simRes.ok) setSimState(await simRes.json());

      // 5. Fetch analytics
      const analyticsRes = await fetch(`${API_BASE}/analytics`);
      if (analyticsRes.ok) setAnalytics(await analyticsRes.json());

    } catch (err) {
      console.error("Error fetching NetSage telemetry:", err);
    } finally {
      if (!silent) setCollecting(false);
    }
  };

  const fetchIncidentDetail = async (incId) => {
    try {
      const res = await fetch(`${API_BASE}/incidents/${incId}`);
      if (res.ok) {
        setSelectedIncident(await res.json());
      }
    } catch (err) {
      console.error("Error loading incident details:", err);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh metrics every 15 seconds to simulate continuous telemetry
    const interval = setInterval(() => fetchData(true), 15000);
    return () => clearInterval(interval);
  }, []);

  const triggerManualCollection = async () => {
    showToast("Triggering full network assurance telemetry scan...", "info");
    setCollecting(true);
    try {
      const res = await fetch(`${API_BASE}/telemetry/collect`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        await fetchData(true);
        if (data.diagnoses && data.diagnoses.length > 0) {
          showToast(`Assurance Scan: ${data.diagnoses.length} fault(s) detected!`, "rose");
        } else {
          showToast("Assurance Scan complete. All nodes verified healthy.", "emerald");
        }
      }
    } catch (err) {
      console.error("Manual telemetry collection failed:", err);
      showToast("Telemetry scan failed. Check server log.", "rose");
    } finally {
      setCollecting(false);
    }
  };

  const triggerScenario = async (scenarioId) => {
    setSimulatingId(scenarioId);
    showToast(`Injecting Scenario ${scenarioId}: Simulating virtual fault state...`, "info");
    try {
      const res = await fetch(`${API_BASE}/simulation/scenario/${scenarioId}`, { method: 'POST' });
      if (res.ok) {
        setSelectedIncident(null);
        await fetchData(true);
        if (scenarioId === 0) {
          showToast("Virtual network state successfully restored to Baseline (Healthy)!", "emerald");
        } else {
          showToast(`Scenario active: ${topology.scenario_name || "Fault injected"}`, "amber");
        }
      }
    } catch (err) {
      console.error("Failed to run scenario:", err);
      showToast("Scenario trigger failed.", "rose");
    } finally {
      setSimulatingId(null);
    }
  };

  const executeCliCommand = async () => {
    setCliExecuting(true);
    setCliOutput(prev => prev + `\n\n${cliDevice}# ${cliCommand}\nExecuting...`);
    try {
      const res = await fetch(`${API_BASE}/terminal/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device: cliDevice, command: cliCommand })
      });
      if (res.ok) {
        const data = await res.json();
        setCliOutput(prev => prev + `\n${data.output}`);
      } else {
        setCliOutput(prev => prev + `\nError executing command. Code: ${res.status}`);
      }
    } catch (err) {
      setCliOutput(prev => prev + `\nError executing command: ${err.message}`);
    } finally {
      setCliExecuting(false);
      setTimeout(() => {
        if (terminalEndRef.current) {
          terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    }
  };

  // Status color mappings
  const getStatusBadge = (status) => {
    switch (status) {
      case 'Healthy':
        return <span className="badge badge-emerald"><CheckCircle size={10} /> Healthy</span>;
      case 'Warning':
        return <span className="badge badge-amber"><AlertTriangle size={10} /> Warning</span>;
      case 'Critical':
        return <span className="badge badge-rose"><AlertTriangle size={10} /> Critical</span>;
      default:
        return <span className="badge badge-cyan">{status}</span>;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'Critical':
      case 'High':
        return <span className="badge badge-rose font-bold text-[10px]">{severity}</span>;
      case 'Medium':
        return <span className="badge badge-amber font-bold text-[10px]">{severity}</span>;
      case 'Low':
      default:
        return <span className="badge badge-cyan text-[10px]">{severity}</span>;
    }
  };

  // Node visualization coordinates
  const getNodeCoordinates = (nodeId) => {
    const coords = {
      'Client01': { x: 60, y: 120, label: 'Client PC', desc: 'HO Client Host Subnet', ip: '192.168.1.50' },
      'Switch1': { x: 200, y: 120, label: 'HO Switch', desc: 'Headquarters Access Switch', ip: '192.168.1.2' },
      'R1': { x: 340, y: 120, label: 'R1 Router', desc: 'HO Gateway OSPF Core R1', ip: '192.168.12.1' },
      'R2': { x: 500, y: 120, label: 'R2 Router', desc: 'OSPF Core Transit R2', ip: '192.168.12.2' },
      'R3': { x: 660, y: 120, label: 'R3 Router', desc: 'Datacenter OSPF Core R3', ip: '192.168.23.2' },
      'Switch2': { x: 800, y: 120, label: 'DC Switch', desc: 'Datacenter Distribution Switch', ip: '192.168.4.2' },
      'Server01': { x: 940, y: 120, label: 'Application Server', desc: 'Core Enterprise Web Server', ip: '192.168.4.10' }
    };
    return coords[nodeId] || { x: 100, y: 100, label: nodeId, desc: '', ip: '' };
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#070b16] relative text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
      
      {/* Dynamic Toast Notifications */}
      <div className="fixed top-20 right-6 z-[9999] flex flex-col gap-2 max-w-sm pointer-events-none">
        {toasts.map(t => (
          <div 
            key={t.id} 
            className={`p-4 rounded-xl shadow-2xl backdrop-blur-xl border pointer-events-auto flex items-start gap-3 transition-all duration-300 transform translate-x-0 animate-slide-in ${
              t.type === 'emerald' ? 'bg-emerald-950/80 border-emerald-500/30 text-emerald-200' :
              t.type === 'rose' ? 'bg-rose-950/80 border-rose-500/30 text-rose-200' :
              t.type === 'amber' ? 'bg-amber-950/80 border-amber-500/30 text-amber-200' :
              'bg-[#0f172a]/90 border-cyan-500/30 text-cyan-200'
            }`}
          >
            {t.type === 'emerald' ? <CheckCircle size={18} className="text-emerald-400 shrink-0" /> :
             t.type === 'rose' ? <AlertTriangle size={18} className="text-rose-400 shrink-0" /> :
             t.type === 'amber' ? <AlertTriangle size={18} className="text-amber-400 shrink-0" /> :
             <Sparkles size={18} className="text-cyan-400 shrink-0 animate-spin" />}
            <span className="text-xs font-medium font-sans leading-relaxed">{t.message}</span>
          </div>
        ))}
      </div>

      {/* Top Banner & Header */}
      <header className="border-b border-white/5 bg-[#0b0e1a]/85 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/20">
              <Activity className="text-white animate-pulse" size={20} />
            </div>
            <div>
              <h1 className="text-2xl font-black tracking-wider text-white font-sans flex items-center gap-1.5">
                NET<span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">SAGE</span>
              </h1>
              <p className="text-[9px] tracking-widest text-slate-500 font-mono font-bold uppercase">AI-POWERED ASSURANCE &amp; NOC DIAGNOSTICS</p>
            </div>
          </div>

          <div className="flex items-center gap-4 flex-wrap">
            {/* Live simulation banner */}
            <div className="px-4 py-2 rounded-xl bg-slate-950/65 border border-white/5 flex items-center gap-3">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
              <div className="text-xs">
                <span className="text-[9px] text-slate-500 block font-mono uppercase tracking-widest">Active Simulator State</span>
                <strong className="text-cyan-300 font-semibold">{simState.scenario_name}</strong>
              </div>
            </div>

            <button 
              onClick={triggerManualCollection}
              disabled={collecting}
              className="btn-glass btn-cyan py-2.5 px-4 text-xs font-semibold"
            >
              <RefreshCw size={13} className={collecting ? "animate-spin text-cyan-400" : ""} />
              {collecting ? "Scanned Telemetry..." : "Run Assurance Cycle"}
            </button>
          </div>
        </div>
      </header>

      {/* Navigation tabs */}
      <div className="bg-[#080b15]/60 backdrop-blur border-b border-white/5">
        <div className="max-w-[1600px] mx-auto px-6 flex gap-4">
          <button 
            onClick={() => { setActiveTab('noc'); setSelectedNode(null); }}
            className={`py-4 px-3 text-sm font-semibold tracking-wide border-b-2 transition-all flex items-center gap-2 ${activeTab === 'noc' ? 'border-cyan-400 text-cyan-400 bg-cyan-950/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <Activity size={15} /> Real-Time NOC Monitor
          </button>
          <button 
            onClick={() => { setActiveTab('analytics'); setSelectedNode(null); }}
            className={`py-4 px-3 text-sm font-semibold tracking-wide border-b-2 transition-all flex items-center gap-2 ${activeTab === 'analytics' ? 'border-cyan-400 text-cyan-400 bg-cyan-950/5' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
          >
            <TrendingUp size={15} /> Historical Analytics &amp; Reports
          </button>
        </div>
      </div>

      {activeTab === 'noc' ? (
        <main className="dashboard-grid flex-1">
          {/* Main Visuals col */}
          <div className="col-span-12 lg:col-span-8 flex flex-col gap-5">
            {/* Interactive SVG Topology Map */}
            <div className="glass-panel p-6 flex flex-col min-h-[380px] relative overflow-hidden">
              <div className="flex items-center justify-between mb-4 z-10">
                <div>
                  <h3 className="font-bold text-lg text-slate-200 flex items-center gap-2">
                    <Database size={16} className="text-cyan-400" /> Monitored Enterprise Topology
                  </h3>
                  <p className="text-xs text-slate-400">Interactive live graph showing operational path, packet flows, and interface states</p>
                </div>
                <div className="flex items-center gap-3 text-[10px] font-mono text-slate-500 bg-slate-950/50 px-3 py-1.5 rounded-lg border border-white/5">
                  <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> Active</span>
                  <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-rose-400"></span> Broken</span>
                  <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span> Degraded</span>
                </div>
              </div>

              {/* SVG Canvas */}
              <div className="flex-1 bg-slate-950/20 rounded-xl border border-white/5 p-4 flex items-center justify-center relative min-h-[260px]">
                <svg className="w-full h-full min-h-[220px]" viewBox="0 0 1000 240">
                  {/* Arrow markers */}
                  <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 2 L 10 5 L 0 8 z" fill="#1e293b" />
                    </marker>
                    <marker id="arrow-active" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 2 L 10 5 L 0 8 z" fill="#06b6d4" />
                    </marker>
                  </defs>

                  {/* Draw connection links */}
                  {topology.links.map((link, idx) => {
                    const src = getNodeCoordinates(link.source);
                    const tgt = getNodeCoordinates(link.target);
                    
                    let strokeColor = '#1e293b';
                    let dashClass = '';
                    let glowColor = '';
                    
                    if (link.status === 'active') {
                      strokeColor = '#06b6d4';
                      glowColor = 'drop-shadow(0px 0px 4px rgba(6,182,212,0.3))';
                    } else if (link.status === 'broken') {
                      strokeColor = '#f43f5e';
                      dashClass = 'dash-link';
                      glowColor = 'drop-shadow(0px 0px 4px rgba(244,63,94,0.3))';
                    } else if (link.status === 'degraded') {
                      strokeColor = '#f59e0b';
                      dashClass = 'dash-link';
                      glowColor = 'drop-shadow(0px 0px 4px rgba(245,158,11,0.3))';
                    }

                    return (
                      <g key={idx} style={{ filter: glowColor }}>
                        {/* Interactive hover line */}
                        <line 
                          x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y} 
                          stroke="transparent" strokeWidth={15} className="cursor-pointer"
                        />
                        {/* Connection line */}
                        <line 
                          x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y} 
                          stroke={strokeColor} strokeWidth={2.5} 
                          className={dashClass}
                          markerEnd={link.status === 'active' ? "url(#arrow-active)" : "url(#arrow)"}
                        />

                        {/* Animated flowing packets along active link */}
                        {link.status === 'active' && (
                          <circle r={3.5} fill="#22d3ee" className="glow-cyan">
                            <animateMotion 
                              path={`M ${src.x} ${src.y} L ${tgt.x} ${tgt.y}`} 
                              dur={`${Math.max(1, Math.min(2.5, (idx + 1) * 0.4))}s`}
                              repeatCount="indefinite" 
                            />
                          </circle>
                        )}

                        {/* Link Label */}
                        {link.label && (
                          <text 
                            x={(src.x + tgt.x)/2} y={src.y - 12} 
                            fill="#475569" fontSize={9} textAnchor="middle" fontWeight="bold" className="font-mono"
                          >
                            {link.label}
                          </text>
                        )}
                        {/* Link failure indicator flag */}
                        {link.status !== 'active' && (
                          <g transform={`translate(${(src.x + tgt.x)/2 - 8}, ${src.y - 8})`}>
                            <rect width={16} height={16} rx={4} fill={link.status === 'broken' ? '#f43f5e' : '#f59e0b'} />
                            <text x={8} y={11} fill="#fff" fontSize={9} textAnchor="middle" fontWeight="bold">!</text>
                          </g>
                        )}
                      </g>
                    );
                  })}

                  {/* Draw Nodes */}
                  {topology.nodes.map((node) => {
                    const coord = getNodeCoordinates(node.id);
                    const isRouter = node.type === 'router';
                    const isSwitch = node.type === 'switch';
                    const isCritical = node.status === 'Critical';
                    const isWarning = node.status === 'Warning';
                    
                    let ringColor = 'rgba(30, 41, 59, 0.4)';
                    let nodeFill = '#0b0f19';
                    let neonBorder = '#334155';
                    
                    if (node.status === 'Healthy') {
                      ringColor = 'rgba(16, 185, 129, 0.15)';
                      nodeFill = '#070a12';
                      neonBorder = '#10b981';
                    } else if (isWarning) {
                      ringColor = 'rgba(245, 158, 11, 0.2)';
                      nodeFill = '#110d05';
                      neonBorder = '#f59e0b';
                    } else if (isCritical) {
                      ringColor = 'rgba(244, 63, 94, 0.25)';
                      nodeFill = '#14080a';
                      neonBorder = '#f43f5e';
                    }

                    return (
                      <g 
                        key={node.id} 
                        onClick={() => {
                          const info = getNodeCoordinates(node.id);
                          setSelectedNode({ ...node, ...info });
                          // Also auto-select device in terminal console if it is a router
                          if (isRouter) setCliDevice(node.id);
                        }}
                        className="cursor-pointer group"
                      >
                        {/* Glow ring */}
                        <circle cx={coord.x} cy={coord.y} r={28} fill={ringColor} className={isCritical ? "animate-pulse" : ""} />
                        
                        {/* Outer hover scale circle */}
                        <circle 
                          cx={coord.x} cy={coord.y} r={22} 
                          fill="transparent" stroke="rgba(6, 182, 212, 0.0)" strokeWidth={1} 
                          className="transition-all duration-300 group-hover:stroke-cyan-500/40 group-hover:r-[24]"
                        />

                        {/* Main circle */}
                        <circle cx={coord.x} cy={coord.y} r={19} fill={nodeFill} stroke={neonBorder} strokeWidth={2} />
                        
                        {/* Type Icon character representation */}
                        <text x={coord.x} y={coord.y + 4} fill={isCritical ? '#f43f5e' : (isWarning ? '#f59e0b' : '#64748b')} fontSize={10} fontWeight="black" textAnchor="middle" className="font-mono">
                          {isRouter ? 'RTR' : (isSwitch ? 'SW' : (node.type === 'server' ? 'SRV' : 'PC'))}
                        </text>

                        {/* Label */}
                        <text x={coord.x} y={coord.y + 36} fill="#f1f5f9" fontSize={10} textAnchor="middle" fontWeight="bold">
                          {coord.label}
                        </text>
                        {/* IP address subtitle */}
                        <text x={coord.x} y={coord.y + 46} fill="#475569" fontSize={9} textAnchor="middle" className="font-mono">
                          {node.ip}
                        </text>
                      </g>
                    );
                  })}
                </svg>

                {/* Floating Node Details Card drawer */}
                {selectedNode && (
                  <div className="absolute top-4 right-4 z-20 w-72 bg-[#090d16]/95 border border-cyan-500/20 rounded-xl p-4 shadow-2xl backdrop-blur-md animate-fade-in">
                    <div className="flex items-start justify-between border-b border-white/5 pb-2 mb-3">
                      <div>
                        <span className="text-[9px] font-mono text-cyan-400 font-bold uppercase tracking-wider">{selectedNode.type} ASSURANCE</span>
                        <h4 className="font-bold text-slate-200 text-sm">{selectedNode.label}</h4>
                      </div>
                      <button 
                        onClick={() => setSelectedNode(null)}
                        className="p-1 rounded-lg hover:bg-slate-900 border border-transparent hover:border-white/5 text-slate-400 hover:text-slate-200"
                      >
                        <X size={12} />
                      </button>
                    </div>

                    <div className="flex flex-col gap-2.5 text-xs">
                      <div className="flex justify-between items-center bg-slate-950/40 p-2 rounded border border-white/5">
                        <span className="text-slate-500 font-mono">Assigned IP:</span>
                        <strong className="text-slate-300 font-mono font-semibold">{selectedNode.ip}</strong>
                      </div>

                      <div className="flex justify-between items-center bg-slate-950/40 p-2 rounded border border-white/5">
                        <span className="text-slate-500 font-mono">Diagnostic State:</span>
                        {getStatusBadge(selectedNode.status)}
                      </div>

                      <div className="p-2 rounded bg-slate-950/40 border border-white/5 text-[10px] text-slate-400 italic">
                        {selectedNode.desc}
                      </div>

                      {selectedNode.type === 'router' && (
                        <div className="flex gap-2 mt-1">
                          <button 
                            onClick={() => {
                              setCliDevice(selectedNode.id);
                              setCliCommand('show ip interface brief');
                              executeCliCommand();
                              // Scroll down to CLI console
                              const cliElement = document.getElementById('cli-console-panel');
                              if (cliElement) cliElement.scrollIntoView({ behavior: 'smooth' });
                            }}
                            className="btn-glass btn-cyan flex-1 py-1.5 text-[10px] font-mono justify-center"
                          >
                            Show Interfaces
                          </button>
                          <button 
                            onClick={() => {
                              setCliDevice(selectedNode.id);
                              setCliCommand('show ip route');
                              executeCliCommand();
                              // Scroll down to CLI console
                              const cliElement = document.getElementById('cli-console-panel');
                              if (cliElement) cliElement.scrollIntoView({ behavior: 'smooth' });
                            }}
                            className="btn-glass btn-cyan flex-1 py-1.5 text-[10px] font-mono justify-center"
                          >
                            View Routes
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Fault Impact Scope Details */}
              {topology.impact_analysis.affected_networks.length > 0 && (
                <div className="mt-4 p-4 rounded-xl bg-rose-950/10 border border-rose-950/20">
                  <h4 className="text-xs font-bold text-rose-400 uppercase tracking-widest mb-2.5 flex items-center gap-1.5 font-mono">
                    <ShieldAlert size={13} className="animate-pulse" /> Outage Topological Impact Scope
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-400 block font-semibold mb-1">Blackholed Route Subnets:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {topology.impact_analysis.affected_networks.map((net, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-slate-950 border border-rose-950/30 text-rose-300 font-mono text-[10px]">{net}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-400 block font-semibold mb-1">Isolated Downstream Hosts:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {topology.impact_analysis.affected_devices.map((dev, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-slate-950 border border-rose-950/30 text-rose-300 font-mono text-[10px]">{dev}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Failure Simulation Lab console */}
            <div className="glass-panel p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-bold text-lg text-slate-200 flex items-center gap-2 mb-1">
                    <Play size={16} className="text-cyan-400" /> NRE Failure Simulation Laboratory
                  </h3>
                  <p className="text-xs text-slate-400">Trigger simulated core hardware/software failure vectors to test parsed rules and AI models</p>
                </div>
                {simulatingId !== null && (
                  <span className="badge badge-cyan animate-pulse">Simulator Active...</span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {/* Reset healthy card */}
                <div 
                  onClick={() => triggerScenario(0)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${simState.current_scenario === 0 ? 'bg-emerald-950/10 border-emerald-500/40 shadow-lg shadow-emerald-950/20' : 'bg-slate-950/20 border-white/5 hover:border-white/10'}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 bg-slate-900 rounded text-slate-400 border border-white/5">RESET STATE</span>
                    <CheckCircle className={simState.current_scenario === 0 ? "text-emerald-400" : "text-slate-600"} size={15} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-200">Reset Baseline Health</h4>
                    <p className="text-[10px] text-slate-400 mt-1">Establishes OSPF neighbor adjacencies, interface routing, and resets metrics.</p>
                  </div>
                </div>

                {/* Scenario 1 */}
                <div 
                  onClick={() => triggerScenario(1)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${simState.current_scenario === 1 ? 'bg-cyan-950/10 border-cyan-500/40 shadow-lg shadow-cyan-950/20' : 'bg-slate-950/20 border-white/5 hover:border-white/10'}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 bg-slate-900 rounded text-slate-400 border border-white/5">SCENARIO 1</span>
                    <AlertTriangle className={simState.current_scenario === 1 ? "text-cyan-400 animate-pulse" : "text-slate-600"} size={15} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-200">OSPF Area Mismatch</h4>
                    <p className="text-[10px] text-slate-400 mt-1">Injects mismatched OSPF Areas (0 vs 10) on connecting link, collapsing adjacency.</p>
                  </div>
                </div>

                {/* Scenario 2 */}
                <div 
                  onClick={() => triggerScenario(2)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${simState.current_scenario === 2 ? 'bg-cyan-950/10 border-cyan-500/40 shadow-lg shadow-cyan-950/20' : 'bg-slate-950/20 border-white/5 hover:border-white/10'}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 bg-slate-900 rounded text-slate-400 border border-white/5">SCENARIO 2</span>
                    <AlertTriangle className={simState.current_scenario === 2 ? "text-cyan-400 animate-pulse" : "text-slate-600"} size={15} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-200">OSPF Cryptographic Key Mismatch</h4>
                    <p className="text-[10px] text-slate-400 mt-1">Configures incorrect MD5 secret signature on interface serial link, blocking OSPF hellos.</p>
                  </div>
                </div>

                {/* Scenario 3 */}
                <div 
                  onClick={() => triggerScenario(3)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${simState.current_scenario === 3 ? 'bg-cyan-950/10 border-cyan-500/40 shadow-lg shadow-cyan-950/20' : 'bg-slate-950/20 border-white/5 hover:border-white/10'}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 bg-slate-900 rounded text-slate-400 border border-white/5">SCENARIO 3</span>
                    <AlertTriangle className={simState.current_scenario === 3 ? "text-cyan-400 animate-pulse" : "text-slate-600"} size={15} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-200">Interface Shutdown</h4>
                    <p className="text-[10px] text-slate-400 mt-1">Issues a Cisco command `shutdown` on R2's Gi0/1 interface, simulating cable failure.</p>
                  </div>
                </div>

                {/* Scenario 4 */}
                <div 
                  onClick={() => triggerScenario(4)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${simState.current_scenario === 4 ? 'bg-cyan-950/10 border-cyan-500/40 shadow-lg shadow-cyan-950/20' : 'bg-slate-950/20 border-white/5 hover:border-white/10'}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 bg-slate-900 rounded text-slate-400 border border-white/5">SCENARIO 4</span>
                    <AlertTriangle className={simState.current_scenario === 4 ? "text-cyan-400 animate-pulse" : "text-slate-600"} size={15} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-200">Missing Return Static Route</h4>
                    <p className="text-[10px] text-slate-400 mt-1">Removes static route on DC Gateway R3 back to Client, creating return path routing loss.</p>
                  </div>
                </div>

                {/* Scenario 5 */}
                <div 
                  onClick={() => triggerScenario(5)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${simState.current_scenario === 5 ? 'bg-cyan-950/10 border-cyan-500/40 shadow-lg shadow-cyan-950/20' : 'bg-slate-950/20 border-white/5 hover:border-white/10'}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 bg-slate-900 rounded text-slate-400 border border-white/5">SCENARIO 5</span>
                    <AlertTriangle className={simState.current_scenario === 5 ? "text-cyan-400 animate-pulse" : "text-slate-600"} size={15} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-200">ACL Client Block Traffic</h4>
                    <p className="text-[10px] text-slate-400 mt-1">Configures ACL denying explicit client subnets, blackholing traffic at DC boundary.</p>
                  </div>
                </div>

                {/* Scenario 6 */}
                <div 
                  onClick={() => triggerScenario(6)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${simState.current_scenario === 6 ? 'bg-cyan-950/10 border-cyan-500/40 shadow-lg shadow-cyan-950/20' : 'bg-slate-950/20 border-white/5 hover:border-white/10'}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 bg-slate-900 rounded text-slate-400 border border-white/5">SCENARIO 6</span>
                    <AlertTriangle className={simState.current_scenario === 6 ? "text-cyan-400 animate-pulse" : "text-slate-600"} size={15} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-slate-200">Control Plane CPU Exhaustion</h4>
                    <p className="text-[10px] text-slate-400 mt-1">Triggers simulated context-switching loop on R1, spiking usage to 98% and dropping packets.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right sidebar: Alerts and Advisor */}
          <div className="col-span-12 lg:col-span-4 flex flex-col gap-5">
            {/* Active Outages Center */}
            <div className="glass-panel p-6 flex flex-col max-h-[350px]">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
                <h3 className="font-bold text-slate-200 flex items-center gap-2">
                  <ShieldAlert size={16} className="text-rose-400 animate-pulse" /> Active Outages &amp; Outlays
                </h3>
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-white/5 font-mono text-[10px] font-bold text-slate-400">
                  {incidents.filter(i => i.status === 'Open').length} Open
                </span>
              </div>

              <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2.5">
                {incidents.filter(i => i.status === 'Open').length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-10 text-slate-500">
                    <CheckCircle size={30} className="text-emerald-400/50 mb-2" />
                    <p className="text-xs italic">Enterprise Network fully operational</p>
                    <p className="text-[9px] text-slate-600 uppercase tracking-widest font-mono font-semibold">No issues flagged</p>
                  </div>
                ) : (
                  incidents.filter(i => i.status === 'Open').map((inc) => (
                    <div 
                      key={inc.id}
                      onClick={() => fetchIncidentDetail(inc.incident_id)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all flex flex-col gap-1.5 ${selectedIncident?.incident_id === inc.incident_id ? 'bg-slate-900/60 border-cyan-500/50 shadow-lg shadow-slate-950/40' : 'bg-slate-950/30 border-white/5 hover:border-white/10'}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-900 border border-white/5 rounded text-cyan-400 font-bold">{inc.incident_id}</span>
                        {getSeverityBadge(inc.severity)}
                      </div>
                      <h4 className="font-bold text-xs text-slate-200 leading-snug">{inc.issue}</h4>
                      <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                        <span>Device: <strong className="text-slate-400 font-semibold">{inc.device_name}</strong></span>
                        <span className="text-cyan-400 font-bold">Conf: {inc.confidence_score.toFixed(0)}%</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* AI Advisor Panel */}
            <div className="glass-panel p-6 flex flex-col min-h-[400px]">
              <div className="flex items-center gap-2 mb-4 border-b border-white/5 pb-3">
                <Award size={18} className="text-cyan-400" />
                <h3 className="font-bold text-slate-200">NetSage AI Technical Advisor</h3>
              </div>

              {!selectedIncident ? (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-10">
                  <Terminal size={32} className="text-slate-700 mb-2" />
                  <p className="text-xs italic">Select an open incident to populate CCIE diagnostic insights</p>
                </div>
              ) : (
                <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-1">
                  <div className="p-3.5 rounded-xl bg-cyan-950/10 border border-cyan-500/20">
                    <span className="text-[9px] uppercase tracking-widest text-cyan-400 font-bold block mb-1 font-mono">Operations Assurance Scope</span>
                    <h4 className="font-bold text-sm text-slate-200 leading-snug">{selectedIncident.issue}</h4>
                    <span className="text-[10px] text-slate-400 block mt-1">Anomaly Type: <strong className="text-slate-300 font-semibold">{selectedIncident.root_cause}</strong></span>
                  </div>

                  {selectedIncident.resolution_details && (
                    <div className="flex flex-col gap-3.5 text-xs text-slate-400">
                      <div>
                        <strong className="text-slate-200 block mb-1 font-semibold">Root Cause Breakdown:</strong>
                        <p className="leading-relaxed">{selectedIncident.resolution_details.root_cause_explanation}</p>
                      </div>
                      <div>
                        <strong className="text-slate-200 block mb-1 font-semibold">Topological Impact:</strong>
                        <p className="leading-relaxed">{selectedIncident.resolution_details.impact_analysis}</p>
                      </div>
                      <div>
                        <strong className="text-slate-200 block mb-1 font-semibold">Recommended CCIE Resolution:</strong>
                        <p className="leading-relaxed">{selectedIncident.resolution_details.recommended_fix}</p>
                      </div>

                      {/* Remediation Steps */}
                      {selectedIncident.resolution_details.remediation_steps?.length > 0 && (
                        <div>
                          <strong className="text-slate-200 block mb-1 font-semibold">Remediation Action CLI Steps:</strong>
                          <div className="bg-slate-950/80 border border-white/5 rounded-lg p-3 font-mono text-[10px] text-rose-300/90 leading-relaxed max-h-[160px] overflow-y-auto">
                            {selectedIncident.resolution_details.remediation_steps.map((step, idx) => (
                              <div key={idx} className="flex gap-2">
                                <span className="text-slate-600 select-none">{idx+1}.</span>
                                <span>{step}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Validation Commands */}
                      {selectedIncident.resolution_details.validation_commands?.length > 0 && (
                        <div>
                          <strong className="text-slate-200 block mb-1 font-semibold">Verification CLI Commands:</strong>
                          <div className="bg-slate-950/80 border border-white/5 rounded-lg p-3 font-mono text-[10px] text-cyan-300/90 leading-relaxed">
                            {selectedIncident.resolution_details.validation_commands.map((cmd, idx) => (
                              <div key={idx} className="flex gap-1.5">
                                <span className="text-slate-600 select-none">&gt;</span>
                                <span>{cmd}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between border-t border-white/5 pt-3.5 text-[10px]">
                        <span>Risk Factor: <strong className="text-amber-400 font-semibold">{selectedIncident.resolution_details.risk_level}</strong></span>
                        <span className="badge badge-emerald">Model Verified</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Interactive Simulated Cisco CLI Terminal Box */}
          <div className="col-span-12" id="cli-console-panel">
            <div className="glass-panel p-6 border-cyan-500/10">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <div>
                  <h3 className="font-bold text-lg text-slate-200 flex items-center gap-2">
                    <Terminal size={17} className="text-cyan-400" /> Interactive Simulated Cisco IOS CLI Terminal
                  </h3>
                  <p className="text-xs text-slate-400">Issue Cisco validation or monitoring commands to nodes in real-time to inspect mock output</p>
                </div>
                
                {/* Selector interface */}
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="flex items-center gap-1.5 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-white/5 text-xs font-mono">
                    <span className="text-slate-500">Device:</span>
                    <select 
                      value={cliDevice}
                      onChange={(e) => setCliDevice(e.target.value)}
                      className="bg-transparent border-none text-cyan-400 font-bold focus:outline-none cursor-pointer"
                    >
                      <option value="R1">R1 (HO Gateway)</option>
                      <option value="R2">R2 (Transit Router)</option>
                      <option value="R3">R3 (DC Gateway)</option>
                      <option value="Client01">Client01 (Host PC)</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-1.5 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-white/5 text-xs font-mono">
                    <span className="text-slate-500">Command:</span>
                    <select 
                      value={cliCommand}
                      onChange={(e) => setCliCommand(e.target.value)}
                      className="bg-transparent border-none text-cyan-400 font-bold focus:outline-none cursor-pointer"
                    >
                      <option value="show ip route">show ip route</option>
                      <option value="show ip ospf neighbor">show ip ospf neighbor</option>
                      <option value="show interface">show interface</option>
                      <option value="show running-config">show running-config</option>
                      <option value="show logging">show logging</option>
                      <option value="show processes cpu">show processes cpu</option>
                      <option value="show access-lists">show access-lists</option>
                      <option value="ping 192.168.4.10">ping 192.168.4.10 (App Server)</option>
                      <option value="show version">show version</option>
                      <option value="show cdp neighbors">show cdp neighbors</option>
                    </select>
                  </div>

                  <button 
                    onClick={executeCliCommand}
                    disabled={cliExecuting}
                    className="btn-glass btn-cyan py-1.5 px-3 text-xs"
                  >
                    <Send size={12} />
                    {cliExecuting ? "Running..." : "Execute Command"}
                  </button>
                </div>
              </div>

              {/* Console window */}
              <div className="bg-[#04060d] border border-cyan-500/10 rounded-xl p-5 shadow-inner relative">
                <div className="absolute top-3 left-3 flex gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full bg-rose-500/60"></div>
                  <div className="h-2.5 w-2.5 rounded-full bg-amber-500/60"></div>
                  <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/60"></div>
                </div>
                <div className="absolute top-2 right-4 text-[9px] font-mono text-cyan-500/30 uppercase tracking-widest font-semibold">Cisco IOSv Terminal Console</div>
                
                <div className="mt-2 h-72 overflow-y-auto font-mono text-xs text-cyan-400/90 leading-relaxed pr-2 whitespace-pre-wrap select-text">
                  {cliOutput}
                  {cliExecuting && (
                    <span className="inline-block h-3.5 w-2 bg-cyan-400 animate-pulse ml-1"></span>
                  )}
                  <div ref={terminalEndRef} />
                </div>
              </div>
            </div>
          </div>

          {/* Routers Health and Metrics */}
          <div className="col-span-12">
            <div className="glass-panel p-6">
              <h3 className="font-bold text-lg text-slate-200 mb-4 flex items-center gap-2">
                <Cpu size={16} className="text-cyan-400" /> Monitored Core Router Diagnostics Matrix
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {devices.filter(d => d.type === 'router').map((device) => {
                  const isCritical = device.status === 'Critical';
                  const isWarning = device.status === 'Warning';
                  return (
                    <div key={device.id} className="p-5 rounded-xl border border-white/5 bg-[#0b0e1b]/35">
                      <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
                        <div>
                          <h4 className="font-bold text-slate-200 text-sm font-mono">{device.name}</h4>
                          <span className="text-[10px] text-slate-500 font-mono">IP: {device.ip}</span>
                        </div>
                        {getStatusBadge(device.status)}
                      </div>

                      <div className="flex flex-col gap-3">
                        {/* CPU usage */}
                        <div>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-slate-400 flex items-center gap-1"><Cpu size={11} /> Control Plane CPU</span>
                            <strong className={device.cpu_usage > 80 ? "text-rose-400 font-mono" : "text-slate-300 font-mono"}>{device.cpu_usage.toFixed(0)}%</strong>
                          </div>
                          <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-white/5">
                            <div 
                              className={`h-full transition-all duration-500 ${device.cpu_usage > 80 ? 'bg-gradient-to-r from-rose-500 to-red-600 animate-pulse' : 'bg-gradient-to-r from-cyan-400 to-blue-500'}`}
                              style={{ width: `${device.cpu_usage}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* Memory usage */}
                        <div>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-slate-400 flex items-center gap-1"><HardDrive size={11} /> Processor Memory</span>
                            <strong className={device.memory_usage > 80 ? "text-rose-400 font-mono" : "text-slate-300 font-mono"}>{device.memory_usage.toFixed(0)}%</strong>
                          </div>
                          <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-white/5">
                            <div 
                              className={`h-full transition-all duration-500 ${device.memory_usage > 80 ? 'bg-gradient-to-r from-rose-500 to-red-600' : 'bg-gradient-to-r from-cyan-400 to-blue-500'}`}
                              style={{ width: `${device.memory_usage}%` }}
                            ></div>
                          </div>
                        </div>

                        <div className="flex justify-between items-center text-[10px] text-slate-500 border-t border-white/5 pt-2 mt-1 font-mono">
                          <span>Interfaces: <strong className="text-slate-300">2 GE (Up)</strong></span>
                          <span>Polled: {new Date(device.last_checked).toLocaleTimeString()}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </main>
      ) : (
        <main className="dashboard-grid flex-1">
          {/* Executive Overview Analytics */}
          <div className="col-span-12 lg:col-span-4 flex flex-col gap-5">
            {/* Resolution metrics */}
            <div className="glass-panel p-6 bg-gradient-to-br from-slate-950/60 to-indigo-950/15">
              <h3 className="font-bold text-slate-200 mb-4 flex items-center gap-2 border-b border-white/5 pb-3">
                <Activity size={15} className="text-cyan-400" /> Executive Health Indicators
              </h3>
              
              <div className="flex flex-col gap-4">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-white/5 flex justify-between items-center">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest block font-mono font-bold">Mean Time to Detect (MTTD)</span>
                    <strong className="text-2xl font-black font-mono text-cyan-400 tracking-tight mt-1 block">
                      {analytics?.mttd || "4.2 mins"}
                    </strong>
                  </div>
                  <div className="h-10 w-10 rounded-lg bg-cyan-950/30 flex items-center justify-center border border-cyan-500/20 shadow-inner">
                    <Activity size={18} className="text-cyan-400" />
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-white/5 flex justify-between items-center">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest block font-mono font-bold">Mean Time to Resolve (MTTR)</span>
                    <strong className="text-2xl font-black font-mono text-emerald-400 tracking-tight mt-1 block">
                      {analytics?.mttr || "14.5 mins"}
                    </strong>
                  </div>
                  <div className="h-10 w-10 rounded-lg bg-emerald-950/30 flex items-center justify-center border border-emerald-500/20 shadow-inner">
                    <CheckCircle size={18} className="text-emerald-400" />
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-white/5">
                  <span className="text-[10px] text-slate-500 uppercase tracking-widest block font-mono font-bold mb-2">Platform Assurance Status</span>
                  <div className="flex gap-2.5 items-start">
                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse mt-1.5 shrink-0"></div>
                    <span className="text-xs text-slate-350 leading-relaxed font-sans">
                      AI systems and deterministic Rule engine synced. Continuous virtual simulation collection active. No metrics Drift.
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Document Report Exporter */}
            <div className="glass-panel p-6">
              <h3 className="font-bold text-slate-200 mb-4 flex items-center gap-2 border-b border-white/5 pb-3">
                <FileText size={15} className="text-cyan-400" /> Compliance Exporters
              </h3>
              <p className="text-xs text-slate-400 mb-4">Export diagnostic logs, device states, and remediation histories in corporate-grade files</p>

              <div className="flex flex-col gap-2.5">
                <a 
                  href="http://localhost:8000/api/reports/generate/pdf" 
                  download 
                  className="btn-glass flex items-center justify-between p-3.5 hover:border-cyan-500/30"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded bg-rose-950/30 border border-rose-900/40 flex items-center justify-center shadow-inner">
                      <FileText size={14} className="text-rose-400" />
                    </div>
                    <div>
                      <strong className="text-xs text-slate-200 block">PDF Operations Report</strong>
                      <span className="text-[9px] text-slate-500 font-mono">Formal diagnostic assessment &amp; fix list</span>
                    </div>
                  </div>
                  <Download size={13} className="text-slate-400" />
                </a>

                <a 
                  href="http://localhost:8000/api/reports/generate/html" 
                  download 
                  className="btn-glass flex items-center justify-between p-3.5 hover:border-cyan-500/30"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded bg-blue-950/30 border border-blue-900/40 flex items-center justify-center shadow-inner">
                      <Terminal size={14} className="text-blue-400" />
                    </div>
                    <div>
                      <strong className="text-xs text-slate-200 block">HTML Standalone Report</strong>
                      <span className="text-[9px] text-slate-500 font-mono">Standalone stylized assessment board file</span>
                    </div>
                  </div>
                  <Download size={13} className="text-slate-400" />
                </a>

                <a 
                  href="http://localhost:8000/api/reports/generate/csv" 
                  download 
                  className="btn-glass flex items-center justify-between p-3.5 hover:border-cyan-500/30"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded bg-emerald-950/30 border border-emerald-900/40 flex items-center justify-center shadow-inner">
                      <Database size={14} className="text-emerald-400" />
                    </div>
                    <div>
                      <strong className="text-xs text-slate-200 block">CSV Logs Spreadsheets</strong>
                      <span className="text-[9px] text-slate-500 font-mono">Raw data grids of all historical metrics</span>
                    </div>
                  </div>
                  <Download size={13} className="text-slate-400" />
                </a>
              </div>
            </div>
          </div>

          {/* Historical Trends Graphs */}
          <div className="col-span-12 lg:col-span-8 flex flex-col gap-5">
            <div className="glass-panel p-6 flex flex-col min-h-[350px]">
              <h3 className="font-bold text-slate-200 mb-4 flex items-center gap-2 border-b border-white/5 pb-3">
                <BarChart2 size={15} className="text-cyan-400" /> Incident Ticket &amp; Outage Volume History
              </h3>
              
              {/* Custom SVG Line Chart */}
              <div className="flex-1 bg-slate-950/40 border border-white/5 rounded-xl p-5 flex items-end justify-between relative min-h-[220px]">
                <div className="absolute top-4 left-4 text-[10px] font-mono text-slate-500">TICKETS VOLUME TRENDS (6-MONTH MATRIX)</div>
                
                <svg className="w-full h-full" viewBox="0 0 600 180">
                  {/* Grid Lines */}
                  <line x1="40" y1="20" x2="560" y2="20" stroke="#101524" strokeWidth="1" />
                  <line x1="40" y1="65" x2="560" y2="65" stroke="#101524" strokeWidth="1" />
                  <line x1="40" y1="110" x2="560" y2="110" stroke="#101524" strokeWidth="1" />
                  <line x1="40" y1="150" x2="560" y2="150" stroke="#1e293b" strokeWidth="1.5" />

                  {/* Trend line coordinates: Jan(2), Feb(5), Mar(4), Apr(8), May(12), Jun(incidents) */}
                  {(() => {
                    const dataPoints = [
                      { x: 70, y: 130, val: 2, label: 'Jan' },
                      { x: 160, y: 100, val: 5, label: 'Feb' },
                      { x: 250, y: 110, val: 4, label: 'Mar' },
                      { x: 340, y: 70, val: 8, label: 'Apr' },
                      { x: 430, y: 40, val: 12, label: 'May' },
                      { x: 520, y: 30, val: Math.max(incidents.length, 12), label: 'Jun' }
                    ];

                    let pathString = `M ${dataPoints[0].x} ${dataPoints[0].y}`;
                    for (let i = 1; i < dataPoints.length; i++) {
                      pathString += ` L ${dataPoints[i].x} ${dataPoints[i].y}`;
                    }

                    return (
                      <g>
                        {/* Area glow */}
                        <path 
                          d={`${pathString} L ${dataPoints[5].x} 150 L ${dataPoints[0].x} 150 Z`} 
                          fill="url(#chart-glow)" 
                        />
                        {/* Line */}
                        <path 
                          d={pathString} 
                          fill="none" 
                          stroke="#06b6d4" 
                          strokeWidth="3.5" 
                          strokeLinecap="round"
                        />
                        
                        {/* Data Points */}
                        {dataPoints.map((pt, i) => (
                          <g key={i}>
                            <circle cx={pt.x} cy={pt.y} r={5} fill="#070b16" stroke="#06b6d4" strokeWidth="3" />
                            <text x={pt.x} y={pt.y - 12} fill="#94a3b8" fontSize={9} textAnchor="middle" fontWeight="bold" className="font-mono">
                              {pt.val}
                            </text>
                            <text x={pt.x} y={170} fill="#475569" fontSize={9} textAnchor="middle" fontWeight="bold" className="font-mono">
                              {pt.label}
                            </text>
                          </g>
                        ))}

                        <defs>
                          <linearGradient id="chart-glow" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.25" />
                            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
                          </linearGradient>
                        </defs>
                      </g>
                    );
                  })()}
                </svg>
              </div>
            </div>

            {/* Unstable Devices Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Most unstable device */}
              <div className="glass-panel p-5">
                <h4 className="text-sm font-bold text-slate-200 mb-3 font-mono flex items-center gap-1.5">
                  <AlertTriangle size={14} className="text-amber-500" /> Top Failing Devices
                </h4>
                <div className="flex flex-col gap-2">
                  {analytics?.most_unstable_devices?.length === 0 ? (
                    <span className="text-xs text-slate-500 italic">No device failures recorded yet.</span>
                  ) : (
                    analytics?.most_unstable_devices?.map((dev, i) => (
                      <div key={i} className="flex justify-between items-center text-xs p-2.5 rounded bg-slate-950/40 border border-white/5">
                        <span className="font-mono font-bold text-slate-350">{dev.device}</span>
                        <span className="badge badge-rose font-mono text-[9px] font-bold">{dev.count} ticket(s)</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Most frequent issues */}
              <div className="glass-panel p-5">
                <h4 className="text-sm font-bold text-slate-200 mb-3 font-mono flex items-center gap-1.5">
                  <Terminal size={14} className="text-cyan-500" /> Most Frequent Outage Causes
                </h4>
                <div className="flex flex-col gap-2">
                  {analytics?.most_frequent_issues?.length === 0 ? (
                    <span className="text-xs text-slate-500 italic">No tickets recorded in model database.</span>
                  ) : (
                    analytics?.most_frequent_issues?.map((issue, i) => (
                      <div key={i} className="flex justify-between items-center text-xs p-2.5 rounded bg-slate-950/40 border border-white/5">
                        <span className="text-slate-350 truncate max-w-[210px] font-sans">{issue.issue}</span>
                        <span className="badge badge-cyan font-mono text-[9px] font-bold">{issue.count} hit(s)</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      )}

      {/* Footer copyright */}
      <footer className="border-t border-white/5 bg-[#04060d] py-6 text-center text-xs text-slate-500 mt-auto">
        <div className="max-w-[1600px] mx-auto px-6 flex flex-wrap items-center justify-between gap-4">
          <p>&copy; {new Date().getFullYear()} NetSage Assurance Platform. Enterprise-Grade Network Assurance Core.</p>
          <div className="flex gap-4 font-mono text-[10px]">
            <span>Status: <strong className="text-emerald-400">NOC-ONLINE</strong></span>
            <span>Firmware: <strong>v1.3.0-stable</strong></span>
          </div>
        </div>
      </footer>
    </div>
  );
}
