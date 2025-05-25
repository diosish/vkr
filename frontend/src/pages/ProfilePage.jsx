import React from 'react';

const ProfilePage = ({ user }) => {
  return (
    <div className="profile-page">
      <h2>👤 Мой профиль</h2>
      <div className="card">
        <h3>Информация о пользователе</h3>
        <p><strong>Имя:</strong> {user?.first_name} {user?.last_name}</p>
        <p><strong>Роль:</strong> {user?.role}</p>
        <p><strong>Telegram:</strong> {user?.display_name}</p>
      </div>
    </div>
  );
};

export default ProfilePage;