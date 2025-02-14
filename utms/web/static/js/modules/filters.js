export let activeFilters = new Set();

export function initializeFilters() {
    
    // Initialize group click handlers
    document.querySelectorAll('.group-name').forEach(span => {
        span.addEventListener('click', (e) => {
            const group = e.target.dataset.group || e.target.textContent.trim();
            const page = document.body.dataset.page;
            toggleFilter(group, page);
        });
    });

    // Initialize search handlers
    const page = document.body.dataset.page;
    const searchHandler = page === 'units' ? filterUnits : filterAnchors;
    
    document.getElementById('labelSearch')?.addEventListener('input', searchHandler);
    document.getElementById('nameSearch')?.addEventListener('input', searchHandler);
    document.getElementById('clearFiltersBtn')?.addEventListener('click', () => {
        const page = document.body.dataset.page;
        clearFilters(page);
    });

  // Load filters from URL
  loadFiltersFromUrl();
}

function loadFiltersFromUrl() {
    const url = new URL(window.location);
    const filterParam = url.searchParams.get('filters');
    if (filterParam) {
        filterParam.split(',').forEach(filter => {
            if (filter) activeFilters.add(filter);
        });
        updateFilters();
        const page = document.body.dataset.page;
        if (page === 'units') {
            filterUnits();
        } else if (page === 'anchors') {
            filterAnchors();
        }
    }
}

export function toggleFilter(group, type = 'units') {
    
    if (activeFilters.has(group)) {
        activeFilters.delete(group);
    } else {
        activeFilters.add(group);
    }
    
    updateFilters();
    
    if (type === 'units') {
        filterUnits();
    } else if (type === 'anchors') {
        filterAnchors();
    }
}

export function clearFilters(type = 'units') {
    activeFilters.clear();
    updateFilters();
    if (type === 'units') {
        filterUnits();
    } else if (type === 'anchors') {
        filterAnchors();
    }
}

export function updateFilters() {
    const filterContainer = document.getElementById('activeFilters');
    if (!filterContainer) return;
    
    filterContainer.innerHTML = '';
    
    activeFilters.forEach(group => {
        const filterTag = document.createElement('div');
        filterTag.className = 'filter-tag';
        filterTag.innerHTML = `
            ${group}
            <i class="material-icons remove-filter" data-group="${group}">close</i>
        `;
      filterContainer.appendChild(filterTag);

        // Add click handler for the remove button
        const removeBtn = filterTag.querySelector('.remove-filter');
        removeBtn.addEventListener('click', () => {
            const group = removeBtn.dataset.group;
            const page = document.body.dataset.page;
            toggleFilter(group, page);
        });      

    });
  
  // Just handle the clear button state
  const clearBtn = document.querySelector('.btn--clear');
    if (clearBtn) {
        clearBtn.disabled = activeFilters.size === 0;

    }
    
    // Update URL
    const url = new URL(window.location);
    url.searchParams.set('filters', Array.from(activeFilters).join(','));
    window.history.pushState({}, '', url);
}

export function filterUnits() {
  const units = document.querySelectorAll('.unit-card');
    const labelQuery = document.getElementById('labelSearch')?.value.trim().toLowerCase() || '';
    const nameQuery = document.getElementById('nameSearch')?.value.trim().toLowerCase() || '';
    
    units.forEach(unit => {
        const label = unit.querySelector('[data-field="label"]').textContent.trim().toLowerCase();
        const name = unit.querySelector('[data-field="name"]').textContent.trim().toLowerCase();
        const groupTags = unit.querySelectorAll('.groups__name');
        const unitGroups = Array.from(groupTags).map(tag => tag.textContent.trim());
        
      const passesFilters = activeFilters.size === 0 || 
			    Array.from(activeFilters).every(filter => unitGroups.includes(filter));
      
      const passesLabelSearch = !labelQuery || label === labelQuery;
      const passesNameSearch = !nameQuery || name.includes(nameQuery);
        
        unit.style.display = (passesFilters && passesLabelSearch && passesNameSearch) ? '' : 'none';
    });
}

export function filterAnchors() {
    const anchors = document.querySelectorAll('.anchor-card');
    const labelQuery = document.getElementById('labelSearch')?.value.toLowerCase() || '';
    const nameQuery = document.getElementById('nameSearch')?.value.toLowerCase() || '';

    anchors.forEach(card => {
        const label = card.querySelector('[data-field="label"]').textContent.toLowerCase();
        const name = card.querySelector('[data-field="name"]').textContent.toLowerCase();
        const groups = Array.from(card.querySelectorAll('.groups__name')).map(span => span.textContent);

        const matchesLabel = label.includes(labelQuery);
        const matchesName = name.includes(nameQuery);
        const matchesFilters = activeFilters.size === 0 || 
                             Array.from(activeFilters).every(filter => groups.includes(filter));

        card.style.display = (matchesLabel && matchesName && matchesFilters) ? '' : 'none';
    });
}

