'use client';

import AppLayout from '@/components/layout/app-layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { GitBranch, PlusCircle, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

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

  useEffect(() => {
    const load = async () => {
      try {
        // Fetch a handful of workflow IDs; for demo, try known IDs seeded
        const wfIds = ['wf_pipeline_opt', 'wf_finance_close', 'wf_incident_triage'];
        const results: WorkflowMatrix[] = [];
        for (const id of wfIds) {
          const res = await fetch(`${apiBase}/atlas/automation/matrix/${id}`);
          if (!res.ok) continue;
          results.push(await res.json());
        }
        setMatrices(results);
      } catch (e: any) {
        setError(e.message || 'Failed to load workflows');
      }
    };
    void load();
  }, [apiBase]);

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
                  <Button variant="ghost" size="sm">Events</Button>
                  <Button variant="outline" size="sm">Swap</Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
