async function saveConfig(key) {
    const value = document.getElementById(key).value;
    try {
        const response = await fetch(`/api/config/${key}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(value)
        });
        if (!response.ok) {
            throw new Error('Failed to save configuration');
        }
        alert('Configuration saved successfully');
    } catch (error) {
        alert('Error saving configuration: ' + error.message);
    }
}

async function saveListItem(key, index) {
    const value = document.getElementById(`${key}_${index}`).value;
    try {
        const response = await fetch(`/api/config/${key}/${index}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(value)
        });
        if (!response.ok) {
            throw new Error('Failed to save list item');
        }
        alert('List item saved successfully');
    } catch (error) {
        alert('Error saving list item: ' + error.message);
    }
}

async function addListItem(key) {
    try {
        const response = await fetch(`/api/config/${key}/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify('')  // Default empty value
        });
        if (!response.ok) {
            throw new Error('Failed to add list item');
        }
        location.reload();  // Refresh to show new item
    } catch (error) {
        alert('Error adding list item: ' + error.message);
    }
}

// static/script.js (add to existing file)

let activeFilters = new Set();

function toggleFilter(group) {
    if (activeFilters.has(group)) {
        activeFilters.delete(group);
    } else {
        activeFilters.add(group);
    }
  updateFilters();

  filterUnits();
}

function clearFilters() {
    activeFilters.clear();
    updateFilters();
    filterUnits();
}

function updateFilters() {
    const filterContainer = document.getElementById('activeFilters');
    filterContainer.innerHTML = '';
    
    activeFilters.forEach(group => {
        const filterTag = document.createElement('div');
        filterTag.className = 'filter-tag';
        filterTag.innerHTML = `
            ${group}
            <i class="material-icons" onclick="toggleFilter('${group}')">close</i>
        `;
        filterContainer.appendChild(filterTag);
    });
    
    // Update URL to reflect current filters
    const url = new URL(window.location);
    url.searchParams.set('filters', Array.from(activeFilters).join(','));
    window.history.pushState({}, '', url);
}

function filterUnits() {
    const units = document.querySelectorAll('.unit-card');
    const labelQuery = document.getElementById('labelSearch').value.trim().toLowerCase();
    const nameQuery = document.getElementById('nameSearch').value.trim().toLowerCase();
    
    units.forEach(unit => {
        const label = unit.querySelector('[data-field="label"]').textContent.trim().toLowerCase();
        const name = unit.querySelector('[data-field="name"]').textContent.trim().toLowerCase();
        
        // Check active filters
        const groupTags = unit.querySelectorAll('.group-name');
        const unitGroups = Array.from(groupTags).map(tag => tag.textContent.trim());
        const passesFilters = activeFilters.size === 0 || 
            Array.from(activeFilters).every(filter => unitGroups.includes(filter));
        
        // Check searches
        const passesLabelSearch = !labelQuery || label === labelQuery;
        const passesNameSearch = !nameQuery || name.includes(nameQuery);
        
        // Show unit only if it passes all conditions
        const shouldShow = passesFilters && passesLabelSearch && passesNameSearch;
        unit.style.display = shouldShow ? '' : 'none';
    });
}

// Add event listeners for search inputs
document.getElementById('labelSearch').addEventListener('input', filterUnits);
document.getElementById('nameSearch').addEventListener('input', filterUnits);

// Initialize filters from URL if any
window.addEventListener('load', () => {
  const url = new URL(window.location);
    const filterParam = url.searchParams.get('filters');
    if (filterParam) {
        filterParam.split(',').forEach(filter => {
            if (filter) activeFilters.add(filter);
        });
        updateFilters();
        filterUnits();
    }
});

function toggleOriginal(button) {
    const container = button.parentElement;
    const codeBlock = container.querySelector('.original-code');
    
    if (codeBlock.style.display === 'block') {
        codeBlock.style.display = 'none';
        button.title = 'Show original expression';
    } else {
        codeBlock.style.display = 'block';
        button.title = 'Hide original expression';
    }
}

function editField(button, anchorLabel, fieldName) {
    const container = button.closest('.evaluated-value');
    const valueDisplay = container.querySelector('.value-display');
    const currentValue = valueDisplay.textContent.trim();
    
    // Create edit controls if they don't exist
    if (!container.querySelector('.edit-controls')) {
        const editControls = document.createElement('div');
        editControls.className = 'edit-controls';
        editControls.innerHTML = `
            <input type="text" class="edit-input" value="${currentValue}">
            <button class="btn-save" onclick="saveField('${anchorLabel}', '${fieldName}', this)">
                <i class="material-icons">check</i>
            </button>
            <button class="btn-cancel" onclick="cancelEdit(this)">
                <i class="material-icons">close</i>
            </button>
        `;
        container.appendChild(editControls);
    }
    
    container.classList.add('editing');
}

function cancelEdit(button) {
    const container = button.closest('.evaluated-value');
    container.classList.remove('editing');
}

async function saveField(anchorLabel, fieldName, button) {
    const container = button.closest('.evaluated-value');
    const input = container.querySelector('.edit-input');
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
        const valueDisplay = container.querySelector('.value-display');
        valueDisplay.textContent = newValue;
        container.classList.remove('editing');
        
    } catch (error) {
        alert('Error saving: ' + error.message);
    }
}

function editNumericField(button, anchorLabel, fieldName) {
    const container = button.closest('.evaluated-value');
    const valueDisplay = container.querySelector('.value-display');
    const currentValue = valueDisplay.textContent.trim();
    
    // Create edit controls if they don't exist
    if (!container.querySelector('.edit-controls')) {
        const editControls = document.createElement('div');
        editControls.className = 'edit-controls';
        editControls.innerHTML = `
            <input type="number" 
                   class="edit-input" 
                   value="${currentValue}"
                   step="any">  <!-- allows decimal numbers -->
            <button class="btn-save" onclick="saveNumericField('${anchorLabel}', '${fieldName}', this)">
                <i class="material-icons">check</i>
            </button>
            <button class="btn-cancel" onclick="cancelEdit(this)">
                <i class="material-icons">close</i>
            </button>
        `;
        container.appendChild(editControls);
    }
    
    container.classList.add('editing');
}

async function saveNumericField(anchorLabel, fieldName, button) {
    const container = button.closest('.evaluated-value');
    const input = container.querySelector('.edit-input');
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
        const valueDisplay = container.querySelector('.value-display');
        valueDisplay.textContent = newValue;
        container.classList.remove('editing');
        
        // Refresh the page to get updated data
        location.reload();
        
    } catch (error) {
        alert('Error saving: ' + error.message);
    }
}

function editTextField(button, anchorLabel, fieldName) {
    const container = button.closest('.evaluated-value');
    const valueDisplay = container.querySelector('.value-display');
    const currentValue = valueDisplay.textContent.trim();
    
    // Create edit controls if they don't exist
    if (!container.querySelector('.edit-controls')) {
        const editControls = document.createElement('div');
        editControls.className = 'edit-controls';
        editControls.innerHTML = `
            <input type="text" 
                   class="edit-input" 
                   value="${currentValue}">
            <button class="btn-save" onclick="saveTextField('${anchorLabel}', '${fieldName}', this)">
                <i class="material-icons">check</i>
            </button>
            <button class="btn-cancel" onclick="cancelEdit(this)">
                <i class="material-icons">close</i>
            </button>
        `;
        container.appendChild(editControls);
    }
    
    container.classList.add('editing');
}


async function saveTextField(anchorLabel, fieldName, button) {
  const container = button.closest('.evaluated-value');
    const input = container.querySelector('.edit-input');
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
        const valueDisplay = container.querySelector('.value-display');
        valueDisplay.textContent = newValue;
        container.classList.remove('editing');
        
        // Refresh the page to get updated data
        location.reload();
        
    } catch (error) {
        alert('Error saving: ' + error.message);
    }
}


async function saveAnchorEdit(label) {
    const card = document.querySelector(`[data-anchor="${label}"]`);
    
    // Save name
    const nameField = card.querySelector('[data-field="name"]');
    await fetch(`/api/anchors/${label}/name`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: nameField.textContent.trim() })
    });

    // Save value
    const valueField = card.querySelector('[data-field="value"]');
    await fetch(`/api/anchors/${label}/value`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: valueField.textContent.trim() })
    });

    // Save groups
    const groupsContainer = card.querySelector('[data-field="groups"]');
    const groups = Array.from(groupsContainer.querySelectorAll('.group-name'))
        .map(span => span.textContent.trim());
    await fetch(`/api/anchors/${label}/groups`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: groups })
    });

    // Reset UI
    const editBtn = card.querySelector('.anchor-edit-btn');
    const editControls = card.querySelector('.edit-controls');
    const editableFields = card.querySelectorAll('.edit-target');
    const groupRemoveButtons = card.querySelectorAll('.group-remove');
    const addGroupBtn = card.querySelector('.add-group-btn');
    
    // Disable editing
    editableFields.forEach(field => {
        field.contentEditable = false;
    });
    
    // Hide group controls
    groupRemoveButtons.forEach(btn => btn.style.display = 'none');
    if (addGroupBtn) addGroupBtn.style.display = 'none';
    
    // Show edit button, hide save/cancel buttons
    editBtn.style.display = 'inline-block';
    editControls.style.display = 'none';
}

function addNewGroup(label) {
  const groupName = prompt("Enter new group name:");
    if (!groupName) return;
    
    const card = document.querySelector(`[data-anchor="${label}"]`);
    const groupsContainer = card.querySelector('.groups');
    const addButton = groupsContainer.querySelector('.add-group-btn');
    
    const newGroupTag = document.createElement('span');
    newGroupTag.className = 'group-tag';
    newGroupTag.innerHTML = `
        <span class="group-name">${groupName}</span>
        <i class="material-icons group-remove" style="display: inline-block;">close</i>
    `;
    
    groupsContainer.insertBefore(newGroupTag, addButton);
    
    // Add click handler to the new remove button
    const removeBtn = newGroupTag.querySelector('.group-remove');
    removeBtn.onclick = () => newGroupTag.remove();
}

function initGroupControls(label) {
    const card = document.querySelector(`[data-anchor="${label}"]`);
    const addGroupBtn = card.querySelector('.add-group-btn');
    const removeButtons = card.querySelectorAll('.group-remove');
    
    addGroupBtn.onclick = () => addNewGroup(label);
    removeButtons.forEach(btn => {
        btn.onclick = () => btn.closest('.group-tag').remove();
    });
}

function cancelAnchorEdit(label) {
    const card = document.querySelector(`[data-anchor="${label}"]`);
    const editBtn = card.querySelector('.anchor-edit-btn');
    const editControls = card.querySelector('.edit-controls');
    const editableFields = card.querySelectorAll('.edit-target');
    
    editableFields.forEach(field => {
        if (field.dataset.field === 'groups') {
            // Restore original groups structure
            const originalGroups = field.dataset.originalValue.split(',').filter(g => g.trim());
            field.innerHTML = originalGroups.map(group => `
                <span class="group-tag">
                    <span class="group-name">${group.trim()}</span>
                    <i class="material-icons group-remove" style="display: none;">close</i>
                </span>
            `).join('') + `
                <button class="add-group-btn" style="display: none;">
                    <i class="material-icons">add</i>
                </button>
            `;
        } else {
            // Handle other fields normally
            field.textContent = field.dataset.originalValue;
        }
        field.contentEditable = false;
    });
    
    // Show edit button, hide save/cancel buttons
    editBtn.style.display = 'inline-block';
    editControls.style.display = 'none';
}

function toggleAnchorEdit(label) {
    const card = document.querySelector(`[data-anchor="${label}"]`);
    const editBtn = card.querySelector('.anchor-edit-btn');
    const editControls = card.querySelector('.edit-controls');
    const editableFields = card.querySelectorAll('.edit-target');
    
    editableFields.forEach(field => {
        if (field.dataset.field === 'groups') {
            // Store original groups as comma-separated string
            const groups = Array.from(field.querySelectorAll('.group-name'))
                .map(span => span.textContent.trim());
            field.dataset.originalValue = groups.join(',');
        } else {
            field.dataset.originalValue = field.textContent.trim();
        }
        field.contentEditable = true;
    });
    
    // Show group controls
    const groupRemoveButtons = card.querySelectorAll('.group-remove');
    const addGroupBtn = card.querySelector('.add-group-btn');
    groupRemoveButtons.forEach(btn => btn.style.display = 'inline-block');
    if (addGroupBtn) addGroupBtn.style.display = 'inline-block';
    
    // Show save/cancel buttons, hide edit button
    editBtn.style.display = 'none';
    editControls.style.display = 'inline-flex';
    
    initGroupControls(label);
}

function sortUnits() {
    const unitsGrid = document.getElementById('unitsGrid');
    const units = Array.from(unitsGrid.querySelectorAll('.unit-card'));
    const sortType = document.getElementById('sortSelect').value;

    units.sort((a, b) => {
        switch(sortType) {
            case 'value-asc':
                const valueA = new Decimal(a.querySelector('[data-field="value"]').dataset.fullValue);
                const valueB = new Decimal(b.querySelector('[data-field="value"]').dataset.fullValue);
                return valueA.minus(valueB).toNumber();
            case 'value-desc':
                const valueADesc = new Decimal(a.querySelector('[data-field="value"]').dataset.fullValue);
                const valueBDesc = new Decimal(b.querySelector('[data-field="value"]').dataset.fullValue);
                return valueBDesc.minus(valueADesc).toNumber();
            case 'label-asc':
                return a.querySelector('h3').textContent.localeCompare(
                       b.querySelector('h3').textContent);
            case 'label-desc':
                return b.querySelector('h3').textContent.localeCompare(
                       a.querySelector('h3').textContent);
        }
    });

    units.forEach(unit => unitsGrid.appendChild(unit));
}


function toggleUnitEdit(label) {
    const card = document.querySelector(`[data-unit="${label}"]`);
    const editBtn = card.querySelector('.unit-edit-btn');
    const editControls = card.querySelector('.edit-controls');
    const editableFields = card.querySelectorAll('.edit-target');
    
    editableFields.forEach(field => {
        if (field.dataset.field === 'groups') {
            // Store original groups as comma-separated string
            const groups = Array.from(field.querySelectorAll('.group-name'))
                .map(span => span.textContent.trim());
            field.dataset.originalValue = groups.join(',');
        } else if (field.dataset.field === 'value') {
          // Store both the formatted display and the full value
          field.dataset.originalDisplay = field.textContent.trim();
          // Show the full value for editing
          field.textContent = field.dataset.fullValue;

        } else {
          field.dataset.originalValue = field.textContent.trim();
        }
        field.contentEditable = true;
    });

    // Show group controls
    const groupRemoveButtons = card.querySelectorAll('.group-remove');
    const addGroupBtn = card.querySelector('.add-group-btn');
    groupRemoveButtons.forEach(btn => btn.style.display = 'inline-block');
    if (addGroupBtn) addGroupBtn.style.display = 'inline-block';
    
    // Show save/cancel buttons, hide edit button
    editBtn.style.display = 'none';
    editControls.style.display = 'inline-flex';
    
    initUnitGroupControls(label);
}


function cancelUnitEdit(label) {
    const card = document.querySelector(`[data-unit="${label}"]`);
    const editBtn = card.querySelector('.unit-edit-btn');
    const editControls = card.querySelector('.edit-controls');
    const editableFields = card.querySelectorAll('.edit-target');
    
    editableFields.forEach(field => {
        if (field.dataset.field === 'groups') {
            // Restore original groups structure
            const originalGroups = field.dataset.originalValue.split(',').filter(g => g.trim());
            field.innerHTML = originalGroups.map(group => `
                <span class="group-tag">
                    <span class="group-name">${group.trim()}</span>
                    <i class="material-icons group-remove" style="display: none;">close</i>
                </span>
            `).join('') + `
                <button class="add-group-btn" style="display: none;">
                    <i class="material-icons">add</i>
                </button>
            `;
        } else if (field.dataset.field === 'value') {
            // Restore the original formatted display
            field.textContent = field.dataset.originalDisplay;
        } else {
            field.textContent = field.dataset.originalValue;
        }
        field.contentEditable = false;
    });

    // Show edit button, hide save/cancel buttons
    editBtn.style.display = 'inline-block';
    editControls.style.display = 'none';
}


async function saveUnitEdit(label) {
  const card = document.querySelector(`[data-unit="${label}"]`);
    
    // Save label first as it might change
    const labelField = card.querySelector('[data-field="label"]');
    const newLabel = labelField.textContent.trim();
    if (newLabel !== label) {
        await fetch(`/api/units/${label}/label`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: newLabel })
        });
        // Update the data-unit attribute to match the new label
        card.setAttribute('data-unit', newLabel);

        // Update the edit button's onclick handler
        const editBtn = card.querySelector('.unit-edit-btn');
        editBtn.setAttribute('onclick', `toggleUnitEdit('${newLabel}')`);
        
        // Update the save/cancel buttons
        const saveBtn = card.querySelector('.btn-save');
        const cancelBtn = card.querySelector('.btn-cancel');
        saveBtn.setAttribute('onclick', `saveUnitEdit('${newLabel}')`);
      cancelBtn.setAttribute('onclick', `cancelUnitEdit('${newLabel}')`);

      label = newLabel; // Use new label for subsequent updates
    }

  // Save name
  const nameField = card.querySelector('[data-field="name"]');
    await fetch(`/api/units/${label}/name`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: nameField.textContent.trim() })
    });

    // Save value
  const valueField = card.querySelector('[data-field="value"]');
  const newValue = valueField.textContent.trim()
    await fetch(`/api/units/${label}/value`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: newValue })
    });
  valueField.dataset.fullValue = newValue;
  valueField.textContent = format_scientific(newValue, 20);

    // Save groups
    const groupsContainer = card.querySelector('[data-field="groups"]');
    const groups = Array.from(groupsContainer.querySelectorAll('.group-name'))
        .map(span => span.textContent.trim());
    await fetch(`/api/units/${label}/groups`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: groups })
    });

    // Reset UI
    const editBtn = card.querySelector('.unit-edit-btn');
    const editControls = card.querySelector('.edit-controls');
    const editableFields = card.querySelectorAll('.edit-target');
    const groupRemoveButtons = card.querySelectorAll('.group-remove');
    const addGroupBtn = card.querySelector('.add-group-btn');
    
    // Disable editing
    editableFields.forEach(field => {
        field.contentEditable = false;
    });
    
    // Hide group controls
    groupRemoveButtons.forEach(btn => btn.style.display = 'none');
    if (addGroupBtn) addGroupBtn.style.display = 'none';
    
    // Show edit button, hide save/cancel buttons
    editBtn.style.display = 'inline-block';
    editControls.style.display = 'none';
}

function initUnitGroupControls(label) {
  const card = document.querySelector(`[data-unit="${label}"]`);
    const addGroupBtn = card.querySelector('.add-group-btn');
    const removeButtons = card.querySelectorAll('.group-remove');
    
    addGroupBtn.onclick = () => addNewUnitGroup(label);
    removeButtons.forEach(btn => {
        btn.onclick = () => btn.closest('.group-tag').remove();
    });
}

function addNewUnitGroup(label) {
    const groupName = prompt("Enter new group name:");
    if (!groupName) return;
    
    const card = document.querySelector(`[data-unit="${label}"]`);
    const groupsContainer = card.querySelector('.groups');
    const addButton = groupsContainer.querySelector('.add-group-btn');
    
    const newGroupTag = document.createElement('span');
    newGroupTag.className = 'group-tag';
    newGroupTag.innerHTML = `
        <span class="group-name">${groupName}</span>
        <i class="material-icons group-remove" style="display: inline-block;">close</i>
    `;
    
    groupsContainer.insertBefore(newGroupTag, addButton);
    
    // Add click handler to the new remove button
    const removeBtn = newGroupTag.querySelector('.group-remove');
    removeBtn.onclick = () => newGroupTag.remove();
}

function format_scientific(num, max_digits) {
    const str = String(num);
    if (str.includes('E')) {
        const [mantissa, exponent] = str.split('E');
        if (mantissa.length > max_digits) {
            return mantissa.substring(0, max_digits) + '...' + 'E' + exponent;
        }
    } else {
        if (str.length > max_digits) {
            return str.substring(0, max_digits) + '...';
        }
    }
    return str;
}
