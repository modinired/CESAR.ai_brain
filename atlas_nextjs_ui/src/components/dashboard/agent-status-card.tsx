import { mockAgents } from '@/lib/mock-data';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export function AgentStatusCard() {
  const statusVariant = {
    active: 'default',
    idle: 'secondary',
    error: 'destructive',
  } as const;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Agent Status</CardTitle>
        <CardDescription>
          Real-time monitoring of the AI agent ecosystem.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockAgents.slice(0, 5).map((agent) => (
            <div key={agent.id} className="flex items-center">
              <Avatar className="h-9 w-9">
                <AvatarImage src={`https://picsum.photos/seed/${agent.id}/100/100`} alt={agent.name} data-ai-hint="abstract robot" />
                <AvatarFallback>{agent.name.charAt(0)}</AvatarFallback>
              </Avatar>
              <div className="ml-4 space-y-1">
                <p className="text-sm font-medium leading-none">{agent.name}</p>
                <p className="text-sm text-muted-foreground">{agent.role}</p>
              </div>
              <div className="ml-auto font-medium">
                <Badge variant={statusVariant[agent.status]} className="capitalize">
                  {agent.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
