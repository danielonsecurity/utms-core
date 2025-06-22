export function initializeSidebar() {
  console.log('Initializing sidebar...');
  
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) {
    console.warn('Sidebar element not found');
    return;
  }

  sidebar.classList.add('no-transition');
  
  // Load saved state
  const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  if (isSidebarCollapsed) {
    console.log("Applying collapsed state on load");
    sidebar.classList.add('sidebar--collapsed');
  }



  sidebar.offsetHeight;

  // Remove no-transition class after a brief delay
  requestAnimationFrame(() => {
    sidebar.classList.remove('no-transition');
  });

  // Add click event listener
  const toggleBtn = document.getElementById('sidebar-toggle-btn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      console.log("Toggle button clicked");
      sidebar.classList.add("animate");
      sidebar.classList.toggle('sidebar--collapsed');
      localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('sidebar--collapsed'));
      setTimeout(() => {
        sidebar.classList.remove('animate');
      }, 300);
    });
  }

  // Debug logging
  console.log('Initial sidebar state:', {
    collapsed: sidebar.classList.contains('sidebar--collapsed'),
    hasAnimate: sidebar.classList.contains('animate'),
    storedState: localStorage.getItem('sidebarCollapsed')
  });

  return {
    toggle: () => toggleBtn?.click(),
    isCollapsed: () => sidebar.classList.contains('sidebar--collapsed'),
    expand: () => {
      sidebar.classList.remove('sidebar--collapsed');
      localStorage.setItem('sidebarCollapsed', 'false');
    },
    collapse: () => {
      sidebar.classList.add('sidebar--collapsed');
      localStorage.setItem('sidebarCollapsed', 'true');
    }
  };
}
