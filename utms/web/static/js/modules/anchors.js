import { filterAnchors, toggleFilter } from './filters.js';
import { 
  saveField, 
  saveNumericField, 
  saveTextField, 
  saveAnchorEdit,
  deleteAnchor 
} from '../api/anchorsApi.js';

export function initializeAnchors() {
  console.log('Initializing anchors...');

  // Initialize search and sort
  document.getElementById('labelSearch')?.addEventListener('input', filterAnchors);
  document.getElementById('nameSearch')?.addEventListener('input', filterAnchors);
  document.getElementById('sortSelect')?.addEventListener('change', sortAnchors);

  // Use event delegation for all anchor card controls
  document.addEventListener('click', (e) => {
    if (e.target.closest('.groups__name')) {
      const groupElement = e.target.closest('.groups__name');
      const group = groupElement.dataset.group || groupElement.textContent.trim();
      const page = document.body.dataset.page;
      toggleFilter(group, page);
      return;
    }

    if (e.target.closest('.anchor-card__original-btn')) {
      const button = e.target.closest('.anchor-card__original-btn');
      handleToggleOriginal(button);
      return
    }
    
    const target = e.target.closest('button');
    if (!target) return;

    const card = target.closest('.anchor-card');
    if (!card) return;

    const label = card.dataset.anchor;
    if (!label) return;

    // Handle different button clicks
    switch (target.dataset.action) {
      case 'edit':
        handleAnchorEdit(label);
        break;
      case 'save':
        handleSaveAnchorEdit(label);
        break;
      case 'cancel':
        handleCancelEdit(label);
        break;
      case 'delete':
        if (confirm(`Are you sure you want to delete anchor "${label}"?`)) {
          handleDeleteAnchor(label);
        }
        break;
    }
  });

  // Initialize filters
  loadFiltersFromUrl();

  console.log('Anchors initialization complete');
}

function loadFiltersFromUrl() {
  const url = new URL(window.location);
  const filterParam = url.searchParams.get('filters');
  if (filterParam) {
    filterParam.split(',').forEach(filter => {
      if (filter) toggleFilter(filter, 'anchors');
    });
  }
}

function handleToggleOriginal(button) {
  const container = button.parentElement;
  const codeBlock = container.querySelector('.anchor-card__original-code');
  
  if (codeBlock.style.display === 'block') {
    codeBlock.style.display = 'none';
    button.title = 'Show original expression';
  } else {
    codeBlock.style.display = 'block';
    button.title = 'Hide original expression';
  }
}

export function handleAnchorEdit(label) {
  const card = document.querySelector(`[data-anchor="${label}"]`);
  const editBtn = card.querySelector('.btn--edit');
  const editControls = card.querySelector('.anchor-card__edit-controls');
  const editableFields = card.querySelectorAll('.edit-target');
  
  editableFields.forEach(field => {
    if (field.dataset.field === 'groups') {
      // Store original groups as comma-separated string
      const groups = Array.from(field.querySelectorAll('.groups__name'))
			  .map(span => span.textContent.trim());
      field.dataset.originalValue = groups.join(',');
    } else {
      field.dataset.originalValue = field.textContent.trim();
    }
    if (!field.closest('.has-original')) {  // Don't make original expression fields editable
      field.contentEditable = true;
      field.classList.add('editing');
    }
  });

  // Show group controls
  const groupRemoveButtons = card.querySelectorAll('.groups__remove');
  const addGroupBtn = card.querySelector('.groups__add');
  groupRemoveButtons.forEach(btn => btn.style.display = 'inline-block');
  if (addGroupBtn) addGroupBtn.style.display = 'inline-block';
  
  // Show save/cancel buttons, hide edit button
  editBtn.style.display = 'none';
  editControls.style.display = 'inline-flex';
  initGroupControls(label);
}

async function handleSaveAnchorEdit(label) {
  const card = document.querySelector(`[data-anchor="${label}"]`);
  const updatedData = {
    label: card.querySelector('[data-field="label"]').textContent,
    name: card.querySelector('[data-field="name"]').textContent,
    value: parseFloat(card.querySelector('[data-field="value"]').textContent),
    groups: Array.from(card.querySelectorAll('.groups__name')).map(span => span.textContent)
  };

  try {
    await saveAnchorEdit(label, updatedData);
    exitEditMode(card);
  } catch (error) {
    alert('Failed to update anchor: ' + error.message);
  }
}


