'use server';

/**
 * @fileOverview A financial forecasting AI agent.
 *
 * - generateFinancialForecasts - A function that handles the generation of financial forecasts based on different scenarios.
 * - GenerateFinancialForecastsInput - The input type for the generateFinancialForecasts function.
 * - GenerateFinancialForecastsOutput - The return type for the generateFinancialForecasts function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const ForecastingToolInputSchema = z.object({
  scenario: z.string().describe('A description of the economic scenario to forecast under, e.g., a recession, a boom, etc.'),
  kpis: z.array(z.string()).describe('The key performance indicators to forecast.'),
  historicalData: z.string().describe('Historical financial data to consider when creating the forecast.'),
});

const ForecastingToolOutputSchema = z.object({
  forecast: z.record(z.string(), z.number()).describe('A map of KPIs to their forecasted values.'),
  reasoning: z.string().describe('The reasoning behind the forecast.'),
});

const forecastingTool = ai.defineTool({
  name: 'forecastingTool',
  description: 'Generates a financial forecast for a given scenario and set of KPIs.',
  inputSchema: ForecastingToolInputSchema,
  outputSchema: ForecastingToolOutputSchema,
}, async (input) => {
  console.log('Running forecasting tool with input:', input);
  // Mock implementation, replace with actual forecasting logic
  const forecast: Record<string, number> = {};
  input.kpis.forEach(kpi => {
    forecast[kpi] = Math.random() * 1000; // Example random forecast
  });
  const reasoning = `This forecast is based on the assumption that the ${input.scenario} will cause these random changes in KPIs.`;
  return {forecast, reasoning};
});

const GenerateFinancialForecastsInputSchema = z.object({
  scenarios: z.array(z.string()).describe('An array of economic scenarios to generate forecasts for, e.g., ["recession", "boom", "stable growth"].'),
  kpis: z.array(z.string()).describe('The key performance indicators to forecast, e.g., ["revenue", "profit", "market share"].'),
  historicalData: z.string().describe('Historical financial data to consider when creating the forecast.'),
});
export type GenerateFinancialForecastsInput = z.infer<typeof GenerateFinancialForecastsInputSchema>;

const GenerateFinancialForecastsOutputSchema = z.array(z.object({
  scenario: z.string().describe('The scenario that was forecasted.'),
  forecast: z.record(z.string(), z.number()).describe('A map of KPIs to their forecasted values.'),
  reasoning: z.string().describe('The reasoning behind the forecast.'),
})).describe('An array of financial forecasts, one for each scenario.');
export type GenerateFinancialForecastsOutput = z.infer<typeof GenerateFinancialForecastsOutputSchema>;

export async function generateFinancialForecasts(input: GenerateFinancialForecastsInput): Promise<GenerateFinancialForecastsOutput> {
  return generateFinancialForecastsFlow(input);
}

const generateFinancialForecastsPrompt = ai.definePrompt({
  name: 'generateFinancialForecastsPrompt',
  tools: [forecastingTool],
  input: {
    schema: GenerateFinancialForecastsInputSchema,
  },
  prompt: `For each scenario in scenarios, use the forecastingTool to generate a financial forecast for the following KPIs: {{kpis}}.  Use the following historical data: {{historicalData}}.  Return an array of forecasts, one for each scenario. Scenarios: {{scenarios}}`,
});

const generateFinancialForecastsFlow = ai.defineFlow({
  name: 'generateFinancialForecastsFlow',
  inputSchema: GenerateFinancialForecastsInputSchema,
  outputSchema: GenerateFinancialForecastsOutputSchema,
}, async (input) => {
  const forecasts: any[] = [];
  for (const scenario of input.scenarios) {
    const {forecast, reasoning} = await forecastingTool({
      scenario,
      kpis: input.kpis,
      historicalData: input.historicalData,
    });

    forecasts.push({
      scenario,
      forecast,
      reasoning,
    });
  }

  return forecasts;
});
