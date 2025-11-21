'use client';

import AppLayout from '@/components/layout/app-layout';
import { AgentCard } from '@/components/agents/agent-card';
import { Button } from '@/components/ui/button';
import { PlusCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

type ApiAgent = {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  status: string;
  performance_score?: number;
};

type Cognition = {
  score: number;
  subscores: Record<string, number>;
};

export default function AgentsPage() {
  const apiBase = useMemo(
    () => (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011').replace(/\/$/, ''),
    []
  );
  const [agents, setAgents] = useState<ApiAgent[]>([]);
  const [cognition, setCognition] = useState<Record<string, Cognition>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAgents = async () => {
      try {
        const res = await fetch(`${apiBase}/api/agents`);
        if (!res.ok) throw new Error(`Failed to fetch agents (${res.status})`);
        const data: ApiAgent[] = await res.json();
        setAgents(data);
        // fetch cognition per agent
        data.forEach(async (a) => {
          try {
            const cRes = await fetch(`${apiBase}/atlas/agents/${a.agent_id || a.id}/cognition`);
            if (!cRes.ok) return;
            const cData = await cRes.json();
            setCognition((prev) => ({
              ...prev,
              [a.id]: { score: cData.score, subscores: cData.subscores },
            }));
          } catch {
            /* ignore per-agent errors */
          }
        });
      } catch (e: any) {
        setError(e.message || 'Failed to load agents');
      }
    };
    void loadAgents();
  }, [apiBase]);

  return (
    <AppLayout>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">
            Multi-Agent Coordination Platform
          </h2>
          <div className="flex items-center space-x-2">
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" /> Add Agent
            </Button>
          </div>
        </div>
        <p className="text-muted-foreground">
          Manage and monitor a dynamic ecosystem of specialized AI agents working in concert.
        </p>
        {error && <div className="text-sm text-red-400">{error}</div>}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {agents.map((agent) => {
            const cog = cognition[agent.id];
            return (
              <AgentCard
                key={agent.id}
                agent={{
                  id: agent.agent_id || agent.id,
                  name: agent.agent_name || agent.agent_id || agent.id,
                  role: agent.agent_type || 'Agent',
                  status: agent.status,
                  performance: agent.performance_score ?? 0,
                  cognition: cog?.score,
                }}
              />
            );
          })}
        </div>
      </div>
    </AppLayout>
  );
}
