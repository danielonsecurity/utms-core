export async function updateUnit(label, field, value) {
    try {
        const response = await fetch(`/api/units/${label}/${field}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ value })
        });

        if (!response.ok) {
            throw new Error(`Failed to update unit ${field}`);
        }

        return response.json();
    } catch (error) {
        console.error(`Error updating unit ${field}:`, error);
        throw error;
    }
}

export async function createUnit(data) {
    const { label, name, value, groups } = data;
    
    if (!label || !name || !value) {
        throw new Error('Missing required fields');
    }

    try {
        const response = await fetch('/api/units/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                label,
                name,
                value,
                groups
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create unit');
        }

        return response.json();
    } catch (error) {
        console.error('Error creating unit:', error);
        throw error;
    }
}

export async function deleteUnit(label) {
    try {
        const response = await fetch(`/api/units/${label}`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            throw new Error('Failed to delete unit');
        }

        // Remove the card from DOM after successful deletion
        const card = document.querySelector(`[data-unit="${label}"]`);
        if (card) {
            card.remove();
        }
      return response.json();
    } catch (error) {
        console.error('Error deleting unit:', error);
        throw error;
    }
}
