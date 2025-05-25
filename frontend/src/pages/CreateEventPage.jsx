import React from 'react';

const CreateEventPage = ({ user }) => {
  return (
    <div className="create-event-page">
      <h2>➕ Создать мероприятие</h2>
      <div className="card">
        <p>Форма создания мероприятия будет здесь</p>
        <p>Доступно для: {user?.role}</p>
      </div>
    </div>
  );
};

export default CreateEventPage;