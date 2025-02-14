import { formatScientific } from './utils.js';
import { filterVariables, toggleFilter } from './filters.js';

function initializeModal() {
    const modal = document.getElementById('createVariableModal');
    if (!modal) return;

    // Close button (X)
    const closeBtn = document.getElementById('closeModalX');
    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            modal.style.display = 'none';
            document.getElementById('createVariableForm')?.reset();
        });
    }
    
    // Form submission
    document.getElementById('createVariableForm')?.addEventListener('submit', handleCreateVariable);

    // Close on click outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            document.getElementById('createVariableForm')?.reset();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
            document.getElementById('createVariableForm')?.reset();
        }
    });
}

export function initializeVariables() {
    console.log('Initializing variables...');

    // Initialize modal
    initializeModal();

    // Initialize search listeners
    document.getElementById('nameSearch')?.addEventListener('input', filterVariables);
    document.getElementById('descriptionSearch')?.addEventListener('input', filterVariables);

    // Use event delegation for all variable card controls
    document.addEventListener('click', (e) => {
        const target = e.target.closest('button');
        if (!target) return;

        // Handle toggle original button
        if (target.classList.contains('toggle-original-btn')) {
            toggleOriginal(target);
            return;
        }

        const card = target.closest('.variable-card');
        if (!card) return;

        const name = card.dataset.variable;
        if (!name) return;

        // Handle different button clicks
        switch (target.dataset.action) {
            case 'edit':
                toggleVariableEdit(name);
                break;
            case 'save':
                saveVariableEdit(name);
                break;
            case 'cancel':
                cancelVariableEdit(name);
                break;
            case 'delete':
                if (confirm(`Are you sure you want to delete variable "${name}"?`)) {
                    deleteVariable(name);
                }
                break;
        }
    });

    // Initialize sort functionality
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', sortVariables);
    }

    // Load filters from URL if any
    loadFiltersFromUrl();

    console.log('Variables initialization complete');
}

