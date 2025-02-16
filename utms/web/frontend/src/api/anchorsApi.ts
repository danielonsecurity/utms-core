import { Anchor, CreateAnchorData, UpdateAnchorData } from '../types/anchors';

export const anchorsApi = {
    getAnchors: async (): Promise<Record<string, Anchor>> => {
        const response = await fetch('/api/anchors');
        if (!response.ok) throw new Error('Failed to fetch anchors');
        return response.json();
    },

    createAnchor: async (data: CreateAnchorData): Promise<Anchor> => {
        const response = await fetch('/api/anchors/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create anchor');
        return response.json();
    },

    updateAnchor: async (label: string, updates: UpdateAnchorData): Promise<void> => {
        const response = await fetch(`/api/anchors/${label}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        if (!response.ok) throw new Error('Failed to update anchor');
    },

    deleteAnchor: async (label: string): Promise<void> => {
        const response = await fetch(`/api/anchors/${label}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete anchor');
    }
};
