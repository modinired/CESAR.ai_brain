import Link from 'next/link';
import { LineChart, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import Image from 'next/image';

export function ScenarioForecastCard() {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center gap-2">
          <LineChart className="w-6 h-6 text-primary" />
          <CardTitle>AI-Powered Scenario Planning</CardTitle>
        </div>
        <CardDescription>
          Generate multiple financial forecasts under different conditions to
          anticipate market changes and de-risk decisions.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-grow relative">
        <Image
          src="https://picsum.photos/seed/forecast/800/400"
          alt="Abstract representation of financial forecasts"
          data-ai-hint="abstract chart"
          fill
          className="object-cover rounded-md"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-4 left-4">
          <h3 className="text-lg font-semibold text-white">Impact on Key KPIs</h3>
          <p className="text-sm text-gray-300">
            Utilize a forecasting tool to see how scenarios like recessions or market booms affect your bottom line.
          </p>
        </div>
      </CardContent>
      <CardFooter>
        <Link href="/forecasting" className="w-full">
          <Button className="w-full">
            <Zap className="mr-2 h-4 w-4" />
            Generate Forecasts
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}
