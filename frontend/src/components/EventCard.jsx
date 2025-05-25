import React from 'react';
import { Calendar, MapPin, Users, Clock } from 'lucide-react';

const EventCard = ({ event, onClick, compact = false, showCategory = false, user }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getCategoryIcon = (category) => {
    const icons = {
      environmental: '🌱',
      social: '🤝',
      education: '📚',
      health: '🏥',
      community: '🏘️',
      culture: '🎭',
      sports: '⚽',
      emergency: '🚨',
      other: '📋'
    };
    return icons[category] || icons.other;
  };

  const getCategoryLabel = (category) => {
    const labels = {
      environmental: 'Экология',
      social: 'Социальные',
      education: 'Образование',
      health: 'Здоровье',
      community: 'Сообщество',
      culture: 'Культура',
      sports: 'Спорт',
      emergency: 'Экстренные',
      other: 'Другое'
    };
    return labels[category] || labels.other;
  };

  const getStatusBadge = () => {
    if (event.user_registration_status) {
      const statusMap = {
        pending: { text: 'Ожидание', class: 'badge-pending' },
        confirmed: { text: 'Записан', class: 'badge-confirmed' },
        cancelled: { text: 'Отменено', class: 'badge-cancelled' }
      };
      const status = statusMap[event.user_registration_status];
      return status ? <span className={`badge ${status.class}`}>{status.text}</span> : null;
    }
    return null;
  };

  return (
    <div
      className={`event-card ${compact ? 'compact' : ''}`}
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      {/* Header */}
      <div className="event-header" style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <h3 className="mb-1" style={{ fontSize: compact ? '16px' : '18px' }}>
              {event.title}
            </h3>
            {showCategory && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '8px' }}>
                <span>{getCategoryIcon(event.category)}</span>
                <span className="font-small text-muted">{getCategoryLabel(event.category)}</span>
              </div>
            )}
          </div>
          {getStatusBadge()}
        </div>
      </div>

      {/* Description */}
      {!compact && event.short_description && (
        <p className="text-muted mb-3" style={{ fontSize: '14px', lineHeight: '1.4' }}>
          {event.short_description}
        </p>
      )}

      {/* Event Details */}
      <div className="event-details" style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
          <Calendar size={16} className="text-muted" />
          <span className="font-small text-muted">
            {formatDate(event.start_date)}
          </span>
        </div>

        {event.location && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <MapPin size={16} className="text-muted" />
            <span className="font-small text-muted">{event.location}</span>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Users size={16} className="text-muted" />
          <span className="font-small text-muted">
            {event.current_volunteers_count}
            {event.max_volunteers > 0 && ` / ${event.max_volunteers}`} волонтеров
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      {event.max_volunteers > 0 && (
        <div className="progress-section mb-3">
          <div style={{
            width: '100%',
            height: '6px',
            backgroundColor: 'var(--tg-secondary-bg-color)',
            borderRadius: '3px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${event.progress_percentage}%`,
              height: '100%',
              backgroundColor: event.progress_percentage >= 100 ? '#dc3545' : 'var(--tg-button-color)',
              transition: 'width 0.3s ease'
            }} />
          </div>
          <div className="font-small text-muted mt-1">
            {event.progress_percentage}% заполнено
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="event-meta">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="font-small text-muted">
            Организатор: {event.creator_name}
          </span>

          {event.can_register && user?.role === 'volunteer' && !event.user_registration_status && (
            <span className="font-small text-primary">
              Можно записаться →
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventCard;