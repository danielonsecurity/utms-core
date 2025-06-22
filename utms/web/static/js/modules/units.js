import { formatScientific } from './utils.js';
import { createUnit, updateUnit, deleteUnit } from '../api/unitsApi.js';
import { filterUnits, toggleFilter } from './filters.js';

function initializeModal() {
  const modal = document.getElementById('createUnitModal');
  if (!modal) return;

  // Close button (X)
  const closeBtn = document.getElementById('closeModalX');

  if (closeBtn) {
    closeBtn.addEventListener('click', (e) => {
      console.log('X button clicked'); // Debug log
      e.preventDefault();
      e.stopPropagation(); // Stop event from bubbling
      modal.style.display = 'none';
      document.getElementById('createUnitForm')?.reset();
    });
  }

  // Form submission
  document.getElementById('createUnitForm')?.addEventListener('submit', handleCreateUnit);

  // Close on click outside
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeCreateUnitModal();
    }
  });

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.style.display === 'block') {
      closeCreateUnitModal();
    }
  });
}

export function initializeUnits() {
  console.log('Initializing units...');
  initializeModal();
  // Initialize search and sort
  document.getElementById('labelSearch')?.addEventListener('input', filterUnits);
  document.getElementById('nameSearch')?.addEventListener('input', filterUnits);
  document.getElementById('sortSelect')?.addEventListener('change', sortUnits);

  // Use event delegation for all unit card controls
  document.addEventListener('click', (e) => {
    if (e.target.closest('.groups__name')) {
      const groupElement = e.target.closest('.groups__name');
      const group = groupElement.dataset.group || groupElement.textContent.trim();
      const page = document.body.dataset.page;
      toggleFilter(group, page);
      return;
    }
    const target = e.target.closest('button');
    if (!target) return;

    const card = target.closest('.unit-card');
    if (!card) return;

    const label = card.dataset.unit;
    if (!label) return;

    // Handle different button clicks
    switch (target.dataset.action) {
      case 'edit':
        toggleUnitEdit(label);
        break;
      case 'save':
        saveUnitEdit(label);
        break;
      case 'cancel':
        cancelUnitEdit(label);
        break;
      case 'delete':
        if (confirm(`Are you sure you want to delete unit "${label}"?`)) {
          deleteUnit(label);
        }
        break;
    }
  });

  // Initialize modal functionality
  const modal = document.getElementById('createUnitModal');
  if (modal) {
    // Create unit button
    document.getElementById('createUnitBtn')?.addEventListener('click', showCreateUnitModal);
    
    // Close modal button
    document.getElementById('closeModalBtn')?.addEventListener('click', closeCreateUnitModal);
    
    // Modal form submission
    document.getElementById('createUnitForm')?.addEventListener('submit', handleCreateUnit);
    
    // Close on click outside
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeCreateUnitModal();
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.style.display === 'block') {
        closeCreateUnitModal();
      }
    });
  }

  // Initialize filters
  loadFiltersFromUrl();

  console.log('Units initialization complete');
}

function loadFiltersFromUrl() {
  const url = new URL(window.location);
  const filterParam = url.searchParams.get('filters');
  if (filterParam) {
    filterParam.split(',').forEach(filter => {
      if (filter) toggleFilter(filter, 'units');
    });
  }
}

async function handleCreateUnit(event) {
  event.preventDefault();
  
  const data = {
    label: document.getElementById('newUnitLabel').value,
    name: document.getElementById('newUnitName').value,
    value: document.getElementById('newUnitValue').value,
    groups: document.getElementById('newUnitGroups').value
		    .split(',')
		    .map(g => g.trim())
		    .filter(g => g)
  };

  try {
    await createUnit(data);
    closeCreateUnitModal();
    window.location.reload();
  } catch (error) {
    console.error('Failed to create unit:', error);
    alert('Failed to create unit: ' + error.message);
  }
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


export function toggleUnitEdit(label) {
  const card = document.querySelector(`[data-unit="${label}"]`);
  const editBtn = card.querySelector('.btn--edit');
  const editControls = card.querySelector('.unit-card__edit-controls');
  const editableFields = card.querySelectorAll('.edit-target');
  
  editableFields.forEach(field => {
    if (field.dataset.field === 'groups') {
      // Store original groups as comma-separated string
      const groups = Array.from(field.querySelectorAll('.groups__name'))
			  .map(span => span.textContent.trim());
      field.dataset.originalValue = groups.join(',');
      field.classList.add('editing');
    } else if (field.dataset.field === 'value') {
      // Store both the formatted display and the full value
      field.dataset.originalDisplay = field.textContent.trim();
      // Show the full value for editing
      field.textContent = field.dataset.fullValue;

    } else {
      field.dataset.originalValue = field.textContent.trim();
    }
    field.contentEditable = true;
    field.classList.add('editing');
  });

  // Show save/cancel buttons, hide edit button
  editBtn.classList.add('hidden');
  editControls.classList.add('visible');
  initUnitGroupControls(label);
}

export function cancelUnitEdit(label) {
  const card = document.querySelector(`[data-unit="${label}"]`);
  const editBtn = card.querySelector('.btn--edit');
  const editControls = card.querySelector('.unit-card__edit-controls');
  const editableFields = card.querySelectorAll('.edit-target');
  
  editableFields.forEach(field => {
    if (field.dataset.field === 'groups') {
      // Restore original groups structure
      const originalGroups = field.dataset.originalValue.split(',').filter(g => g.trim());
      field.innerHTML = originalGroups.map(group => `
                <span class="groups__tag">
                    <span class="groups__name" data-group="${group.trim()}">${group.trim()}</span>
                    <i class="material-icons groups__remove">close</i>
                </span>
      `).join('') + `
                <button class="groups__add">
                    <i class="material-icons">add</i>
                </button>
      `;
      field.classList.remove('editing');
      initUnitGroupControls(label);
    } else if (field.dataset.field === 'value') {
      // Restore the original formatted display
      field.textContent = field.dataset.originalDisplay;
    } else {
      field.textContent = field.dataset.originalValue;
    }
    field.contentEditable = false;
    field.classList.remove('editing');
  });

  // Show edit button, hide save/cancel buttons
  editBtn.classList.remove('hidden');
  editControls.classList.remove('visible');
}


export async function saveUnitEdit(label) {
    const card = document.querySelector(`[data-unit="${label}"]`);
    
    try {
        // Save label first as it might change
        const newLabel = card.querySelector('[data-field="label"]').textContent.trim();
        if (newLabel !== label) {
            await updateUnit(label, 'label', newLabel);
            card.dataset.unit = newLabel;
            label = newLabel;
        }

        // Save other fields
        await updateUnit(label, 'name', card.querySelector('[data-field="name"]').textContent.trim());
        
        const newValue = card.querySelector('[data-field="value"]').textContent.trim();
        await updateUnit(label, 'value', newValue);
        
        const groups = Array.from(card.querySelectorAll('.groups__name'))
            .map(span => span.textContent.trim());
        await updateUnit(label, 'groups', groups);

        // Update display
        const valueField = card.querySelector('[data-field="value"]');
        valueField.dataset.fullValue = newValue;
        valueField.textContent = formatScientific(newValue, 20);

        // Reset UI
        exitEditMode(card);
    } catch (error) {
        console.error('Failed to save unit:', error);
        alert('Failed to save changes: ' + error.message);
    }
}

function exitEditMode(card) {
    const editControls = card.querySelector('.unit-card__edit-controls');
    const editBtn = card.querySelector('.btn--edit');
    
    if (editControls) editControls.classList.remove('visible');
    if (editBtn) editBtn.classList.remove('hidden');

    // Reset contentEditable
    card.querySelectorAll('.edit-target').forEach(field => {
        field.contentEditable = false;
        field.classList.remove('editing');  // Add this class for edit state styling
    });

    // Hide group controls
    const groupRemoveButtons = card.querySelectorAll('.unit-card__group-remove');
    const addGroupBtn = card.querySelector('.unit-card__group-add');
    
    groupRemoveButtons.forEach(btn => btn.classList.remove('visible'));
    if (addGroupBtn) addGroupBtn.classList.remove('visible');
}

function initUnitGroupControls(label) {
    const card = document.querySelector(`[data-unit="${label}"]`);
    if (!card) return;

    const groupsContainer = card.querySelector('.groups');
    if (!groupsContainer) return;

    const addGroupBtn = groupsContainer.querySelector('.groups__add');
  if (addGroupBtn) {
    addGroupBtn.style.display = groupsContainer.classList.contains('editing') ? 'block' : 'none';
        addGroupBtn.onclick = () => addNewUnitGroup(label);
    }
  const removeButtons = groupsContainer.querySelectorAll('.groups__remove');

  removeButtons.forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const groupTag = btn.closest('.groups__tag');
      if (groupTag) groupTag.remove();
    }
  });

    // Initialize group name click handlers for filtering
    const groupNames = groupsContainer.querySelectorAll('.groups__name');
    groupNames.forEach(name => {
        name.onclick = (e) => {
            // Only allow filtering when not in edit mode
            if (!groupsContainer.classList.contains('editing')) {
                const group = e.target.dataset.group || e.target.textContent.trim();
                const page = document.body.dataset.page;
                toggleFilter(group, page);
            }
        };
    });


}

function addNewUnitGroup(label) {
  const groupName = prompt("Enter new group name:");
  if (!groupName?.trim()) return;
  
  const card = document.querySelector(`[data-unit="${label}"]`);
  const groupsContainer = card.querySelector('.groups');
  const addButton = groupsContainer.querySelector('.groups__add');
  
  const newGroupTag = document.createElement('span');
  newGroupTag.className = 'groups__tag';
  newGroupTag.innerHTML = `
    <span class="groups__name" data-group="${groupName.trim()}">${groupName.trim()}</span>
    <i class="material-icons groups__remove">close</i>
  `;
  
  groupsContainer.insertBefore(newGroupTag, addButton);
  initUnitGroupControls(label);
}


export function showCreateUnitModal() {
  document.getElementById('createUnitModal').style.display = 'block';
}

export function closeCreateUnitModal() {
    const modal = document.getElementById('createUnitModal');
    if (modal) {
        modal.style.display = 'none';
        // Clear form
        document.getElementById('createUnitForm')?.reset();
    }
}
