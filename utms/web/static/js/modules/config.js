import { updateConfig, updateListItem, addNewListItem } from '../api/configApi.js';

async function saveConfig(key) {
    try {
        const value = document.getElementById(key).value;
        await updateConfig(key, value);
        alert('Configuration saved successfully');
    } catch (error) {
        alert('Error saving configuration: ' + error.message);
    }
}

async function saveListItem(key, index) {
    try {
        const value = document.getElementById(`${key}_${index}`).value;
        await updateListItem(key, index, value);
        alert('List item saved successfully');
    } catch (error) {
        alert('Error saving list item: ' + error.message);
    }
}

async function addListItem(key) {
    try {
        await addNewListItem(key);
        location.reload();  // Refresh to show new item
    } catch (error) {
        alert('Error adding list item: ' + error.message);
    }
}

async function handleSelectChange(key, index = null) {
    const selectId = index !== null ? `${key}_${index}` : key;
    const select = document.getElementById(selectId);
    
    if (select.value === '__new__') {
        const newValue = prompt('Enter new value:');
        if (newValue) {
            const option = document.createElement('option');
            option.value = newValue;
            option.textContent = newValue;
            select.insertBefore(option, select.lastElementChild);
            select.value = newValue;
            
            try {
                if (index !== null) {
                    await saveListItem(key, index);
                } else {
                    await saveConfig(key);
                }
            } catch (error) {
                alert('Error saving new value: ' + error.message);
                // Reset to previous value if save fails
                select.value = select.querySelector('option:checked').value;
            }
        } else {
            // Reset to previous value if user cancels
            select.value = select.querySelector('option:checked').value;
        }
    }
}

export function initializeConfig() {
    // Initialize select change handlers
    document.querySelectorAll('.config__select').forEach(select => {
        const key = select.dataset.key;
        const index = select.dataset.index;
        select.addEventListener('change', () => handleSelectChange(key, index));
    });

    // Initialize save buttons
    document.querySelectorAll('.config__btn--save').forEach(button => {
        const key = button.dataset.key;
        const index = button.dataset.index;
        button.addEventListener('click', () => {
            if (index !== undefined) {
                saveListItem(key, index);
            } else {
                saveConfig(key);
            }
        });
    });

    // Initialize add list item buttons
    document.querySelectorAll('[data-add-list-key]').forEach(button => {
        const key = button.dataset.addListKey;
        button.addEventListener('click', () => addListItem(key));
    });
}
