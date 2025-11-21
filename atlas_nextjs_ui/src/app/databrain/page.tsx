'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Database, Activity, Zap, Brain, Network, TrendingUp,
  CheckCircle, AlertTriangle, Clock, Server, Cpu, Globe
} from 'lucide-react';

interface SyncStatus {
  status: string;
  connected: boolean;
  timestamp: string;
  tables: Record<string, {
    count: number;
    synced: boolean;
    error?: string;
  }>;
  recent_activity: {
    a2a_messages_hourly: number;
    llm_collaborations_hourly: number;
    brain_mutations_hourly: number;
  };
  health: {
    total_agents: number;
    knowledge_nodes: number;
    active_workflows: number;
  };
}

interface BrainStats {
  layers: Record<string, number>;
  top_nodes: Array<{
    id: string;
    label: string;
    mass: number;
    z_index: number;
  }>;
  recent_mutations: Record<string, number>;
  timestamp: string;
}

interface TrainingStatus {
  latest_lora_prep: {
    total_samples: number;
    quality_metrics: {
      high_quality_samples: number;
      knowledge_samples: number;
    };
  } | null;
  training_samples_24h: number;
  next_scheduled_training: string;
  training_active: boolean;
  timestamp: string;
}

export default function DataBrainDashboard() {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [brainStats, setBrainStats] = useState<BrainStats | null>(null);
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [syncRes, brainRes, trainingRes] = await Promise.all([
          fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011'}/sync/status`),
          fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011'}/sync/brain/stats`),
          fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011'}/sync/training/status`)
        ]);

        if (syncRes.ok) setSyncStatus(await syncRes.json());
        if (brainRes.ok) setBrainStats(await brainRes.json());
        if (trainingRes.ok) setTrainingStatus(await trainingRes.json());
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
        <div className="text-center">
          <Cpu className="w-16 h-16 mx-auto mb-4 text-emerald-500 animate-pulse" />
          <p className="text-slate-400">Loading DataBrain telemetry...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
              <Brain className="w-10 h-10 text-emerald-500" />
              DataBrain Intelligence Console
            </h1>
            <p className="text-slate-400">Real-time knowledge graph & synchronization telemetry</p>
          </div>

          {syncStatus && (
            <div className="flex items-center gap-3 px-4 py-2 bg-emerald-900/20 rounded-full border border-emerald-500/20">
              <Globe className="w-4 h-4 text-emerald-400" />
              <span className="text-sm font-mono text-emerald-200">
                {syncStatus.connected ? 'COCKROACHDB LIVE' : 'DISCONNECTED'}
              </span>
              {syncStatus.connected && (
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              )}
            </div>
          )}
        </div>
      </div>

      {/* Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={<Server className="w-5 h-5" />}
          label="Active Agents"
          value={syncStatus?.health.total_agents || 0}
          sublabel="Neural Grid Online"
          color="blue"
        />
        <StatCard
          icon={<Network className="w-5 h-5" />}
          label="Knowledge Nodes"
          value={syncStatus?.health.knowledge_nodes || 0}
          sublabel="3D Semantic Graph"
          color="emerald"
        />
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          label="Workflows Active"
          value={syncStatus?.health.active_workflows || 0}
          sublabel="Automation Matrix"
          color="amber"
        />
        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="Brain Mutations/Hr"
          value={syncStatus?.recent_activity.brain_mutations_hourly || 0}
          sublabel="Neuroplasticity Events"
          color="purple"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Database Sync Status */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-xl lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <Database className="w-5 h-5 text-blue-400" />
              CockroachDB Synchronization
            </CardTitle>
            <CardDescription>
              Multi-region distributed SQL database persistence layer
            </CardDescription>
          </CardHeader>
          <CardContent>
            {syncStatus && (
              <div className="space-y-4">
                {Object.entries(syncStatus.tables).map(([table, data]) => (
                  <div key={table} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-700/30">
                    <div className="flex items-center gap-3">
                      {data.synced ? (
                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                      )}
                      <div>
                        <div className="font-mono text-sm text-white">{table}</div>
                        {data.error && (
                          <div className="text-xs text-red-400 mt-1">{data.error}</div>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-white">{data.count.toLocaleString()}</div>
                      <div className="text-xs text-slate-400">records</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <Clock className="w-5 h-5 text-emerald-400" />
              Hourly Activity
            </CardTitle>
            <CardDescription>Last 60 minutes</CardDescription>
          </CardHeader>
          <CardContent>
            {syncStatus && (
              <div className="space-y-4">
                <ActivityItem
                  label="A2A Messages"
                  value={syncStatus.recent_activity.a2a_messages_hourly}
                  icon={<Network className="w-4 h-4 text-blue-400" />}
                />
                <ActivityItem
                  label="LLM Collaborations"
                  value={syncStatus.recent_activity.llm_collaborations_hourly}
                  icon={<Cpu className="w-4 h-4 text-purple-400" />}
                />
                <ActivityItem
                  label="Brain Mutations"
                  value={syncStatus.recent_activity.brain_mutations_hourly}
                  icon={<Brain className="w-4 h-4 text-emerald-400" />}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Knowledge Layers */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Intelligence Layers
            </CardTitle>
            <CardDescription>Z-index stratification</CardDescription>
          </CardHeader>
          <CardContent>
            {brainStats && (
              <div className="space-y-4">
                {Object.entries(brainStats.layers).map(([layer, count]) => (
                  <div key={layer} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-300">{layer}</span>
                      <span className="text-white font-bold">{count}</span>
                    </div>
                    <Progress
                      value={(count / Math.max(...Object.values(brainStats.layers))) * 100}
                      className="h-2"
                    />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Nodes */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-xl lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <Network className="w-5 h-5 text-amber-400" />
              High-Mass Knowledge Nodes
            </CardTitle>
            <CardDescription>Most important concepts (by mass)</CardDescription>
          </CardHeader>
          <CardContent>
            {brainStats && (
              <div className="space-y-3">
                {brainStats.top_nodes.map((node, idx) => (
                  <div
                    key={node.id}
                    className="flex items-center gap-4 p-4 bg-slate-800/30 rounded-lg border border-slate-700/20 hover:border-emerald-500/30 transition-colors"
                  >
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-blue-500 flex items-center justify-center text-white font-bold text-sm">
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <div className="text-white font-medium">{node.label}</div>
                      <div className="text-xs text-slate-400 mt-1">
                        Layer: {node.z_index.toFixed(0)} • Mass: {node.mass.toFixed(1)}
                      </div>
                    </div>
                    <Badge variant="outline" className="bg-emerald-900/20 text-emerald-400 border-emerald-500/30">
                      {node.mass.toFixed(1)}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* LoRA Training */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <Zap className="w-5 h-5 text-purple-400" />
              LoRA Fine-Tuning
            </CardTitle>
            <CardDescription>Brain-as-Curriculum Training</CardDescription>
          </CardHeader>
          <CardContent>
            {trainingStatus && (
              <div className="space-y-6">
                <div>
                  <div className="text-3xl font-bold text-white mb-1">
                    {trainingStatus.training_samples_24h}
                  </div>
                  <div className="text-sm text-slate-400">Samples collected (24h)</div>
                </div>

                {trainingStatus.latest_lora_prep && (
                  <div className="p-4 bg-purple-900/10 border border-purple-500/20 rounded-lg">
                    <div className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-2">
                      Latest Prep
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Total Samples:</span>
                        <span className="text-white font-bold">
                          {trainingStatus.latest_lora_prep.total_samples}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">High Quality:</span>
                        <span className="text-emerald-400 font-bold">
                          {trainingStatus.latest_lora_prep.quality_metrics.high_quality_samples}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t border-slate-700/50">
                  <div className="text-xs text-slate-400 mb-1">Next Training:</div>
                  <div className="text-sm text-white font-mono">
                    {trainingStatus.next_scheduled_training}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Helper Components
function StatCard({ icon, label, value, sublabel, color }: any) {
  const colors: Record<string, string> = {
    blue: 'from-blue-500/10 to-blue-500/5 border-blue-500/20 text-blue-400',
    emerald: 'from-emerald-500/10 to-emerald-500/5 border-emerald-500/20 text-emerald-400',
    amber: 'from-amber-500/10 to-amber-500/5 border-amber-500/20 text-amber-400',
    purple: 'from-purple-500/10 to-purple-500/5 border-purple-500/20 text-purple-400',
  };

  return (
    <Card className={`bg-gradient-to-br ${colors[color]} backdrop-blur-xl border`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className={`p-2.5 rounded-xl bg-white/5 ${colors[color].split(' ')[2]}`}>
            {icon}
          </div>
        </div>
        <div className="text-sm text-slate-400 font-bold uppercase tracking-wider mb-1">
          {label}
        </div>
        <div className="text-3xl font-black text-white mb-1">
          {value.toLocaleString()}
        </div>
        <div className="text-xs text-slate-500 font-medium">
          {sublabel}
        </div>
      </CardContent>
    </Card>
  );
}

function ActivityItem({ label, value, icon }: any) {
  return (
    <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg">
      <div className="flex items-center gap-3">
        {icon}
        <span className="text-sm text-slate-300">{label}</span>
      </div>
      <span className="text-lg font-bold text-white">{value}</span>
    </div>
  );
}
