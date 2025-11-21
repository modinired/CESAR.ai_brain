import type { Agent } from '@/lib/types';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Bot, Cpu, Gauge, Terminal } from 'lucide-react';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';

type AgentCardProps = {
  agent: Agent;
};

const statusConfig = {
  active: {
    color: 'bg-green-500',
    variant: 'default',
    text: 'Active',
  },
  idle: {
    color: 'bg-yellow-500',
    variant: 'secondary',
    text: 'Idle',
  },
  error: {
    color: 'bg-red-500',
    variant: 'destructive',
    text: 'Error',
  },
} as const;

export function AgentCard({ agent }: AgentCardProps) {
  const config = statusConfig[agent.status];
  const perf = Math.max(0, Math.min(100, agent.performance || 0));
  const cognition = agent.cognition !== undefined ? Math.max(0, Math.min(100, agent.cognition)) : null;

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-2 rounded-lg">
              <Bot className="w-6 h-6 text-primary" />
            </div>
            <div>
              <CardTitle>{agent.name}</CardTitle>
              <CardDescription>{agent.role}</CardDescription>
            </div>
          </div>
          <Badge variant={config.variant}>
            <span
              className={`mr-2 h-2 w-2 rounded-full ${config.color}`}
            />
            {config.text}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-grow space-y-4">
        {agent.task && (
          <div className="text-sm text-muted-foreground flex items-start gap-2">
            <Terminal className="w-4 h-4 mt-0.5 shrink-0" />
            <span>Task: <span className="font-medium text-foreground">{agent.task}</span></span>
          </div>
        )}
        <div>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-muted-foreground flex items-center gap-2">
                <Gauge className="w-4 h-4" /> Performance
            </span>
            <span className="font-semibold text-primary">{perf}%</span>
          </div>
          <Progress value={perf} />
        </div>
        {cognition !== null && (
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted-foreground flex items-center gap-2">
                <Cpu className="w-4 h-4" /> Cognition
              </span>
              <span className="font-semibold text-primary">{cognition}</span>
            </div>
            <Progress value={cognition} />
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button variant="outline" className="w-full">
          View Details
        </Button>
      </CardFooter>
    </Card>
  );
}
