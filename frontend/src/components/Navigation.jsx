import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Home, Calendar, User, FileText, Plus } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  // Определяем навигационные элементы в зависимости от роли
  const getNavItems = () => {
    const baseItems = [
      { path: '/', icon: Home, label: 'Главная' },
      { path: '/events', icon: Calendar, label: 'События' },
      { path: '/profile', icon: User, label: 'Профиль' }
    ];

    if (user?.role === 'volunteer') {
      baseItems.splice(2, 0, {
        path: '/my-registrations',
        icon: FileText,
        label: 'Заявки'
      });
    }

    if (user?.role === 'organizer' || user?.role === 'admin') {
      baseItems.splice(2, 0, {
        path: '/create-event',
        icon: Plus,
        label: 'Создать'
      });
      baseItems.splice(2, 0, {
        path: '/manage-events',
        icon: FileText,
        label: 'Мои события'
      });
    }

    if (user?.role === 'admin') {
      baseItems.push({
        path: '/admin',
        icon: FileText,
        label: 'Админ'
      });
    }

    return baseItems;
  };

  const navItems = getNavItems();

  return (
    <nav className="bottom-nav">
      {navItems.map(({ path, icon: Icon, label }) => (
        <div
          key={path}
          className={`nav-item ${location.pathname === path ? 'active' : ''}`}
          onClick={() => navigate(path)}
        >
          <div className="nav-icon">
            <Icon size={20} />
          </div>
          <span>{label}</span>
        </div>
      ))}
    </nav>
  );
};

export default Navigation;