'use client';
import { useFormState, useFormStatus } from 'react-dom';
import { detectDataAnomalies, type AnomalyState } from '@/app/anomalies/actions';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, Bot, Loader2, Sparkles } from 'lucide-react';
import { useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';

const initialState: AnomalyState = {
  message: null,
};

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending} className="w-full">
      {pending ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing...
        </>
      ) : (
        <>
          <Sparkles className="mr-2 h-4 w-4" /> Detect Anomalies
        </>
      )}
    </Button>
  );
}

const exampleData = `Date,Revenue,Expenses\n2023-01-01,1000,500\n2023-01-02,1100,550\n2023-01-03,950,480\n2023-01-04,15000,600\n2023-01-05,1200,590`;

export default function AnomalyForm() {
  const [state, formAction] = useFormState(detectDataAnomalies, initialState);
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
            <CardTitle>Input Data</CardTitle>
            <CardDescription>
              Paste your financial data in CSV format below. Ensure it includes headers.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              name="financialData"
              placeholder="e.g., Date,Revenue,Expenses..."
              className="min-h-[250px] font-mono text-xs"
              defaultValue={exampleData}
            />
          </CardContent>
          <CardFooter>
            <SubmitButton />
          </CardFooter>
        </Card>
      </form>

      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Analysis Results</CardTitle>
          <CardDescription>
            Anomalies and insights will appear here after analysis.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-grow">
          {!state.result && (
             <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-8 rounded-lg border-2 border-dashed">
                <Bot className="w-16 h-16 mb-4" />
                <h3 className="text-lg font-semibold text-foreground">Waiting for data</h3>
                <p>The AI is ready to analyze your data.</p>
             </div>
          )}
          {state.result && (
            <div className="space-y-4">
              <Alert>
                <Sparkles className="h-4 w-4" />
                <AlertTitle>AI Summary</AlertTitle>
                <AlertDescription>{state.result.summary}</AlertDescription>
              </Alert>
              <h3 className="font-semibold text-lg mt-4">Detected Anomalies:</h3>
              <div className="space-y-3">
                {state.result.anomalies.map((anomaly, index) => (
                  <Alert key={index} variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Anomaly #{index + 1}</AlertTitle>
                    <AlertDescription>{anomaly}</AlertDescription>
                  </Alert>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
