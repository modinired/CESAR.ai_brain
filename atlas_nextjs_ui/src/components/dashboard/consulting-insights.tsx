import { BrainCircuit } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Separator } from '../ui/separator';

export function ConsultingInsights() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-6 h-6 text-primary" />
          <CardTitle>CESAR.AI Consulting Insights</CardTitle>
        </div>
        <CardDescription>
          Expert analysis to guide your decision-making.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        <div className="flex items-start gap-4">
          <div className="font-semibold text-primary">Tip</div>
          <div className="text-muted-foreground">
            Revenue growth in Q2 is strong, but watch for increased market
            volatility. Consider running a 'recession' scenario in the
            forecasting tool.
          </div>
        </div>
        <Separator />
        <div className="flex items-start gap-4">
          <div className="font-semibold text-primary">Alert</div>
          <div className="text-muted-foreground">
            The AnomalyBot agent has detected unusual expense patterns in the
            logistics department. A detailed report is available on the{' '}
            <span className="font-medium text-foreground">Anomalies</span> page.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
