import React, { useEffect, useState } from 'react';
import { getMyEvents, publishEvent, EVENT_STATUS, apiRequest } from '../services/api';
import EventCard from '../components/EventCard';
import LoadingSpinner from '../components/LoadingSpinner';

const STATUS_LABELS = {
  all: 'Все',
  draft: 'Черновики',
  published: 'Опубликованные',
  cancelled: 'Отменённые',
};

const ManageEventsPage = ({ user }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('all');
  const [publishing, setPublishing] = useState(null);

  useEffect(() => {
    loadEvents();
    // eslint-disable-next-line
  }, [status]);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await getMyEvents();
      setEvents(data);
    } catch (e) {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async (eventId) => {
    setPublishing(eventId);
    try {
      await publishEvent(eventId);
      await loadEvents();
    } catch (e) {
      alert('Ошибка публикации: ' + (e.message || e));
    } finally {
      setPublishing(null);
    }
  };

  const handleChangeStatus = async (eventId, newStatus) => {
    try {
      await apiRequest(`/events/${eventId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      await loadEvents();
    } catch (e) {
      alert('Ошибка смены статуса: ' + (e.message || e));
    }
  };

  return (
    <div className="manage-events-page">
      <h2>⚙️ Управление мероприятиями</h2>
      <div className="card mb-3">
        <div style={{ display: 'flex', gap: 8 }}>
          {Object.entries(STATUS_LABELS).map(([key, label]) => (
            <button
              key={key}
              className={`btn btn-small ${status === key ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setStatus(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {loading ? (
        <LoadingSpinner message="Загрузка ваших мероприятий..." />
      ) : events.length === 0 ? (
        <div className="card text-center">Нет мероприятий</div>
      ) : (
        <div className="events-list">
          {events.map(event => (
            <div key={event.id} className="mb-3">
              <EventCard event={event} user={user}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {event.status === 'draft' && (
                    <button
                      className="btn btn-success btn-small mt-2"
                      disabled={publishing === event.id}
                      onClick={() => handlePublish(event.id)}
                    >
                      {publishing === event.id ? 'Публикация...' : 'Опубликовать'}
                    </button>
                  )}
                  <select
                    value={event.status}
                    onChange={e => handleChangeStatus(event.id, e.target.value)}
                    style={{ marginLeft: 8 }}
                  >
                    <option value={EVENT_STATUS.DRAFT}>Черновик</option>
                    <option value={EVENT_STATUS.PUBLISHED}>Опубликовано</option>
                    <option value={EVENT_STATUS.CANCELLED}>Отменено</option>
                    <option value={EVENT_STATUS.COMPLETED}>Завершено</option>
                  </select>
                </div>
              </EventCard>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ManageEventsPage;