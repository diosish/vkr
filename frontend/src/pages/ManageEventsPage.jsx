import React, { useEffect, useState } from 'react';
import { getMyEvents, publishEvent } from '../services/api';
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
      let url = '/events/my/created';
      if (status !== 'all') url += `?status=${status}`;
      const res = await fetch(url, { headers: { 'Content-Type': 'application/json' } });
      const data = await res.json();
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
                {event.status === 'draft' && (
                  <button
                    className="btn btn-success btn-small mt-2"
                    disabled={publishing === event.id}
                    onClick={() => handlePublish(event.id)}
                  >
                    {publishing === event.id ? 'Публикация...' : 'Опубликовать'}
                  </button>
                )}
              </EventCard>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ManageEventsPage;