export function handleCancelEdit(label) {
  const card = document.querySelector(`[data-anchor="${label}"]`);
  const editBtn = card.querySelector('.btn--edit');
  const editControls = card.querySelector('.anchor-card__edit-controls');
  const editableFields = card.querySelectorAll('.edit-target');
  
  editableFields.forEach(field => {
    if (field.dataset.field === 'groups') {
      // Restore original groups structure
      const originalGroups = field.dataset.originalValue.split(',').filter(g => g.trim());
      field.innerHTML = originalGroups.map(group => `
                <span class="groups__tag">
                    <span class="groups__name">${group.trim()}</span>
                    <i class="groups__remove material-icons">close</i>
                </span>
      `).join('') + `
                <button class="groups__add">
                    <i class="material-icons">add</i>
                </button>
      `;
    } else {
      field.textContent = field.dataset.originalValue;
    }
    field.contentEditable = false;
    field.classList.remove('editing');
  });

  exitEditMode(card);
}

async function handleDeleteAnchor(label) {
  if (confirm(`Are you sure you want to delete the anchor "${label}"?`)) {
    try {
      await deleteAnchor(label);
      const card = document.querySelector(`[data-anchor="${label}"]`);
      card.remove();
    } catch (error) {
      alert('Failed to delete anchor: ' + error.message);
    }
  }
}

async function handleSaveField(anchorLabel, fieldName, button) {
  const container = button.closest('.anchor-card__evaluated-value');
  const input = container.querySelector('.anchor-card__edit-input');
  
  try {
    await saveField(anchorLabel, fieldName, input.value);
    const valueDisplay = container.querySelector('.anchor-card__value');
    valueDisplay.textContent = input.value;
    container.classList.remove('editing');
  } catch (error) {
    alert('Error saving: ' + error.message);
  }
}

function exitEditMode(card) {
  const editControls = card.querySelector('.anchor-card__edit-controls');
  const editBtn = card.querySelector('.btn--edit');
  if (editControls) editControls.style.display = 'none';
  if (editBtn) editBtn.style.display = 'inline-block';

  // Reset contentEditable
  card.querySelectorAll('.edit-target').forEach(field => {
    field.contentEditable = false;
    field.classList.remove('editing');
  });

  // Hide group controls
  const groupRemoveButtons = card.querySelectorAll('.groups__remove');
  const addGroupBtn = card.querySelector('.groups__add');
  groupRemoveButtons.forEach(btn => btn.style.display = 'none');
  if (addGroupBtn) addGroupBtn.style.display = 'none';
}



export function editField(button, anchorLabel, fieldName) {
  const container = button.closest('.anchor-card__evaluated-value');
  const valueDisplay = container.querySelector('.anchor-card__value');
  const currentValue = valueDisplay.textContent.trim();
  
  // Create edit controls if they don't exist
  if (!container.querySelector('.anchor-card__edit-controls')) {
    const editControls = document.createElement('div');
    editControls.className = 'anchor-card__edit-controls';
    editControls.innerHTML = `
      <input type="text" class="anchor-card__edit-input" value="${currentValue}">
            <button class="btn btn--save" onclick="saveField('${anchorLabel}', '${fieldName}', this)">
                <i class="material-icons">check</i>
            </button>
            <button class="btn btn--cancel" onclick="cancelEdit(this)">
                <i class="material-icons">close</i>
            </button>
    `;
    const saveBtn = editControls.querySelector('.btn--save');
    saveBtn.addEventListener('click', () => handleSaveField(anchorLabel, fieldName, saveBtn));

    const cancelBtn = editControls.querySelector('.btn--cancel');
    cancelBtn.addEventListener('click', () => handleCancelEdit(anchorLabel));

    container.appendChild(editControls);
    }
    
    container.classList.add('editing');
}

export function cancelEdit(button) {
    const container = button.closest('.anchor-card__evaluated-value');
    container.classList.remove('editing');
}


