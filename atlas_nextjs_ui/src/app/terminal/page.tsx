import AppLayout from '@/components/layout/app-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function TerminalPage() {
  return (
    <AppLayout>
      <div className="flex-1 p-4 md:p-8 pt-6 h-[calc(100vh-60px)]">
        <Card className="h-full flex flex-col bg-gray-900 text-gray-200 font-mono border-gray-700">
            <CardHeader className="border-b border-gray-700">
                <CardTitle className="text-gray-200">CLI Terminal</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-4 text-sm">
                <p><span className="text-green-400">user@cesar-ai</span>:<span className="text-blue-400">~</span>$ ls -l</p>
                <p>total 8</p>
                <p>drwxr-xr-x 2 user user 4096 Jun 10 10:30 documents</p>
                <p>drwxr-xr-x 2 user user 4096 Jun 10 10:31 forecasts</p>
                <br/>
                <p><span className="text-green-400">user@cesar-ai</span>:<span className="text-blue-400">~</span>$ run forecast --scenario=recession</p>
                <p>Initializing forecasting agent...</p>
                <p>Loading historical data model...</p>
                <p>Generating forecast for 'recession' scenario... <span className="animate-pulse">|</span></p>
                <br/>
                <p className="text-green-400">Forecast complete.</p>
                <p>Results saved to /forecasts/recession_q3_2024.json</p>
                <br/>
                <p><span className="text-green-400">user@cesar-ai</span>:<span className="text-blue-400">~</span>$ <span className="animate-pulse">_</span></p>
            </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
