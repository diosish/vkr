import React from 'react';
import Navigation from './Navigation';

const Layout = ({ user, children }) => {
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

      <Navigation user={user} />
    </div>
  );
};

export default Layout;