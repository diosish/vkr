import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Users, Award, TrendingUp } from 'lucide-react';
import { getEvents, getMyRegistrations } from '../services/api';
import EventCard from '../components/EventCard';
import LoadingSpinner from '../components/LoadingSpinner';
import useTelegram from '../hooks/useTelegram';
import { User, FileText } from 'react-feather';

const getRoleWelcome = (role) => {
  switch (role) {
    case 'admin':
      return {
        title: 'Панель администратора',
        description: 'Управляйте системой и пользователями',
        icon: '🔧'
      };
    case 'organizer':
      return {
        title: 'Панель организатора',
        description: 'Создавайте и управляйте мероприятиями',
        icon: '👔'
      };
    default:
      return {
        title: 'Добро пожаловать!',
        description: 'Найдите интересные мероприятия и станьте волонтером',
        icon: '🤝'
      };
  }
};

const HomePage = ({ user }) => {
  const [stats, setStats] = useState({
    upcomingEvents: 0,
    myRegistrations: 0,
    completedEvents: 0
  });
  const [recentEvents, setRecentEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { showAlert } = useTelegram();

  useEffect(() => {
    if (user) {
      loadHomeData();
    }
  }, [user]);

  const loadHomeData = async () => {
    try {
      setLoading(true);

      const eventsData = await getEvents({ limit: 3 });
      setRecentEvents(eventsData);
      setStats(prev => ({ ...prev, upcomingEvents: eventsData.length }));

      if (user.role === 'volunteer') {
        const registrationsData = await getMyRegistrations();
        setStats(prev => ({
          ...prev,
          myRegistrations: registrationsData.filter(r => r.status === 'confirmed').length,
          completedEvents: registrationsData.filter(r => r.status === 'completed').length
        }));
      }
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      showAlert('Ошибка загрузки данных: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <LoadingSpinner message="Загрузка профиля..." />;
  }

  const roleInfo = getRoleWelcome(user.role);

  if (loading) {
    return <LoadingSpinner message="Загрузка главной страницы..." />;
  }

  return (
    <div className="home-page">
      {/* Welcome Section */}
      <div className="welcome-section">
        <div className="welcome-card card">
          <div style={{ fontSize: '48px', textAlign: 'center', marginBottom: '16px' }}>
            {roleInfo.icon}
          </div>
          <h2 className="text-center mb-2">{roleInfo.title}</h2>
          <p className="text-center text-muted mb-3">{roleInfo.description}</p>

          {user.role === 'volunteer' && (
            <button
              className="btn btn-primary btn-full"
              onClick={() => navigate('/events')}
            >
              🔍 Найти мероприятия
            </button>
          )}

          {(user.role === 'organizer' || user.role === 'admin') && (
            <button
              className="btn btn-primary btn-full"
              onClick={() => navigate('/create-event')}
            >
              ➕ Создать мероприятие
            </button>
          )}
        </div>
      </div>

      {/* Stats Section */}
      <div className="stats-section">
        <h3 className="mb-3">📊 Статистика</h3>
        <div className="grid grid-3">
          <div className="stat-card card text-center">
            <Calendar size={24} className="text-primary mb-2" />
            <div className="font-large">{stats.upcomingEvents}</div>
            <div className="font-small text-muted">Предстоящие события</div>
          </div>

          {user.role === 'volunteer' && (
            <>
              <div className="stat-card card text-center">
                <Users size={24} className="text-primary mb-2" />
                <div className="font-large">{stats.myRegistrations}</div>
                <div className="font-small text-muted">Мои регистрации</div>
              </div>

              <div className="stat-card card text-center">
                <Award size={24} className="text-primary mb-2" />
                <div className="font-large">{stats.completedEvents}</div>
                <div className="font-small text-muted">Завершено</div>
              </div>
            </>
          )}

          {(user.role === 'organizer' || user.role === 'admin') && (
            <>
              <div className="stat-card card text-center">
                <TrendingUp size={24} className="text-primary mb-2" />
                <div className="font-large">12</div>
                <div className="font-small text-muted">Создано событий</div>
              </div>

              <div className="stat-card card text-center">
                <Users size={24} className="text-primary mb-2" />
                <div className="font-large">45</div>
                <div className="font-small text-muted">Всего участников</div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Recent Events */}
      {recentEvents.length > 0 && (
        <div className="recent-events-section">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px'
            }}
          >
            <h3 className="mb-0">🔥 Актуальные мероприятия</h3>
            <button
              className="btn btn-outline btn-small"
              onClick={() => navigate('/events')}
            >
              Все →
            </button>
          </div>

          <div className="events-list">
            {recentEvents.map(event => (
              <EventCard
                key={event.id}
                event={event}
                onClick={() => navigate(`/events/${event.id}`)}
                compact
              />
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="quick-actions-section">
        <h3 className="mb-3">⚡ Быстрые действия</h3>
        <div className="grid grid-2">
          <button
            className="action-card btn btn-secondary"
            onClick={() => navigate('/profile')}
            style={{ padding: '20px', height: 'auto', flexDirection: 'column' }}
          >
            <User size={24} className="mb-2" />
            <span>Мой профиль</span>
          </button>

          {user.role === 'volunteer' && (
            <button
              className="action-card btn btn-secondary"
              onClick={() => navigate('/my-registrations')}
              style={{ padding: '20px', height: 'auto', flexDirection: 'column' }}
            >
              <FileText size={24} className="mb-2" />
              <span>Мои заявки</span>
            </button>
          )}

          {(user.role === 'organizer' || user.role === 'admin') && (
            <button
              className="action-card btn btn-secondary"
              onClick={() => navigate('/manage-events')}
              style={{ padding: '20px', height: 'auto', flexDirection: 'column' }}
            >
              <Calendar size={24} className="mb-2" />
              <span>Управление</span>
            </button>
          )}
        </div>
      </div>

      {/* Tips Section */}
      <div className="tips-section">
        <div
          className="tip-card card"
          style={{ backgroundColor: 'var(--tg-secondary-bg-color)' }}
        >
          <h4 className="mb-2">💡 Совет дня</h4>
          {user.role === 'volunteer' ? (
            <p className="text-muted mb-0">
              Заполните свой профиль полностью, чтобы организаторы могли лучше понять ваши навыки и опыт!
            </p>
          ) : (
            <p className="text-muted mb-0">
              Добавьте подробное описание к вашим мероприятиям, чтобы привлечь больше волонтеров!
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