export function editNumericField(button, anchorLabel, fieldName) {
    const container = button.closest('.anchor-card__evaluated-value');
    const valueDisplay = container.querySelector('.anchor-card__value');
    const currentValue = valueDisplay.textContent.trim();
    
    // Create edit controls if they don't exist
    if (!container.querySelector('.anchor-card__edit-controls')) {
        const editControls = document.createElement('div');
        editControls.className = 'anchor-card__edit-controls';
        editControls.innerHTML = `
            <input type="number" 
                   class="anchor-card__edit-input" 
                   value="${currentValue}"
                   step="any">
            <button class="btn btn--save" onclick="saveNumericField('${anchorLabel}', '${fieldName}', this)">
                <i class="material-icons">check</i>
            </button>
            <button class="btn btn--cancel" onclick="cancelEdit(this)">
                <i class="material-icons">close</i>
            </button>
        `;
    const saveBtn = editControls.querySelector('.btn--save');
    saveBtn.addEventListener('click', () => handleSaveField(anchorLabel, fieldName, saveBtn));

    const cancelBtn = editControls.querySelector('.btn--cancel');
      cancelBtn.addEventListener('click', () => handleCancelEdit(anchorLabel));

      container.appendChild(editControls);
    }
    
    container.classList.add('editing');
}


export function editTextField(button, anchorLabel, fieldName) {
    const container = button.closest('.anchor-card__evaluated-value');
    const valueDisplay = container.querySelector('.anchor-card__value');
    const currentValue = valueDisplay.textContent.trim();
    
    // Create edit controls if they don't exist
    if (!container.querySelector('.anchor-card__edit-controls')) {
        const editControls = document.createElement('div');
        editControls.className = 'anchor-card__edit-controls';
        editControls.innerHTML = `
            <input type="text" 
                   class="anchor-card__edit-input" 
                   value="${currentValue}">
            <button class="btn btn--save" onclick="saveTextField('${anchorLabel}', '${fieldName}', this)">
                <i class="material-icons">check</i>
            </button>
            <button class="btn btn--cancel" onclick="cancelEdit(this)">
                <i class="material-icons">close</i>
            </button>
        `;
    const saveBtn = editControls.querySelector('.btn--save');
    saveBtn.addEventListener('click', () => handleSaveField(anchorLabel, fieldName, saveBtn));

    const cancelBtn = editControls.querySelector('.btn--cancel');
      cancelBtn.addEventListener('click', () => handleCancelEdit(anchorLabel));

      container.appendChild(editControls);
    }
    
    container.classList.add('editing');
}



function addNewGroup(label) {
  const groupName = prompt("Enter new group name:");
    if (!groupName) return;
    
    const card = document.querySelector(`[data-anchor="${label}"]`);
    const groupsContainer = card.querySelector('.groups');
    const addButton = groupsContainer.querySelector('.groups__add');
    
    const newGroupTag = document.createElement('span');
    newGroupTag.className = 'groups__tag';
    newGroupTag.innerHTML = `
        <span class="groups__name">${groupName}</span>
        <i class="groups__remove material-icons">close</i>
    `;
    
    groupsContainer.insertBefore(newGroupTag, addButton);
    
    // Add click handler to the new remove button
    const removeBtn = newGroupTag.querySelector('.groups__remove');
    removeBtn.onclick = () => newGroupTag.remove();
}

function initGroupControls(label) {
    const card = document.querySelector(`[data-anchor="${label}"]`);
    const addGroupBtn = card.querySelector('.groups__add');
    const removeButtons = card.querySelectorAll('.groups__remove');
    
    addGroupBtn.onclick = () => addNewGroup(label);
    removeButtons.forEach(btn => {
        btn.onclick = () => btn.closest('.groups__tag').remove();
    });
}


function sortAnchors() {
    const sortSelect = document.getElementById('sortSelect');
    const anchorsGrid = document.getElementById('anchorsGrid');
    if (!sortSelect || !anchorsGrid) return;

    const [field, direction] = sortSelect.value.split('-');
    const cards = Array.from(anchorsGrid.getElementsByClassName('anchor-card'));

    cards.sort((a, b) => {
        let aValue, bValue;
        
        const aElement = a.querySelector(`[data-field="${field}"]`);
        const bElement = b.querySelector(`[data-field="${field}"]`);
        
        if (!aElement || !bElement) return 0;

        if (field === 'value') {
            aValue = parseFloat(aElement.textContent) || 0;
            bValue = parseFloat(bElement.textContent) || 0;
        } else {
            aValue = aElement.textContent.trim().toLowerCase();
            bValue = bElement.textContent.trim().toLowerCase();
        }

        if (direction === 'asc') {
            return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
        } else {
            return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
        }
    });

    // Clear and rebuild the grid
    while (anchorsGrid.firstChild) {
        anchorsGrid.removeChild(anchorsGrid.firstChild);
    }
    cards.forEach(card => anchorsGrid.appendChild(card));
}



