import { initializeSidebar } from './modules/sidebar.js';
import { initializeConfig } from './modules/config.js';
import { initializeUnits } from './modules/units.js';
import { initializeAnchors } from './modules/anchors.js';
import { initializeFilters } from './modules/filters.js';

async function initializeApp() {
    try {
        const page = document.body.dataset.page;
        if (!page) {
            console.warn('No page type specified');
            return;
        }

        // Initialize core functionality
      await initializeSidebar();
      await initializeFilters();

        // Initialize page-specific functionality
        switch (page) {
            case 'units':
                await initializeUnits();
                break;
            case 'anchors':
                await initializeAnchors();
                break;
            case 'config':
                await initializeConfig();
            break;
          default:
            console.warn(`Unknown page type: ${page}`);
            return;
        }

        console.log(`Application initialized for ${page} page`);
    } catch (error) {
        console.error('Failed to initialize application:', error);
        // You might want to show a user-friendly error message
        document.body.innerHTML += `
            <div class="error-message">
                Failed to initialize application. Please refresh the page.
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', initializeApp);

window.addEventListener('error', (event) => {
    if (event.message.includes('Failed to load module script')) {
        console.error('Module loading error:', event);
        document.body.innerHTML += `
            <div class="error-message">
                Failed to load application resources. Please check your connection and refresh.
            </div>
        `;
    }
});
