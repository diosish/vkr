import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Home,
  Calendar,
  User,
  FileText,
  Plus
} from 'lucide-react';
import useTelegram from '../hooks/useTelegram';

const Navigation = ({ user }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { hapticFeedback } = useTelegram();

  const handleNavClick = (path) => {
    hapticFeedback('light');
    navigate(path);
  };

  const navItems = [
    {
      path: '/',
      icon: Home,
      label: 'Главная',
      show: true
    },
    {
      path: '/events',
      icon: Calendar,
      label: 'События',
      show: true
    },
    {
      path: '/my-registrations',
      icon: FileText,
      label: 'Мои заявки',
      show: user?.role === 'volunteer'
    },
    {
      path: '/create-event',
      icon: Plus,
      label: 'Создать',
      show: user?.role === 'organizer' || user?.role === 'admin'
    },
    {
  path: '/profile',
  icon: User,
  label: 'Профиль',
  show: true
    }
].filter(item => item.show);
return (
<nav className="bottom-nav">
{navItems.map(({ path, icon: Icon, label }) => (
<button
key={path}
className={nav-item ${location.pathname === path ? 'active' : ''}}
onClick={() => handleNavClick(path)}
>
<Icon className="nav-icon" size={20} />
<span>{label}</span>
</button>
))}
</nav>
);
};
export default Navigation;