export async function updateAnchor(label, field, value) {
    try {
        const response = await fetch(`/api/anchors/${label}/${field}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ value })
        });

        if (!response.ok) {
            throw new Error(`Failed to update anchor ${field}`);
        }

        return response.json();
    } catch (error) {
        console.error(`Error updating anchor ${field}:`, error);
        throw error;
    }
}

export async function deleteAnchor(label) {
    try {
        const response = await fetch(`/api/anchors/${label}`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            throw new Error('Failed to delete anchor');
        }

        return response.json();
    } catch (error) {
        console.error('Error deleting anchor:', error);
        throw error;
    }
}


export async function saveField(anchorLabel, fieldName, button) {
    const container = button.closest('.anchor-card__evaluated-value');
    const input = container.querySelector('.anchor-card__edit-input');
    const newValue = input.value;
    
    try {
        const response = await fetch(`/api/anchors/${anchorLabel}/${fieldName}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ value: newValue })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save');
        }
        
        // Update display
        const valueDisplay = container.querySelector('.anchor-card__value');
        valueDisplay.textContent = newValue;
        container.classList.remove('editing');
        
    } catch (error) {
        alert('Error saving: ' + error.message);
    }
}

export async function saveNumericField(anchorLabel, fieldName, button) {
    const container = button.closest('.anchor-card__evaluated-value');
    const input = container.querySelector('.anchor-card__edit-input');
    const newValue = input.value;
    
    // Basic numeric validation
    if (!newValue || isNaN(newValue)) {
        alert('Please enter a valid number');
        return;
    }
    
    try {
        const response = await fetch(`/api/anchors/${anchorLabel}/${fieldName}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ value: Number(newValue) })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save');
        }
        
        // Update display
        const valueDisplay = container.querySelector('.anchor-card__value');
        valueDisplay.textContent = newValue;
        container.classList.remove('editing');
        
        // Refresh the page to get updated data
        location.reload();
        
    } catch (error) {
        alert('Error saving: ' + error.message);
    }
}


export async function saveTextField(anchorLabel, fieldName, button) {
  const container = button.closest('.anchor-card__evaluated-value');
    const input = container.querySelector('.anchor-card__edit-input');
    const newValue = input.value;
    
    try {
        const response = await fetch(`/api/anchors/${anchorLabel}/${fieldName}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ value: newValue })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save');
        }
        
        // Update display
        const valueDisplay = container.querySelector('.anchor-card__value');
        valueDisplay.textContent = newValue;
        container.classList.remove('editing');
        
        // Refresh the page to get updated data
        location.reload();
        
    } catch (error) {
        alert('Error saving: ' + error.message);
    }
}

export async function saveAnchorEdit(label) {
    const card = document.querySelector(`[data-anchor="${label}"]`);
    const updatedData = {
        label: card.querySelector('[data-field="label"]').textContent,
        name: card.querySelector('[data-field="name"]').textContent,
        value: parseFloat(card.querySelector('[data-field="value"]').textContent),
        groups: Array.from(card.querySelectorAll('.groups__name')).map(span => span.textContent)
    };

    try {
        const response = await fetch(`/api/anchors/${label}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedData)
        });

        if (!response.ok) {
            throw new Error('Failed to update anchor');
        }

        exitEditMode(card);
    } catch (error) {
        console.error('Error updating anchor:', error);
        alert('Failed to update anchor');
    }
}
