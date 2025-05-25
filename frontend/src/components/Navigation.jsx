import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Home, Calendar, Plus, User } from 'react-feather';

const navItems = [
  { path: '/', icon: <Home /> },
  { path: '/my-registrations', icon: <User /> },
  { path: '/create-event', icon: <Plus /> },
  { path: '/manage-events', icon: <Calendar /> },
];

function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleNavClick = (path) => {
    navigate(path);
  };

  return (
    <nav className="nav-bar">
      {navItems.map(({ path, icon }) => (
        <button
          key={path}
          className={`nav-item ${location.pathname === path ? 'active' : ''}`}
          onClick={() => handleNavClick(path)}
        >
          {icon}
        </button>
      ))}
    </nav>
  );
}

export default Navigation;