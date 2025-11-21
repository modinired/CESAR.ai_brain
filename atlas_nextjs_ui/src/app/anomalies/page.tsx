import AppLayout from '@/components/layout/app-layout';
import AnomalyForm from '@/components/anomalies/anomaly-form';
import { BarChart, ShieldCheck } from 'lucide-react';

export default function AnomalyDetectionPage() {
  return (
    <AppLayout>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-3 rounded-lg">
              <BarChart className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-3xl font-bold tracking-tight">
                Automated Anomaly Detection
              </h2>
              <p className="text-muted-foreground">
                Detect and highlight anomalies in financial data and agent behavior using AI.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm text-muted-foreground bg-card p-3 rounded-lg border">
          <ShieldCheck className="w-4 h-4 text-green-500" />
          <span>
            Your data is processed securely and is not used for training. All data is stored locally.
          </span>
        </div>

        <AnomalyForm />
      </div>
    </AppLayout>
  );
}
