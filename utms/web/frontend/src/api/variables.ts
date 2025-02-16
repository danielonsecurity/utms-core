import { Variable } from '../types/variables';

export const variablesApi = {
  getVariables: async (): Promise<Record<string, Variable>> => {
    console.log('Fetching variables...'); // Debug log
    const response = await fetch('/api/variables');
    if (!response.ok) {
      throw new Error('Failed to fetch variables');
    }
    const data = await response.json();
    console.log('Received data:', data); // Debug log
    return data;
  }
};
