'use client';

import '@phosphor-icons/web';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

type Telemetry = {
  uptime?: number;
  active_agents?: number;
  tasks_processed?: number;
  status?: string;
  timestamp?: string;
};

type AgentProfile = {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  status: string;
  config?: Record<string, unknown>;
};

type ModuleId = 'overview' | 'brain' | 'forge' | 'workflow' | 'finance' | 'talent' | 'data';

const modules: Array<{ id: ModuleId; icon: string; label: string; section?: string }> = [
  { id: 'overview', icon: 'squares-four', label: 'Command Center' },
  { section: 'NEURAL CORE', id: 'brain', icon: 'brain', label: 'Cortex Visualizer' },
  { id: 'forge', icon: 'robot', label: 'Agent Forge' },
  { id: 'workflow', icon: 'lightning', label: 'Workflow Matrix' },
  { section: 'INTELLIGENCE', id: 'finance', icon: 'chart-line-up', label: 'Financial Engine' },
  { id: 'talent', icon: 'users', label: 'Talent Constellation' },
  { section: 'SYSTEM', id: 'data', icon: 'database', label: 'CockroachDB Sync' },
];

const gradientBackground = {
  backgroundImage:
    'radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 40%), radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 40%)',
};

export default function SingularityConsole() {
  const [activeModule, setActiveModule] = useState<ModuleId>('overview');
  const [mode, setMode] = useState<'live' | 'sim'>('live');
  const [telemetry, setTelemetry] = useState<Telemetry>({ uptime: 99.999, active_agents: 24, tasks_processed: 2847 });
  const [agents, setAgents] = useState<AgentProfile[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [socketStatus, setSocketStatus] = useState<'connected' | 'disconnected'>('disconnected');
  const socketRef = useRef<WebSocket | null>(null);
  const brainCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const workflowCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const financeCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const talentCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const apiBase = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000',
    []
  );
  const wsUrl = useMemo(
    () => process.env.NEXT_PUBLIC_WS_TELEMETRY || 'ws://localhost:8000/ws/telemetry',
    []
  );

  // Live telemetry via WebSocket (respects mode switch)
  useEffect(() => {
    if (mode !== 'live') {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setSocketStatus('disconnected');
      return;
    }
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;
    ws.onopen = () => setSocketStatus('connected');
    ws.onclose = () => setSocketStatus('disconnected');
    ws.onerror = () => setSocketStatus('disconnected');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setTelemetry({
          uptime: data.uptime ?? data.uptime_pct ?? telemetry.uptime,
          active_agents: data.active_agents ?? telemetry.active_agents,
          tasks_processed: data.tasks_processed ?? telemetry.tasks_processed,
          status: data.status ?? telemetry.status,
          timestamp: data.timestamp,
        });
      } catch {
        /* ignore malformed data */
      }
    };
    return () => {
      ws.close();
    };
  }, [mode, wsUrl]);

  // Agents fetch
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const res = await fetch(`${apiBase}/api/agents`);
        if (!res.ok) throw new Error(`Agent fetch failed ${res.status}`);
        const data: AgentProfile[] = await res.json();
        setAgents(data);
        if (data.length > 0) setSelectedAgent(data[0].id);
      } catch {
        setAgents([]);
      }
    };
    void loadAgents();
  }, [apiBase]);

  // Brain canvas animation
  useEffect(() => {
    const canvas = brainCanvasRef.current;
    if (!canvas || activeModule !== 'brain') return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const nodes = Array.from({ length: 50 }, (_, i) => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 1.5,
      vy: (Math.random() - 0.5) * 1.5,
      r: Math.random() * 4 + 2,
      color: i % 5 === 0 ? '#ef4444' : i % 3 === 0 ? '#3b82f6' : '#10b981',
    }));
    let raf: number;
    const animate = () => {
      if (activeModule !== 'brain') return;
      ctx.fillStyle = '#020617';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 1;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.strokeStyle = `rgba(255,255,255,${0.1 - dist / 1200})`;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }
      nodes.forEach((n) => {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
        if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.shadowBlur = 10;
        ctx.shadowColor = n.color;
        ctx.fill();
        ctx.shadowBlur = 0;
      });
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [activeModule]);

  // Workflow canvas animation
  useEffect(() => {
    const canvas = workflowCanvasRef.current;
    if (!canvas || activeModule !== 'workflow') return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const stations = [
      { x: 100, y: 300, l: 'Input' },
      { x: 400, y: 300, l: 'Process' },
      { x: 700, y: 200, l: 'Human' },
      { x: 700, y: 400, l: 'AI Agent' },
      { x: 1000, y: 300, l: 'Output' },
    ];
    const particles: Array<{ x: number; y: number; t: number; p: number; c: string }> = [];
    let raf: number;
    const animate = () => {
      if (activeModule !== 'workflow') return;
      ctx.fillStyle = '#020617';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      if (Math.random() > 0.92) particles.push({ x: 100, y: 300, t: 1, p: 0, c: Math.random() > 0.5 ? '#3b82f6' : '#10b981' });
      stations.forEach((s) => {
        ctx.fillStyle = '#1e293b';
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(s.x, s.y, 20, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px Inter';
        ctx.fillText(s.l, s.x - 20, s.y + 40);
      });
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        const s = stations[p.t - 1];
        const e = stations[p.t];
        if (!e) {
          particles.splice(i, 1);
          continue;
        }
        p.p += 0.015;
        p.x = s.x + (e.x - s.x) * p.p;
        p.y = s.y + (e.y - s.y) * p.p;
        ctx.fillStyle = p.c;
        ctx.shadowBlur = 8;
        ctx.shadowColor = p.c;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
        if (p.p >= 1) {
          p.t++;
          p.p = 0;
          if (p.t === 2) p.t = Math.random() > 0.5 ? 2 : 3;
          else if (p.t === 3 || p.t === 4) p.t = 4;
        }
      }
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [activeModule]);

  // Finance canvas animation (flow line)
  useEffect(() => {
    const canvas = financeCanvasRef.current;
    if (!canvas || activeModule !== 'finance') return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let f = 0;
    let raf: number;
    const animate = () => {
      if (activeModule !== 'finance') return;
      f++;
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 20;
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
      for (let i = 0; i < 15; i++) {
        const x = ((f * 3 + i * 50) % canvas.width);
        ctx.fillStyle = '#10b981';
        ctx.beginPath();
        ctx.arc(x, canvas.height / 2, 6, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [activeModule]);

  // Talent canvas animation
  useEffect(() => {
    const canvas = talentCanvasRef.current;
    if (!canvas || activeModule !== 'talent') return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const nodes = Array.from({ length: 20 }, (_, i) => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 10 + 5,
      label: `Emp ${i + 1}`,
    }));
    let raf: number;
    const animate = () => {
      if (activeModule !== 'talent') return;
      ctx.fillStyle = '#020617';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      nodes.forEach((n, i) => {
        n.y += Math.sin(Date.now() * 0.002 + i) * 0.3;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(168, 85, 247, 0.4)';
        ctx.strokeStyle = '#fff';
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.font = '10px Inter';
        ctx.fillText(n.label, n.x - 10, n.y + n.r + 10);
      });
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [activeModule]);

  const throughputData = [
    { name: 't1', value: 45 },
    { name: 't2', value: 52 },
    { name: 't3', value: 48 },
    { name: 't4', value: 60 },
    { name: 't5', value: 55 },
    { name: 't6', value: 70 },
  ];

  const mcData = [
    { label: 'Jan', optimistic: 10, expected: 10, pessimistic: 10 },
    { label: 'Feb', optimistic: 15, expected: 12, pessimistic: 11 },
    { label: 'Mar', optimistic: 25, expected: 18, pessimistic: 13 },
    { label: 'Apr', optimistic: 35, expected: 22, pessimistic: 15 },
  ];

  const selected = agents.find((a) => a.id === selectedAgent);

  return (
    <div className="flex h-screen w-screen font-sans text-slate-300 selection:bg-emerald-500/30" style={gradientBackground}>
      {/* Sidebar */}
      <aside className="w-72 glass-panel border-r border-white/5 flex flex-col z-30">
        <div className="h-20 flex items-center px-6 border-b border-white/5">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20 mr-3">
            <i className="ph ph-cpu text-2xl text-white" />
          </div>
          <div>
            <h1 className="font-bold text-xl tracking-tight text-white">
              CESAR<span className="text-emerald-400">.AI</span>
            </h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <p className="text-[9px] text-emerald-400 tracking-widest uppercase font-bold">
                {socketStatus === 'connected' ? 'ONLINE' : 'OFFLINE'}
              </p>
            </div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-1">
          {modules.map((m, idx) =>
            m.section ? (
              <div
                key={`${m.section}-${idx}`}
                className="px-4 pt-6 pb-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest"
              >
                {m.section}
              </div>
            ) : (
              <button
                key={m.id}
                onClick={() => setActiveModule(m.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group relative overflow-hidden mx-2 ${
                  activeModule === m.id
                    ? 'text-white bg-white/5 border-l-2 border-emerald-500'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <i
                  className={`ph ph-${m.icon} text-lg relative z-10 ${
                    activeModule === m.id ? 'text-emerald-400' : 'text-slate-500 group-hover:text-emerald-300'
                  }`}
                />
                <span className="text-sm font-medium relative z-10">{m.label}</span>
                {activeModule === m.id && <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-transparent" />}
              </button>
            )
          )}
        </nav>
        <div className="p-4 border-t border-white/5">
          <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center font-bold text-xs text-white border border-white/10">
              AD
            </div>
            <div>
              <div className="text-xs font-bold text-white">Administrator</div>
              <div className="text-[10px] text-slate-500">US-EAST-1</div>
            </div>
            <i className="ph ph-gear ml-auto text-slate-500 hover:text-white cursor-pointer" />
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col relative z-10">
        <header className="h-20 border-b border-white/5 flex items-center justify-between px-8 glass-panel bg-opacity-40">
          <div className="flex items-center gap-4 w-1/3">
            <div className="relative w-full group">
              <i className="ph ph-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-400 transition-colors" />
              <input
                type="text"
                placeholder="Search nodes, workflows, or agents..."
                className="w-full bg-[#0B1121] border border-white/10 rounded-lg py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-all"
              />
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 bg-[#0B1121] border border-white/10 rounded-lg p-1">
              <button
                onClick={() => setMode('live')}
                className={`px-3 py-1 text-[10px] font-bold rounded ${
                  mode === 'live'
                    ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-500 hover:text-white'
                }`}
              >
                LIVE DATA
              </button>
              <button
                onClick={() => setMode('sim')}
                className={`px-3 py-1 text-[10px] font-bold rounded ${
                  mode === 'sim'
                    ? 'bg-blue-900/30 text-blue-400 border border-blue-500/30'
                    : 'text-slate-500 hover:text-white'
                }`}
              >
                SIMULATION
              </button>
            </div>
            <button className="relative text-slate-400 hover:text-white transition-colors">
              <i className="ph ph-bell text-xl" />
              <span className="absolute top-0 right-0 w-2 h-2 bg-rose-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.8)]" />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-hidden relative p-6">
          <div className="w-full h-full relative rounded-2xl overflow-hidden glass-panel flex flex-col">
            {activeModule === 'overview' && (
              <div className="p-10 overflow-y-auto">
                <div className="mb-8 flex justify-between items-end">
                  <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Mission Control</h1>
                    <p className="text-slate-400 text-sm mt-1">System Telemetry &amp; Vitals</p>
                  </div>
                  <div className="flex gap-3">
                    <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-bold text-white transition-all">
                      EXPORT LOGS
                    </button>
                    <button className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold shadow-lg flex items-center gap-2">
                      <i className="ph ph-activity" /> DIAGNOSTICS
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8" id="kpi-grid">
                  {renderStatCard('System Uptime', `${(telemetry.uptime ?? 0).toFixed(3)}%`, 'High Availability', 'emerald', 'server')}
                  {renderStatCard('Active Agents', `${telemetry.active_agents ?? 0}`, 'Neural Grid Online', 'blue', 'cpu')}
                  {renderStatCard('Tasks Today', `${telemetry.tasks_processed ?? 0}`, 'Last 24 Hours', 'purple', 'lightning')}
                  {renderStatCard('Status', telemetry.status ?? 'operational', 'Telemetry link', 'amber', 'check-circle')}
                </div>
                <div className="grid grid-cols-3 gap-6 h-96">
                  <div className="col-span-2 glass-panel rounded-2xl p-6 border border-white/5 relative overflow-hidden">
                    <div className="flex justify-between items-center mb-6">
                      <h3 className="font-bold text-white flex items-center gap-2">
                        <i className="ph ph-trend-up text-emerald-400" /> Throughput
                      </h3>
                    </div>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={throughputData}>
                        <YAxis stroke="#94a3b8" width={40} tick={{ fill: '#94a3b8' }} />
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#10b981"
                          strokeWidth={3}
                          dot={false}
                          activeDot={{ r: 4, fill: '#10b981' }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="glass-panel rounded-2xl p-6 border border-white/5 relative overflow-hidden flex flex-col">
                    <h3 className="font-bold text-white flex items-center gap-2 mb-4">
                      <i className="ph ph-shield-check text-blue-400" /> System Health
                    </h3>
                    <div className="flex-1 flex items-center justify-center relative">
                      <div className="text-center z-10">
                        <div className="text-5xl font-black text-white">98</div>
                        <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Score</div>
                      </div>
                      <svg className="absolute w-48 h-48 transform -rotate-90">
                        <circle cx="96" cy="96" r="88" stroke="#1e293b" strokeWidth="12" fill="transparent" />
                        <circle
                          cx="96"
                          cy="96"
                          r="88"
                          stroke="#10b981"
                          strokeWidth="12"
                          fill="transparent"
                          strokeDasharray="552"
                          strokeDashoffset="20"
                          strokeLinecap="round"
                        />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeModule === 'forge' && (
              <div className="flex h-full">
                <div className="w-72 border-r border-white/5 bg-[#0B1121]/50 flex flex-col">
                  <div className="p-6 border-b border-white/5">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                      <i className="ph ph-robot text-emerald-400" /> Agent Forge
                    </h2>
                  </div>
                  <div className="flex-1 p-4 space-y-2 overflow-y-auto">
                    {agents.map((agent) => (
                      <button
                        key={agent.id}
                        onClick={() => setSelectedAgent(agent.id)}
                        className={`w-full text-left p-3 rounded-xl border transition-all ${
                          selectedAgent === agent.id
                            ? 'bg-emerald-900/20 border-emerald-500/50 text-white'
                            : 'bg-white/5 border-transparent text-slate-400'
                        }`}
                      >
                        <div className="font-bold text-sm mb-1">{agent.agent_name || agent.agent_id}</div>
                        <div className="flex justify-between text-[10px] uppercase">
                          <span>{agent.agent_type || 'Agent'}</span>{' '}
                          <span className={agent.status === 'active' ? 'text-emerald-400' : 'text-slate-500'}>●</span>
                        </div>
                      </button>
                    ))}
                    {agents.length === 0 && (
                      <div className="text-xs text-slate-500">No agents found. Verify backend connectivity.</div>
                    )}
                  </div>
                </div>
                <div className="flex-1 p-8 overflow-y-auto">
                  {selected ? (
                    <div className="max-w-3xl mx-auto space-y-8">
                      <div className="flex justify-between items-center border-b border-white/10 pb-6">
                        <div>
                          <h1 className="text-2xl font-bold text-white">{selected.agent_name || selected.agent_id}</h1>
                          <div className="text-xs font-mono text-emerald-400 mt-1">
                            ID: {selected.agent_id} • MODEL: {(selected.config as any)?.base_model || 'GPT-4o'}
                          </div>
                        </div>
                        <button className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-bold shadow-lg">
                          DEPLOY CONFIG
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-6">
                        <div className="bg-[#0B1121] border border-white/10 p-5 rounded-xl">
                          <label className="block text-xs font-bold text-slate-400 uppercase mb-3">Base Model</label>
                          <select className="w-full bg-slate-900 border border-white/10 rounded-lg p-3 text-sm text-white outline-none">
                            <option>GPT-4o (OpenAI)</option>
                            <option>Claude 3.5 Sonnet</option>
                            <option>Llama 3 70B (Local)</option>
                          </select>
                        </div>
                        <div className="bg-[#0B1121] border border-white/10 p-5 rounded-xl">
                          <label className="block text-xs font-bold text-slate-400 uppercase mb-3">Temperature (Creativity)</label>
                          <input
                            type="range"
                            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                            min="0"
                            max="1"
                            step="0.1"
                            defaultValue={(selected.config as any)?.temperature ?? 0.7}
                          />
                          <div className="flex justify-between mt-2 text-[10px] text-slate-500">
                            <span>Precise</span>
                            <span>Creative</span>
                          </div>
                        </div>
                      </div>
                      <div className="relative">
                        <div className="absolute top-0 left-0 w-full h-8 bg-slate-900 rounded-t-xl border border-white/10 flex items-center px-3 gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50" />
                          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                          <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50" />
                        </div>
                        <textarea
                          className="w-full h-64 bg-[#050911] border border-white/10 rounded-xl pt-10 p-4 font-mono text-xs text-slate-300 leading-relaxed focus:border-emerald-500/50 outline-none resize-none"
                          readOnly
                          value={`YOU ARE AGENT ${selected.agent_id}.
YOUR PRIME DIRECTIVE IS TO OPTIMIZE WORKFLOW EFFICIENCY.

RULES:
1. NEVER HALLUCINATE DATA.
2. ALWAYS QUERY THE 'DataBrain' FOR CONTEXT BEFORE ACTING.
3. REPORT ALL ANOMALIES TO THE MASTER DASHBOARD.

CONTEXT:
- Connected to CockroachDB (US-EAST-1)
- Authorized for read-only access on Financial Tables.`}
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-slate-400">Select an agent to configure.</div>
                  )}
                </div>
              </div>
            )}

            {activeModule === 'brain' && (
              <div className="relative w-full h-full">
                <canvas ref={brainCanvasRef} className="w-full h-full" width={1400} height={800} />
                <div className="absolute top-6 left-6 pointer-events-none">
                  <h2 className="text-2xl font-bold text-white">Cortex Visualization</h2>
                  <p className="text-sm text-slate-400">Real-time Z-Index Stratification</p>
                  <div className="mt-4 flex gap-4 text-[10px] uppercase font-bold text-slate-500">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      Knowledge
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                      Data
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-red-500" />
                      Wisdom
                    </span>
                  </div>
                </div>
              </div>
            )}

            {activeModule === 'workflow' && <canvas ref={workflowCanvasRef} className="w-full h-full" width={1200} height={700} />}

            {activeModule === 'finance' && (
              <div className="grid grid-cols-2 h-full">
                <div className="relative border-r border-white/5 p-6 flex flex-col">
                  <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                    <i className="ph ph-wave-sine text-emerald-400" /> Fluid Liquidity Model
                  </h3>
                  <canvas ref={financeCanvasRef} className="flex-1 w-full rounded-xl bg-slate-900/50" width={800} height={400} />
                  <div className="absolute top-20 left-10 text-3xl font-black text-white">$1,240,000</div>
                </div>
                <div className="p-8 flex flex-col gap-6 overflow-y-auto">
                  <div className="h-64 glass-panel rounded-xl p-4 relative">
                    <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">Monte Carlo Forecast</h4>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={mcData}>
                        <YAxis stroke="#94a3b8" width={40} tick={{ fill: '#94a3b8' }} />
                        <Line type="monotone" dataKey="optimistic" stroke="#10b981" strokeDasharray="5 5" dot={false} />
                        <Line type="monotone" dataKey="expected" stroke="#3b82f6" strokeWidth={3} dot={false} />
                        <Line type="monotone" dataKey="pessimistic" stroke="#f43f5e" strokeDasharray="5 5" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-emerald-900/20 border border-emerald-500/20 rounded-xl">
                      <div className="text-xs text-emerald-400 font-bold uppercase">Runway</div>
                      <div className="text-2xl font-bold text-white">18 Mo</div>
                    </div>
                    <div className="p-4 bg-rose-900/20 border border-rose-500/20 rounded-xl">
                      <div className="text-xs text-rose-400 font-bold uppercase">Burn Rate</div>
                      <div className="text-2xl font-bold text-white">$42k</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeModule === 'talent' && <canvas ref={talentCanvasRef} className="w-full h-full" width={1200} height={700} />}

            {activeModule === 'data' && (
              <div className="p-10 text-center text-slate-300">
                <div className="max-w-xl mx-auto glass-panel rounded-2xl p-8 border border-white/10">
                  <h3 className="text-lg font-bold text-white mb-2">CockroachDB Sync</h3>
                  <p className="text-sm text-slate-400">
                    Monitor schema health, replication lag, and last successful sync. Verify changefeeds and vector indices remain
                    warm.
                  </p>
                  <div className="grid grid-cols-3 gap-4 mt-6 text-sm">
                    <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                      <div className="text-xs uppercase text-slate-500 font-bold">Tables</div>
                      <div className="text-xl text-white font-bold">42</div>
                    </div>
                    <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                      <div className="text-xs uppercase text-slate-500 font-bold">Lag</div>
                      <div className="text-xl text-white font-bold">180 ms</div>
                    </div>
                    <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                      <div className="text-xs uppercase text-slate-500 font-bold">Vectors</div>
                      <div className="text-xl text-white font-bold">1536-d</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function renderStatCard(label: string, value: string, sub: string, color: 'emerald' | 'blue' | 'purple' | 'amber', icon: string) {
  const colors: Record<typeof color, string> = {
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  };
  const blurAccent: Record<typeof color, string> = {
    emerald: 'bg-emerald-500/5 group-hover:bg-emerald-500/10',
    blue: 'bg-blue-500/5 group-hover:bg-blue-500/10',
    purple: 'bg-purple-500/5 group-hover:bg-purple-500/10',
    amber: 'bg-amber-500/5 group-hover:bg-amber-500/10',
  };
  return (
    <div className="glass-panel p-6 rounded-2xl border border-white/5 relative overflow-hidden group hover:border-white/10 transition-all">
      <div className={`absolute top-0 right-0 p-20 rounded-full blur-[40px] transition-all ${blurAccent[color]}`} />
      <div className="relative z-10">
        <div className="flex justify-between items-start mb-4">
          <div className={`p-2.5 rounded-xl border ${colors[color]}`}>
            <i className={`ph ph-${icon} text-lg`} />
          </div>
        </div>
        <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">{label}</div>
        <div className="text-3xl font-black text-white mb-1 tracking-tight">{value}</div>
        <div className="text-xs text-slate-500 font-medium">{sub}</div>
      </div>
    </div>
  );
}
