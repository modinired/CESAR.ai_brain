'use server';

import { detectAnomalies } from '@/ai/flows/detect-anomalies-in-data';
import { z } from 'zod';

const schema = z.object({
  financialData: z.string().min(1, { message: 'Financial data cannot be empty.' }),
});

export type AnomalyState = {
  message: string | null;
  result?: {
    anomalies: string[];
    summary: string;
  };
};

export async function detectDataAnomalies(
  prevState: AnomalyState,
  formData: FormData
): Promise<AnomalyState> {
  const validatedFields = schema.safeParse({
    financialData: formData.get('financialData'),
  });

  if (!validatedFields.success) {
    return {
      message: 'Invalid data. ' + validatedFields.error.flatten().fieldErrors.financialData?.join(', '),
    };
  }

  try {
    const result = await detectAnomalies({
      financialData: validatedFields.data.financialData,
    });
    return { message: 'success', result };
  } catch (error) {
    console.error(error);
    return { message: 'An error occurred while analyzing the data.' };
  }
}
