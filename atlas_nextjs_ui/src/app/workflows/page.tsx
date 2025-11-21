'use client';

import AppLayout from '@/components/layout/app-layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { GitBranch, PlusCircle, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';

type WorkflowStep = {
  id: string;
  name: string;
  type: string;
  expected_duration_ms?: number;
  stats?: Record<string, any>;
};

type Bottleneck = {
  step_id: string;
  score: number;
  backlog_count: number;
  updated_at: string;
};

type WorkflowMatrix = {
  workflow_id: string;
  steps: WorkflowStep[];
  bottlenecks: Bottleneck[];
};

type WorkflowEvent = {
  id: string;
  step: string;
  actor_type: string;
  actor_id?: string | null;
  status: string;
  latency_ms?: number | null;
  created_at: string;
};

const apiKey = process.env.NEXT_PUBLIC_API_KEY;

const statusIcons = {
  running: <Clock className="w-4 h-4 text-blue-500" />,
  completed: <CheckCircle2 className="w-4 h-4 text-green-500" />,
  failed: <AlertCircle className="w-4 h-4 text-red-500" />,
};

const statusBadges = {
  running: 'default',
  completed: 'secondary',
  failed: 'destructive',
} as const;

export default function WorkflowsPage() {
  const apiBase = useMemo(
    () => (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011').replace(/\/$/, ''),
    []
  );
  const [matrices, setMatrices] = useState<WorkflowMatrix[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [swapStep, setSwapStep] = useState<string>('');
  const [swapActor, setSwapActor] = useState<string>('');
  const [swapStatus, setSwapStatus] = useState<string | null>(null);
  const [events, setEvents] = useState<Record<string, WorkflowEvent[]>>({});

  useEffect(() => {
    const load = async () => {
      try {
        const wfRes = await fetch(`${apiBase}/atlas/automation/workflows`);
        const wfData = wfRes.ok ? await wfRes.json() : { workflows: [] };
        const wfIds: string[] = wfData.workflows || [];
        const results: WorkflowMatrix[] = [];
        for (const id of wfIds) {
          const res = await fetch(`${apiBase}/atlas/automation/matrix/${id}`);
          if (!res.ok) continue;
          results.push(await res.json());
          const evRes = await fetch(`${apiBase}/atlas/automation/matrix/${id}/events?limit=10`);
          if (evRes.ok) {
            const evts: WorkflowEvent[] = await evRes.json();
            setEvents((prev) => ({ ...prev, [id]: evts }));
          }
        }
        setMatrices(results);
      } catch (e: any) {
        setError(e.message || 'Failed to load workflows');
      }
    };
    void load();
  }, [apiBase]);

  const doSwap = async (workflow_id: string) => {
    if (!swapStep || !swapActor) {
      setSwapStatus('Step and new actor ID required');
      return;
    }
    setSwapStatus(null);
    try {
      const res = await fetch(`${apiBase}/atlas/automation/matrix/swap`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        },
        body: JSON.stringify({
          workflow_id,
          step: swapStep,
          new_actor_id: swapActor,
          new_actor_type: 'agent',
        }),
      });
      if (!res.ok) throw new Error(`Swap failed (${res.status})`);
      const data = await res.json();
      setSwapStatus(`Swap recorded for ${data.step} -> ${data.new_actor_id}`);
    } catch (e: any) {
      setSwapStatus(e.message || 'Swap failed');
    }
  };

  return (
    <AppLayout>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-3 rounded-lg">
              <GitBranch className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-3xl font-bold tracking-tight">
                Workflow Automation
              </h2>
              <p className="text-muted-foreground">
                Live Automation Matrix with bottlenecks and events.
              </p>
            </div>
          </div>
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" /> Create Workflow
          </Button>
        </div>
        {error && <div className="text-sm text-red-400">{error}</div>}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {matrices.map((matrix) => (
            <Card key={matrix.workflow_id} className="flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{matrix.workflow_id}</span>
                  <Badge variant="secondary" className="capitalize">
                    {matrix.bottlenecks?.length ? 'bottlenecked' : 'healthy'}
                  </Badge>
                </CardTitle>
                <CardDescription>Steps: {matrix.steps.length}</CardDescription>
              </CardHeader>
              <CardContent className="flex-grow space-y-3">
                {matrix.steps.map((step) => (
                  <div key={step.id} className="p-3 rounded-lg border border-dashed border-white/10 text-sm">
                    <div className="flex justify-between">
                      <span className="font-semibold">{step.name}</span>
                      <span className="uppercase text-xs text-muted-foreground">{step.type}</span>
                    </div>
                    {step.stats && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {step.stats.count ? `${step.stats.count} events` : 'No events'}
                        {step.stats.avg_latency ? ` • avg ${Math.round(step.stats.avg_latency)} ms` : ''}
                      </div>
                    )}
                  </div>
                ))}
                <Separator />
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-muted-foreground">Recent events</div>
                  {(events[matrix.workflow_id] || []).map((evt) => (
                    <div key={evt.id} className="flex justify-between text-xs text-muted-foreground p-2 rounded bg-white/5">
                      <div className="flex gap-2">
                        <span className="font-semibold text-foreground">{evt.step}</span>
                        <span className="uppercase">{evt.actor_type}</span>
                        {evt.actor_id && <span>{evt.actor_id}</span>}
                      </div>
                      <div className="flex gap-3">
                        <span className="capitalize">{evt.status}</span>
                        {evt.latency_ms ? <span>{evt.latency_ms} ms</span> : null}
                        <span>{new Date(evt.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                  {(events[matrix.workflow_id] || []).length === 0 && (
                    <div className="text-xs text-muted-foreground">No recent events.</div>
                  )}
                </div>
                {matrix.bottlenecks?.length > 0 && (
                  <div className="text-xs text-red-400">
                    Bottlenecks: {matrix.bottlenecks.map((b) => b.step_id).join(', ')}
                  </div>
                )}
              </CardContent>
              <CardFooter className="flex justify-between text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  {statusIcons['running']}
                  <span>{matrix.workflow_id}</span>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => doSwap(matrix.workflow_id)}>Swap</Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Swap Human → Agent</CardTitle>
            <CardDescription>Record a swap for a step in the selected workflow.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Input placeholder="Step name" value={swapStep} onChange={(e) => setSwapStep(e.target.value)} />
            <Input placeholder="New agent ID" value={swapActor} onChange={(e) => setSwapActor(e.target.value)} />
            <Button onClick={() => doSwap(matrices[0]?.workflow_id || '')} disabled={!matrices.length}>
              Execute Swap
            </Button>
          </CardContent>
          {swapStatus && <div className="px-6 pb-4 text-sm text-muted-foreground">{swapStatus}</div>}
        </Card>
      </div>
    </AppLayout>
  );
}
