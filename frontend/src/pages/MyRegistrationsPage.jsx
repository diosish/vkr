import React, { useState, useEffect } from 'react';
import { Calendar, MapPin, Clock } from 'lucide-react';
import { getMyRegistrations } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const MyRegistrationsPage = ({ user }) => {
  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRegistrations();
  }, []);

  const loadRegistrations = async () => {
    try {
      const data = await getMyRegistrations();
      setRegistrations(data);
    } catch (error) {
      console.error('Ошибка загрузки регистраций:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Загрузка ваших заявок..." />;
  }

  return (
    <div className="my-registrations-page">
      <h2 className="mb-4">📋 Мои заявки</h2>

      {registrations.length === 0 ? (
        <div className="empty-state card text-center" style={{ padding: '40px 20px' }}>
          <Calendar size={48} className="text-muted mb-3" />
          <h3 className="mb-2">Пока нет заявок</h3>
          <p className="text-muted">Подайте заявку на участие в мероприятии</p>
        </div>
      ) : (
        <div className="registrations-list">
          {registrations.map(registration => (
            <div key={registration.id} className="card mb-3">
              <h4>{registration.event_title}</h4>
              <div className="registration-info">
                <div className="mb-2">
                  <Calendar size={16} className="text-muted" />
                  <span className="ml-2">
                    {new Date(registration.event_start_date).toLocaleDateString()}
                  </span>
                </div>
                <div className="mb-2">
                  <span className={`badge badge-${registration.status}`}>
                    {registration.status === 'confirmed' ? 'Подтверждено' :
                     registration.status === 'pending' ? 'Ожидание' : 'Отменено'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyRegistrationsPage;