'use server';

import { generateFinancialForecasts } from '@/ai/flows/generate-financial-forecasts';
import type { Forecast } from '@/lib/types';
import { z } from 'zod';

const schema = z.object({
  scenarios: z.string().min(1, { message: 'Scenarios cannot be empty.' }),
  kpis: z.string().min(1, { message: 'KPIs cannot be empty.' }),
  historicalData: z.string().min(1, { message: 'Historical data cannot be empty.' }),
});

export type ForecastState = {
  message: string | null;
  result?: Forecast[];
};

export async function generateForecasts(
  prevState: ForecastState,
  formData: FormData
): Promise<ForecastState> {
  const validatedFields = schema.safeParse({
    scenarios: formData.get('scenarios'),
    kpis: formData.get('kpis'),
    historicalData: formData.get('historicalData'),
  });

  if (!validatedFields.success) {
    const errors = validatedFields.error.flatten().fieldErrors;
    const errorMessage = Object.values(errors).flat().join(', ');
    return {
      message: 'Invalid data. ' + errorMessage,
    };
  }

  try {
    const scenariosArray = validatedFields.data.scenarios.split(',').map(s => s.trim()).filter(s => s);
    const kpisArray = validatedFields.data.kpis.split(',').map(s => s.trim()).filter(s => s);

    if(scenariosArray.length === 0 || kpisArray.length === 0) {
      return { message: 'Please provide at least one scenario and one KPI.' };
    }

    const result = await generateFinancialForecasts({
      scenarios: scenariosArray,
      kpis: kpisArray,
      historicalData: validatedFields.data.historicalData,
    });
    return { message: 'success', result };
  } catch (error) {
    console.error(error);
    return { message: 'An error occurred while generating forecasts.' };
  }
}
