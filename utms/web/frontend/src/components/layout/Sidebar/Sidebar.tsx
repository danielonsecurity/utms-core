import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';

interface NavItem {
  path: string;
  title: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: '/', title: 'Dashboard', icon: 'dashboard' },
  { path: '/config', title: 'Configuration', icon: 'settings' },
  { path: '/units', title: 'Units', icon: 'straighten' },
  { path: '/anchors', title: 'Anchors', icon: 'anchor' },
  { path: '/variables', title: 'Variables', icon: 'data_object' },
  { path: '/clock', title: 'Clock', icon: 'schedule' },
  { path: '/calendar', title: 'Calendar', icon: 'calendar_today' },
  { path: '/resolve', title: 'Resolve', icon: 'smart_toy' },
  { path: '/events', title: 'Events', icon: 'event' },
  { path: '/analytics', title: 'Analytics', icon: 'analytics' },
];

interface SidebarProps {
  activePage?: string;
}

export const Sidebar = ({ activePage }: SidebarProps) => {
  const [isCollapsed, setIsCollapsed] = useState(() => 
    localStorage.getItem('sidebarCollapsed') === 'true'
  );
  const sidebarRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (sidebarRef.current) {
      sidebarRef.current.classList.add('no-transition');
      sidebarRef.current.offsetHeight; // Force reflow
      requestAnimationFrame(() => {
        sidebarRef.current?.classList.remove('no-transition');
      });
    }
  }, []);

  const handleToggle = () => {
    if (sidebarRef.current) {
      sidebarRef.current.classList.add('animate');
      setIsCollapsed(prev => {
        const newState = !prev;
        localStorage.setItem('sidebarCollapsed', String(newState));
        return newState;
      });
      setTimeout(() => {
        sidebarRef.current?.classList.remove('animate');
      }, 300);
    }
  };

  return (
    <nav 
      ref={sidebarRef}
      className={`sidebar ${isCollapsed ? 'sidebar--collapsed' : ''}`}
    >
      <div className="sidebar__header">
        <img src="/images/logo.png" alt="UTMS Logo" className="sidebar__logo" />
        <h2 className="sidebar__header-title">UTMS</h2>
      </div>
      
      <ul className="sidebar__nav">
        {navItems.map((item) => (
          <li 
            key={item.path}
            className={`sidebar__nav-item ${
              activePage === item.title.toLowerCase() ? 'sidebar__nav-item--active' : ''
            }`}
          >
            <Link 
              to={item.path} 
              className="sidebar__nav-link"
              data-title={item.title}
            >
              <i className="material-icons sidebar__nav-icon">{item.icon}</i>
              <span className="sidebar__nav-text">{item.title}</span>
            </Link>
          </li>
        ))}
      </ul>

      <div className="sidebar__toggle">
        <button 
          className="sidebar__toggle-button"
          onClick={handleToggle}
        >
          <i className="material-icons sidebar__toggle-icon">
            chevron_left
          </i>
        </button>
      </div>
    </nav>
  );
};
