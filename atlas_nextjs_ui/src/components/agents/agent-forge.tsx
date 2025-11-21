'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  Bot,
  Cpu,
  Save,
  RefreshCw,
  Shield,
  Terminal,
  Sliders,
  Database,
  Globe,
  Code,
  Zap,
  DollarSign,
} from 'lucide-react';

type AgentProfile = {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  status: string;
  config?: {
    base_model?: string;
    temperature?: number;
    tools?: Record<string, boolean>;
  };
};

type AgentConfig = {
  id: string;
  agentId: string;
  name: string;
  role: string;
  baseModel: string;
  status: string;
  temp: number;
  tools: Record<string, boolean>;
};

export default function AgentForge() {
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiBase = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000',
    []
  );

  useEffect(() => {
    const fetchAgents = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiBase}/api/agents`);
        if (!res.ok) {
          throw new Error(`Failed to load agents (${res.status})`);
        }
        const data: AgentProfile[] = await res.json();
        const mapped = data.map((agent) => {
          const cfg = agent.config || {};
          return {
            id: agent.id,
            agentId: agent.agent_id || agent.id,
            name: agent.agent_name || agent.agent_id || 'Agent',
            role: agent.agent_type || 'Agent',
            baseModel: cfg.base_model || 'GPT-4o',
            status: agent.status,
            temp: cfg.temperature ?? 0.7,
            tools: cfg.tools || {
              web_browsing: true,
              cockroachdb_read: true,
              workflow_trigger: true,
              python: false,
              shell: false,
              crypto_wallet: false,
            },
          } as AgentConfig;
        });
        setAgents(mapped);
        if (mapped.length > 0) {
          setSelectedAgentId(mapped[0].id);
          setConfig(mapped[0]);
        }
      } catch (err: any) {
        setError(err.message || 'Unable to load agents');
      } finally {
        setIsLoading(false);
      }
    };

    void fetchAgents();
  }, [apiBase]);

  useEffect(() => {
    if (!selectedAgentId) return;
    const agent = agents.find((a) => a.id === selectedAgentId);
    if (agent) {
      setConfig(agent);
    }
  }, [selectedAgentId, agents]);

  const handleSave = async () => {
    if (!config) return;
    setIsSaving(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/agents/${config.agentId}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_model: config.baseModel,
          temperature: config.temp,
          tools: config.tools,
        }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `Failed to save config (${res.status})`);
      }
    } catch (err: any) {
      setError(err.message || 'Save failed');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex h-full min-h-[calc(100vh-80px)] bg-[#020617] text-slate-200">
      {/* Agent roster */}
      <div className="w-72 border-r border-white/5 bg-[#0B1121]/50 backdrop-blur-xl flex flex-col">
        <div className="p-6 border-b border-white/5">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Bot className="w-5 h-5 text-emerald-500" /> Agent Forge
          </h2>
          <p className="text-xs text-slate-500 mt-1">Neural Configuration</p>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading && <div className="text-xs text-slate-500">Loading agents...</div>}
          {error && <div className="text-xs text-red-400">{error}</div>}
          {!isLoading &&
            !error &&
            agents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => setSelectedAgentId(agent.id)}
                className={`w-full text-left p-3 rounded-xl border transition-all ${
                  selectedAgentId === agent.id
                    ? 'bg-emerald-900/20 border-emerald-500/50 text-white shadow-[0_0_15px_rgba(16,185,129,0.1)]'
                    : 'bg-white/5 border-transparent text-slate-400 hover:bg-white/10'
                }`}
              >
                <div className="font-bold text-sm mb-1">{agent.name}</div>
                <div className="flex justify-between items-center text-[10px] uppercase tracking-wider">
                  <span>{agent.role}</span>
                  <span className={agent.status === 'active' ? 'text-emerald-400' : 'text-slate-500'}>
                    ● {agent.status}
                  </span>
                </div>
              </button>
            ))}
        </div>
        <div className="p-4 border-t border-white/5">
          <button className="w-full py-2 border border-dashed border-slate-700 text-slate-500 rounded-lg text-xs hover:text-white hover:border-slate-500 transition-colors">
            + Provision New Agent
          </button>
        </div>
      </div>

      {/* Configuration panel */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-[#0B1121]/30">
          {config && (
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center shadow-lg">
                <Cpu className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">{config.name}</h1>
                <div className="text-xs font-mono text-emerald-400 flex items-center gap-2">
                  ID: {config.agentId} <span className="text-slate-600">|</span> RUNTIME: {config.status.toUpperCase()}
                </div>
              </div>
            </div>
          )}
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={isSaving || !config}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold text-sm shadow-lg flex items-center gap-2 transition-all disabled:opacity-70"
            >
              {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {isSaving ? 'UPLOADING...' : 'DEPLOY CONFIG'}
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-4xl mx-auto space-y-8">
            {/* Model parameters */}
            <section>
              <h3 className="text-xs font-bold text-slate-500 uppercase mb-4 flex items-center gap-2">
                <Sliders className="w-4 h-4" /> Synaptic Parameters
              </h3>
              {config && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-[#0B1121] border border-white/10 p-5 rounded-xl">
                    <label className="block text-sm text-slate-300 mb-3">Base Model</label>
                    <select
                      value={config.baseModel}
                      onChange={(e) => setConfig({ ...config, baseModel: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white focus:border-emerald-500 outline-none"
                    >
                      <option value="GPT-4o">GPT-4o (OpenAI)</option>
                      <option value="Claude-3.5-Sonnet">Claude 3.5 Sonnet (Anthropic)</option>
                      <option value="Llama-3-70B">Llama 3 70B (Local)</option>
                    </select>
                  </div>
                  <div className="bg-[#0B1121] border border-white/10 p-5 rounded-xl">
                    <div className="flex justify-between mb-3">
                      <label className="block text-sm text-slate-300">Temperature (Creativity)</label>
                      <span className="text-xs font-mono text-emerald-400">{config.temp.toFixed(1)}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={config.temp}
                      onChange={(e) => setConfig({ ...config, temp: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                    <div className="flex justify-between mt-2 text-[10px] text-slate-500 uppercase">
                      <span>Precise</span>
                      <span>Balanced</span>
                      <span>Creative</span>
                    </div>
                  </div>
                </div>
              )}
            </section>

            {/* Tool authorization */}
            <section>
              <h3 className="text-xs font-bold text-slate-500 uppercase mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4" /> Tool Authorization Protocol
              </h3>
              {config && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <ToolCard
                    icon={<Globe />}
                    label="Web Browsing"
                    active={!!config.tools.web_browsing}
                    onToggle={() =>
                      setConfig({ ...config, tools: { ...config.tools, web_browsing: !config.tools.web_browsing } })
                    }
                  />
                  <ToolCard
                    icon={<Database />}
                    label="CockroachDB Read"
                    active={!!config.tools.cockroachdb_read}
                    onToggle={() =>
                      setConfig({
                        ...config,
                        tools: { ...config.tools, cockroachdb_read: !config.tools.cockroachdb_read },
                      })
                    }
                  />
                  <ToolCard
                    icon={<Zap />}
                    label="Workflow Trigger"
                    active={!!config.tools.workflow_trigger}
                    onToggle={() =>
                      setConfig({
                        ...config,
                        tools: { ...config.tools, workflow_trigger: !config.tools.workflow_trigger },
                      })
                    }
                  />
                  <ToolCard
                    icon={<Code />}
                    label="Python Interpreter"
                    active={!!config.tools.python}
                    onToggle={() =>
                      setConfig({ ...config, tools: { ...config.tools, python: !config.tools.python } })
                    }
                  />
                  <ToolCard
                    icon={<Terminal />}
                    label="Shell Access"
                    active={!!config.tools.shell}
                    danger
                    onToggle={() =>
                      setConfig({ ...config, tools: { ...config.tools, shell: !config.tools.shell } })
                    }
                  />
                  <ToolCard
                    icon={<DollarSign />}
                    label="Crypto Wallet"
                    active={!!config.tools.crypto_wallet}
                    danger
                    onToggle={() =>
                      setConfig({
                        ...config,
                        tools: { ...config.tools, crypto_wallet: !config.tools.crypto_wallet },
                      })
                    }
                  />
                </div>
              )}
            </section>

            {/* System prompt */}
            <section className="h-full">
              <h3 className="text-xs font-bold text-slate-500 uppercase mb-4 flex items-center gap-2">
                <Terminal className="w-4 h-4" /> Neuro-Symbolic Directive (System Prompt)
              </h3>
              <div className="relative">
                <div className="absolute top-0 left-0 w-full h-8 bg-slate-900 rounded-t-xl border border-slate-800 flex items-center px-3 gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50" />
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50" />
                </div>
                <textarea
                  className="w-full h-64 bg-[#050911] border border-white/10 rounded-xl pt-10 p-4 font-mono text-xs text-slate-300 leading-relaxed focus:border-emerald-500/50 outline-none resize-none"
                  value={
                    config
                      ? `YOU ARE AGENT ${config.agentId}.
YOUR PRIME DIRECTIVE IS TO OPTIMIZE WORKFLOW EFFICIENCY.

RULES:
1. NEVER HALLUCINATE DATA.
2. ALWAYS QUERY THE 'DataBrain' FOR CONTEXT BEFORE ACTING.
3. REPORT ALL ANOMALIES TO THE MASTER DASHBOARD.

CONTEXT:
- Connected to CockroachDB (US-EAST-1)
- Authorized for read-only access on Financial Tables.`
                      : ''
                  }
                  readOnly
                />
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

function ToolCard({
  icon,
  label,
  active,
  danger,
  onToggle,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  danger?: boolean;
  onToggle?: () => void;
}) {
  return (
    <div
      className={`p-4 rounded-xl border flex items-center gap-3 cursor-pointer transition-all ${
        active
          ? danger
            ? 'bg-red-900/10 border-red-500/40 text-red-100'
            : 'bg-blue-900/10 border-blue-500/30 text-blue-200'
          : 'bg-[#0B1121] border-white/5 text-slate-500 hover:border-white/10'
      }`}
      onClick={onToggle}
    >
      <div className={`${active ? (danger ? 'text-red-400' : 'text-blue-400') : 'text-slate-600'}`}>{icon}</div>
      <div className="flex-1 font-medium text-xs">{label}</div>
      <div
        className={`w-8 h-4 rounded-full relative ${active ? (danger ? 'bg-red-900/50' : 'bg-blue-600') : 'bg-slate-700'}`}
      >
        <div
          className="absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all"
          style={{ left: active ? '18px' : '2px' }}
        />
      </div>
    </div>
  );
}
