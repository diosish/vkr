import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, MapPin, Users, Clock, ArrowLeft } from 'lucide-react';
import { getEvent, registerForEvent } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import useTelegram from '../hooks/useTelegram';

const EventDetailsPage = ({ user }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showAlert, setBackButton, hideBackButton } = useTelegram();

  useEffect(() => {
    loadEvent();
    setBackButton(() => navigate(-1));
    return () => hideBackButton();
  }, [id]);

  const loadEvent = async () => {
    try {
      const data = await getEvent(id);
      setEvent(data);
    } catch (error) {
      console.error('Ошибка загрузки мероприятия:', error);
      showAlert('Ошибка загрузки мероприятия');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    try {
      await registerForEvent({ event_id: event.id });
      showAlert('Заявка подана успешно!');
      loadEvent(); // Перезагружаем данные
    } catch (error) {
      showAlert('Ошибка подачи заявки: ' + error.message);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Загрузка мероприятия..." />;
  }

  if (!event) {
    return (
      <div className="error-screen">
        <h2>Мероприятие не найдено</h2>
        <button onClick={() => navigate('/events')} className="btn btn-primary">
          К списку мероприятий
        </button>
      </div>
    );
  }

  return (
    <div className="event-details-page">
      <button onClick={() => navigate(-1)} className="btn btn-outline mb-3">
        <ArrowLeft size={16} /> Назад
      </button>

      <div className="event-header card mb-4">
        <h1 className="mb-3">{event.title}</h1>
        <div className="event-meta mb-3">
          <div className="mb-2">
            <Calendar size={16} className="text-muted" />
            <span className="ml-2">
              {new Date(event.start_date).toLocaleDateString('ru-RU', {
                day: 'numeric',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>
          </div>
          {event.location && (
            <div className="mb-2">
              <MapPin size={16} className="text-muted" />
              <span className="ml-2">{event.location}</span>
            </div>
          )}
          <div>
            <Users size={16} className="text-muted" />
            <span className="ml-2">
              {event.current_volunteers_count}
              {event.max_volunteers > 0 && ` / ${event.max_volunteers}`} волонтеров
            </span>
          </div>
        </div>
      </div>

      <div className="event-description card mb-4">
        <h3 className="mb-3">Описание</h3>
        <p>{event.description}</p>
      </div>

      {event.can_register && user?.role === 'volunteer' && !event.user_registration_status && (
        <button
          onClick={handleRegister}
          className="btn btn-primary btn-full"
        >
          Подать заявку
        </button>
      )}
    </div>
  );
};

export default EventDetailsPage;