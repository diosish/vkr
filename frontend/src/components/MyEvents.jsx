import React, { useState, useEffect } from 'react';
import { Card, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getMyEvents } from '../services/api';
import EventCard from './EventCard';

const MyEvents = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!user) {
            setError('Необходима авторизация');
            setLoading(false);
            return;
        }

        if (user.role !== 'organizer' && user.role !== 'admin') {
            setError('У вас нет прав для просмотра созданных мероприятий');
            setLoading(false);
            return;
        }

        fetchEvents();
    }, [user]);

    const fetchEvents = async () => {
        try {
            const eventsData = await getMyEvents();
            setEvents(eventsData);
            setLoading(false);
        } catch (err) {
            setError('Ошибка при загрузке мероприятий');
            setLoading(false);
        }
    };

    const handleCreateEvent = () => {
        navigate('/events/create');
    };

    if (loading) return <div>Загрузка...</div>;
    if (error) return <Alert variant="danger">{error}</Alert>;

    return (
        <div className="container mt-4">
            <Card>
                <Card.Header className="d-flex justify-content-between align-items-center">
                    <h2>Мои мероприятия</h2>
                    <Button variant="primary" onClick={handleCreateEvent}>
                        Создать мероприятие
                    </Button>
                </Card.Header>
                <Card.Body>
                    {events.length === 0 ? (
                        <Alert variant="info">
                            У вас пока нет созданных мероприятий
                        </Alert>
                    ) : (
                        <div>
                            {events.map(event => (
                                <EventCard 
                                    key={event.id} 
                                    event={event}
                                    onClick={() => navigate(`/events/${event.id}`)}
                                />
                            ))}
                        </div>
                    )}
                </Card.Body>
            </Card>
        </div>
    );
};

export default MyEvents; 