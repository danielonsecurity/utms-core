import { ResolveRequest, ResolveResult } from '../types/resolve';

export const resolveApi = {
    resolveTime: async (data: ResolveRequest): Promise<ResolveResult> => {
        const response = await fetch('/api/resolve/resolve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to resolve time');
        }

        return response.json();
    }
};
