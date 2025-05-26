import React from 'react';
import Navigation from './Navigation';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';

const Layout = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner message="Загрузка..." />;
  }

  let title = 'Волонтеры';
  if (user?.role === 'organizer') title = 'Организатор';
  if (user?.role === 'admin') title = 'Администратор';

  return (
    <div className="layout">
      <header className="header">
        <h1>🤝 {title}</h1>
        {user && user.role === 'volunteer' && (
          <p style={{ margin: '8px 0 0 0', fontSize: '14px', opacity: 0.9 }}>
            Привет, {user.first_name}! 👋
          </p>
        )}
      </header>

      <main className="main-content">
        {children}
      </main>

      {user && <Navigation />}
    </div>
  );
};

export default Layout;