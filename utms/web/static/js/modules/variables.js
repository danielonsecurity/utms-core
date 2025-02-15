export function initializeVariables() {
    console.log('Initializing variables...');

    // Use event delegation for original code toggles
    document.addEventListener('click', (e) => {
        if (e.target.closest('.variable-card__original-btn')) {
            const button = e.target.closest('.variable-card__original-btn');
            handleToggleOriginal(button);
        }
    });

    console.log('Variables initialization complete');
}

function handleToggleOriginal(button) {
    const container = button.parentElement;
    const codeBlock = container.querySelector('.variable-card__original-code');
    
    if (codeBlock.style.display === 'block') {
        codeBlock.style.display = 'none';
        button.title = 'Show original expression';
    } else {
        codeBlock.style.display = 'block';
        button.title = 'Hide original expression';
    }
}
