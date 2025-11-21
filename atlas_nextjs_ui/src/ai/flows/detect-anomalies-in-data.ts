'use server';
/**
 * @fileOverview Detects anomalies in financial data using Genkit.
 *
 * - detectAnomalies - A function that detects anomalies in financial data.
 * - DetectAnomaliesInput - The input type for the detectAnomalies function.
 * - DetectAnomaliesOutput - The return type for the detectAnomalies function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const DetectAnomaliesInputSchema = z.object({
  financialData: z
    .string()
    .describe(
      'A string containing financial data, such as time series data. Must be a CSV with headers.'
    ),
  description: z
    .string()
    .optional()
    .describe('Optional description of the financial data.'),
});
export type DetectAnomaliesInput = z.infer<typeof DetectAnomaliesInputSchema>;

const DetectAnomaliesOutputSchema = z.object({
  anomalies: z.array(z.string()).describe('An array of strings describing the anomalies detected in the financial data.'),
  summary: z.string().describe('A summary of the detected anomalies.'),
});
export type DetectAnomaliesOutput = z.infer<typeof DetectAnomaliesOutputSchema>;

export async function detectAnomalies(input: DetectAnomaliesInput): Promise<DetectAnomaliesOutput> {
  return detectAnomaliesFlow(input);
}

const prompt = ai.definePrompt({
  name: 'detectAnomaliesPrompt',
  input: {schema: DetectAnomaliesInputSchema},
  output: {schema: DetectAnomaliesOutputSchema},
  prompt: `You are an expert financial analyst specializing in anomaly detection.

You will analyze the provided financial data and identify any anomalies or unusual patterns.

Provide a detailed description of each anomaly detected, including the specific data points and reasons for considering them anomalous.  Output the anomalies as an array of strings.
Also generate a brief summary of all the anomalies detected.

Financial Data:
{{financialData}}

{% if description %}Description: {{description}}{% endif %}`,
});

const detectAnomaliesFlow = ai.defineFlow(
  {
    name: 'detectAnomaliesFlow',
    inputSchema: DetectAnomaliesInputSchema,
    outputSchema: DetectAnomaliesOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
