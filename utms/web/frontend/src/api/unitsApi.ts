import { Unit, CreateUnitData, UpdateUnitField } from '../types/units';

export const unitsApi = {
    getUnits: async (): Promise<Record<string, Unit>> => {
	const response = await fetch('/api/units');
	if (!response.ok) throw new Error('Failed to fetch units');
	return response.json();
    },

    createUnit: async (data: CreateUnitData): Promise<Unit> => {
	const response = await fetch('/api/units/', {
	    method: 'POST',
	    headers: { 'Content-Type': 'application/json' },
	    body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create unit');
	return response.json();
    },

    updateUnit: async (label: string, updates: Partial<{
	label: string;
	name: string;
	value: string;
	groups: string[];
    }>): Promise<{ new_label: string }> => {
	const response = await fetch(`/api/units/${label}`, {
	    method: 'PUT',
	    headers: {
		'Content-Type': 'application/json',
	    },
	    body: JSON.stringify(updates)
	});

	if (!response.ok) {
	    throw new Error('Failed to update unit');
	}

	return response.json();
    },


    deleteUnit: async (label: string): Promise<void> => {
	const response = await fetch(`/api/units/${label}`, {
	    method: 'DELETE'
	});
	if (!response.ok) throw new Error('Failed to delete unit');
    },
};
