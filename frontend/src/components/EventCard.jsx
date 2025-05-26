import React from 'react';
import { Calendar, MapPin, Users, Clock } from 'lucide-react';
import { Card, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { formatDate, formatDateShort } from '../services/api';

const EventCard = ({ event, onClick, compact = false, showCategory = false, user }) => {
  const navigate = useNavigate();

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

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/events/${event.id}`);
    }
  };

  return (
    <Card className="mb-3" style={{ cursor: 'pointer' }} onClick={handleClick}>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h5 className="mb-0">{event.title}</h5>
        <span className={`badge bg-${getStatusColor(event.status)}`}>
          {getStatusText(event.status)}
        </span>
      </Card.Header>
      <Card.Body>
        <Card.Text>
          <strong>Место:</strong> {event.location}<br/>
          <strong>Дата начала:</strong> {formatDate(event.start_date)}<br/>
          <strong>Дата окончания:</strong> {formatDate(event.end_date)}<br/>
          <strong>Волонтеры:</strong> {event.current_volunteers_count}/{event.max_volunteers}
        </Card.Text>
        {event.short_description && (
          <Card.Text className="text-muted">
            {event.short_description}
          </Card.Text>
        )}
      </Card.Body>
    </Card>
  );
};

const getStatusColor = (status) => {
  switch (status) {
    case 'draft':
      return 'secondary';
    case 'published':
      return 'success';
    case 'cancelled':
      return 'danger';
    case 'completed':
      return 'info';
    default:
      return 'secondary';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'draft':
      return 'Черновик';
    case 'published':
      return 'Опубликовано';
    case 'cancelled':
      return 'Отменено';
    case 'completed':
      return 'Завершено';
    default:
      return status;
  }
};

export default EventCard;