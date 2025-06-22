export async function updateConfig(key, value) {
    try {
        const response = await fetch(`/api/config/${key}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(value)
        });

        if (!response.ok) {
            throw new Error('Failed to update configuration');
        }

        return response.json();
    } catch (error) {
        console.error('Error updating configuration:', error);
        throw error;
    }
}

export async function updateListItem(key, index, value) {
    try {
        const response = await fetch(`/api/config/${key}/${index}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(value)
        });

        if (!response.ok) {
            throw new Error('Failed to update list item');
        }

        return response.json();
    } catch (error) {
        console.error('Error updating list item:', error);
        throw error;
    }
}

export async function addNewListItem(key) {
    try {
        const response = await fetch(`/api/config/${key}/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify('')
        });

        if (!response.ok) {
            throw new Error('Failed to add list item');
        }

        return response.json();
    } catch (error) {
        console.error('Error adding list item:', error);
        throw error;
    }
}
