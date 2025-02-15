export function initializeResolve() {
  console.log('Initializing resolve...');

  const resolveBtn = document.getElementById('resolveBtn');
  const selectAllBtn = document.getElementById('selectAllAnchors');
  const deselectAllBtn = document.getElementById('deselectAllAnchors');
  const resolveInput = document.getElementById('resolveInput');

  if (resolveBtn) {
    resolveBtn.addEventListener('click', handleResolve);
  }
  if (resolveInput) {
    resolveInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleResolve();
      }
    });
  }  

  if (selectAllBtn) {
    selectAllBtn.addEventListener('click', () => {
      document.querySelectorAll('.resolve__anchor-checkbox').forEach(checkbox => {
        checkbox.checked = true;
      });
    });
  }

  if (deselectAllBtn) {
    deselectAllBtn.addEventListener('click', () => {
      document.querySelectorAll('.resolve__anchor-checkbox').forEach(checkbox => {
        checkbox.checked = false;
      });
    });
  }

  console.log('Resolve initialization complete');
}



async function handleResolve() {
    const resolveBtn = document.getElementById('resolveBtn');
    const input = document.getElementById('resolveInput').value.trim();
    const resultsContainer = document.getElementById('resolveResults');

    if (!input) {
        alert('Please enter a time expression');
        return;
    }

    const selectedAnchors = Array.from(document.querySelectorAll('.resolve__anchor-checkbox:checked'))
        .map(checkbox => checkbox.value);

    if (selectedAnchors.length === 0) {
        alert('Please select at least one anchor');
        return;
    }

    try {
        // Show loading state
        resolveBtn.disabled = true;
        resolveBtn.innerHTML = '<i class="material-icons">hourglass_empty</i> Resolving...';
        
        const response = await fetch('/api/resolve/resolve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input: input,
                anchors: selectedAnchors
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to resolve time');
        }

        const data = await response.json();
        
        // Display results
        resultsContainer.style.display = 'block';
        resultsContainer.innerHTML = `
            <div class="resolve__result-header">
                <h3>Resolved Date: ${formatDate(data.resolved_date)}</h3>
            </div>
            <div class="resolve__result-grid">
                ${Object.entries(data.results).map(([label, result]) => `
                    <div class="resolve__result-card">
                        <div class="resolve__result-title">${result.name}</div>
                        <div class="resolve__result-formats">
                            ${result.formats.map(format => `
                                <div class="resolve__result-format">${format}</div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

    } catch (error) {
        alert(error.message);
    } finally {
        // Reset button state
        resolveBtn.disabled = false;
        resolveBtn.innerHTML = '<i class="material-icons">schedule</i> Resolve';
    }
}

function formatDate(isoDate) {
    const date = new Date(isoDate);
    return date.toLocaleString();
}
