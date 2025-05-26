import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Form, Button, Card, Alert } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import { getEvent, updateEvent } from '../services/api';

const EventEdit = () => {
    const { eventId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const [event, setEvent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        short_description: '',
        location: '',
        address: '',
        start_date: '',
        end_date: '',
        registration_deadline: '',
        max_volunteers: 0,
        min_volunteers: 1,
        required_skills: [],
        preferred_skills: [],
        min_age: null,
        max_age: null,
        requirements_description: '',
        what_to_bring: '',
        dress_code: '',
        meal_provided: false,
        transport_provided: false,
        contact_person: '',
        contact_phone: '',
        contact_email: ''
    });

    useEffect(() => {
        fetchEvent();
    }, [eventId]);

    const fetchEvent = async () => {
        try {
            const response = await getEvent(eventId);
            const eventData = response.data;
            setEvent(eventData);
            setFormData({
                ...eventData,
                start_date: new Date(eventData.start_date).toISOString().slice(0, 16),
                end_date: new Date(eventData.end_date).toISOString().slice(0, 16),
                registration_deadline: eventData.registration_deadline 
                    ? new Date(eventData.registration_deadline).toISOString().slice(0, 16)
                    : ''
            });
            setLoading(false);
        } catch (err) {
            setError('Ошибка при загрузке мероприятия');
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await updateEvent(eventId, formData);
            navigate(`/events/${eventId}`);
        } catch (err) {
            setError('Ошибка при сохранении мероприятия');
        }
    };

    if (loading) return <div>Загрузка...</div>;
    if (error) return <Alert variant="danger">{error}</Alert>;
    if (!event) return <Alert variant="warning">Мероприятие не найдено</Alert>;

    const isCreator = user && event.creator_id === user.id;
    const isAdmin = user && user.role === 'admin';

    if (!isCreator && !isAdmin) {
        return <Alert variant="danger">У вас нет прав на редактирование этого мероприятия</Alert>;
    }

    return (
        <div className="container mt-4">
            <Card>
                <Card.Header>
                    <h2>Редактирование мероприятия</h2>
                </Card.Header>
                <Card.Body>
                    <Form onSubmit={handleSubmit}>
                        <Form.Group className="mb-3">
                            <Form.Label>Название</Form.Label>
                            <Form.Control
                                type="text"
                                name="title"
                                value={formData.title}
                                onChange={handleChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Описание</Form.Label>
                            <Form.Control
                                as="textarea"
                                name="description"
                                value={formData.description}
                                onChange={handleChange}
                                rows={3}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Краткое описание</Form.Label>
                            <Form.Control
                                type="text"
                                name="short_description"
                                value={formData.short_description}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Место проведения</Form.Label>
                            <Form.Control
                                type="text"
                                name="location"
                                value={formData.location}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Адрес</Form.Label>
                            <Form.Control
                                type="text"
                                name="address"
                                value={formData.address}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Дата начала</Form.Label>
                            <Form.Control
                                type="datetime-local"
                                name="start_date"
                                value={formData.start_date}
                                onChange={handleChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Дата окончания</Form.Label>
                            <Form.Control
                                type="datetime-local"
                                name="end_date"
                                value={formData.end_date}
                                onChange={handleChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Дедлайн регистрации</Form.Label>
                            <Form.Control
                                type="datetime-local"
                                name="registration_deadline"
                                value={formData.registration_deadline}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Максимум волонтеров</Form.Label>
                            <Form.Control
                                type="number"
                                name="max_volunteers"
                                value={formData.max_volunteers}
                                onChange={handleChange}
                                min="0"
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Минимум волонтеров</Form.Label>
                            <Form.Control
                                type="number"
                                name="min_volunteers"
                                value={formData.min_volunteers}
                                onChange={handleChange}
                                min="1"
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Контактное лицо</Form.Label>
                            <Form.Control
                                type="text"
                                name="contact_person"
                                value={formData.contact_person}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Контактный телефон</Form.Label>
                            <Form.Control
                                type="tel"
                                name="contact_phone"
                                value={formData.contact_phone}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Контактный email</Form.Label>
                            <Form.Control
                                type="email"
                                name="contact_email"
                                value={formData.contact_email}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Check
                                type="checkbox"
                                name="meal_provided"
                                label="Предоставляется питание"
                                checked={formData.meal_provided}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Check
                                type="checkbox"
                                name="transport_provided"
                                label="Предоставляется транспорт"
                                checked={formData.transport_provided}
                                onChange={handleChange}
                            />
                        </Form.Group>

                        <div className="d-flex justify-content-between">
                            <Button variant="secondary" onClick={() => navigate(`/events/${eventId}`)}>
                                Отмена
                            </Button>
                            <Button variant="primary" type="submit">
                                Сохранить
                            </Button>
                        </div>
                    </Form>
                </Card.Body>
            </Card>
        </div>
    );
};

export default EventEdit; 