import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Calendar, MapPin } from 'lucide-react';
import { getEvents } from '../services/api';
import EventCard from '../components/EventCard';
import LoadingSpinner from '../components/LoadingSpinner';
import useTelegram from '../hooks/useTelegram';

const EventsPage = ({ user }) => {
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showFilters, setShowFilters] = useState(false);

  const navigate = useNavigate();
  const { showAlert, hapticFeedback } = useTelegram();

  const categories = [
    { value: 'all', label: 'Все категории', icon: '📋' },
    { value: 'environmental', label: 'Экология', icon: '🌱' },
    { value: 'social', label: 'Социальные', icon: '🤝' },
    { value: 'education', label: 'Образование', icon: '📚' },
    { value: 'health', label: 'Здоровье', icon: '🏥' },
    { value: 'community', label: 'Сообщество', icon: '🏘️' },
    { value: 'culture', label: 'Культура', icon: '🎭' },
    { value: 'sports', label: 'Спорт', icon: '⚽' },
    { value: 'emergency', label: 'Экстренные', icon: '🚨' }
  ];

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    filterEvents();
  }, [events, searchQuery, selectedCategory]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await getEvents({ upcoming_only: true });
      setEvents(data);
    } catch (error) {
      console.error('Ошибка загрузки мероприятий:', error);
      showAlert('Ошибка загрузки мероприятий: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const filterEvents = () => {
    let filtered = events;

    // Фильтр по категории
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(event => event.category === selectedCategory);
    }

    // Поиск по тексту
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(event =>
        event.title.toLowerCase().includes(query) ||
        event.description?.toLowerCase().includes(query) ||
        event.location?.toLowerCase().includes(query)
      );
    }

    setFilteredEvents(filtered);
  };

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  const handleCategoryChange = (category) => {
    hapticFeedback('light');
    setSelectedCategory(category);
    setShowFilters(false);
  };

  const handleEventClick = (event) => {
    hapticFeedback('medium');
    navigate(`/events/${event.id}`);
  };

  if (loading) {
    return <LoadingSpinner message="Загрузка мероприятий..." />;
  }

  return (
    <div className="events-page">
      {/* Header */}
      <div className="page-header mb-4">
        <h2 className="mb-2">📅 Мероприятия</h2>
        <p className="text-muted">Найдите интересные события для участия</p>
      </div>

      {/* Search and Filters */}
      <div className="search-filters mb-4">
        {/* Search Bar */}
        <div className="search-bar mb-3">
          <div style={{ position: 'relative' }}>
            <Search
              size={20}
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--tg-hint-color)'
              }}
            />
            <input
              type="text"
              className="form-control"
              placeholder="Поиск мероприятий..."
              value={searchQuery}
              onChange={handleSearchChange}
              style={{ paddingLeft: '44px' }}
            />
          </div>
        </div>

        {/* Filter Toggle */}
        <div className="filter-controls mb-3">
          <button
            className="btn btn-outline"
            onClick={() => setShowFilters(!showFilters)}
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            <Filter size={16} />
            {categories.find(c => c.value === selectedCategory)?.label || 'Фильтры'}
          </button>
        </div>

        {/* Category Filters */}
        {showFilters && (
          <div className="category-filters card" style={{ padding: '16px' }}>
            <div className="grid grid-2" style={{ gap: '8px' }}>
              {categories.map(category => (
                <button
                  key={category.value}
                  className={`btn ${selectedCategory === category.value ? 'btn-primary' : 'btn-secondary'} btn-small`}
                  onClick={() => handleCategoryChange(category.value)}
                  style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '8px 12px' }}
                >
                  <span>{category.icon}</span>
                  <span style={{ fontSize: '12px' }}>{category.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Results Counter */}
      <div className="results-info mb-3">
        <p className="text-muted font-small">
          Найдено мероприятий: {filteredEvents.length}
        </p>
      </div>

      {/* Events List */}
      <div className="events-list">
        {filteredEvents.length === 0 ? (
          <div className="empty-state card text-center" style={{ padding: '40px 20px' }}>
            <Calendar size={48} className="text-muted mb-3" />
            <h3 className="mb-2">Мероприятий не найдено</h3>
            <p className="text-muted mb-3">
              {searchQuery || selectedCategory !== 'all'
                ? 'Попробуйте изменить критерии поиска'
                : 'Пока нет доступных мероприятий'
              }
            </p>
            {(searchQuery || selectedCategory !== 'all') && (
              <button
                className="btn btn-outline"
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategory('all');
                }}
              >
                Сбросить фильтры
              </button>
            )}
          </div>
        ) : (
          filteredEvents.map(event => (
            <EventCard
              key={event.id}
              event={event}
              onClick={() => handleEventClick(event)}
              showCategory
              user={user}
            />
          ))
        )}
      </div>

      {/* Load More Button (if needed) */}
      {filteredEvents.length > 0 && filteredEvents.length % 10 === 0 && (
        <div className="load-more text-center mt-4">
          <button className="btn btn-outline">
            Загрузить еще
          </button>
        </div>
      )}
    </div>
  );
};

export default EventsPage;