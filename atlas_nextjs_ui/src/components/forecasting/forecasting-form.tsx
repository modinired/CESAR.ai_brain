'use client';
import { useFormState, useFormStatus } from 'react-dom';
import { generateForecasts, type ForecastState } from '@/app/forecasting/actions';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, Zap, BrainCircuit, Bot } from 'lucide-react';
import { useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';

const initialState: ForecastState = {
  message: null,
};

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending} className="w-full">
      {pending ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...
        </>
      ) : (
        <>
          <Zap className="mr-2 h-4 w-4" /> Generate Forecasts
        </>
      )}
    </Button>
  );
}

export default function ForecastingForm() {
  const [state, formAction] = useFormState(generateForecasts, initialState);
  const { toast } = useToast();

  useEffect(() => {
    if (state.message && state.message !== 'success') {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: state.message,
      });
    }
  }, [state, toast]);

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <form action={formAction}>
        <Card>
          <CardHeader>
            <CardTitle>Forecasting Parameters</CardTitle>
            <CardDescription>
              Define scenarios, KPIs, and provide historical data for the AI to analyze.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="scenarios">Scenarios</Label>
              <Input
                id="scenarios"
                name="scenarios"
                placeholder="e.g., recession, boom, stable growth"
                defaultValue="recession, stable growth, boom"
              />
              <p className="text-xs text-muted-foreground">Enter comma-separated values.</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="kpis">Key Performance Indicators (KPIs)</Label>
              <Input
                id="kpis"
                name="kpis"
                placeholder="e.g., revenue, profit, market share"
                defaultValue="revenue, profit_margin, customer_acquisition_cost"
              />
              <p className="text-xs text-muted-foreground">Enter comma-separated values.</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="historicalData">Historical Data (CSV)</Label>
              <Textarea
                id="historicalData"
                name="historicalData"
                placeholder="Paste relevant historical data in CSV format..."
                className="min-h-[150px] font-mono text-xs"
                defaultValue="Year,Revenue,Profit_Margin,Customer_Acquisition_Cost\n2021,1000000,0.25,50\n2022,1200000,0.23,55\n2023,1500000,0.28,48"
              />
            </div>
          </CardContent>
          <CardFooter>
            <SubmitButton />
          </CardFooter>
        </Card>
      </form>
      
      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Forecast Results</CardTitle>
          <CardDescription>
            Generated forecasts for each scenario will appear here.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-grow">
          {!state.result && (
             <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-8 rounded-lg border-2 border-dashed">
                <Bot className="w-16 h-16 mb-4" />
                <h3 className="text-lg font-semibold text-foreground">Awaiting parameters</h3>
                <p>The AI is ready to generate forecasts.</p>
             </div>
          )}
          {state.result && (
            <Tabs defaultValue={state.result[0].scenario} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                {state.result.map(res => (
                  <TabsTrigger key={res.scenario} value={res.scenario} className="capitalize">{res.scenario}</TabsTrigger>
                ))}
              </TabsList>
              {state.result.map(res => (
                <TabsContent key={res.scenario} value={res.scenario} className="space-y-4">
                  <Alert>
                    <BrainCircuit className="h-4 w-4" />
                    <AlertTitle>AI Reasoning</AlertTitle>
                    <AlertDescription>{res.reasoning}</AlertDescription>
                  </Alert>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>KPI</TableHead>
                        <TableHead className="text-right">Forecasted Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Object.entries(res.forecast).map(([kpi, value]) => (
                        <TableRow key={kpi}>
                          <TableCell className="font-medium capitalize">{kpi.replace(/_/g, ' ')}</TableCell>
                          <TableCell className="text-right">{typeof value === 'number' ? value.toLocaleString(undefined, {style: 'currency', currency: 'USD'}) : value}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TabsContent>
              ))}
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
