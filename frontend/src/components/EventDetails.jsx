import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Form, Alert, Modal } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import { getEvent, updateEvent, deleteEvent } from '../services/api';

const EventDetails = () => {
    const { eventId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const [event, setEvent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showStatusModal, setShowStatusModal] = useState(false);
    const [selectedStatus, setSelectedStatus] = useState('');

    useEffect(() => {
        fetchEvent();
    }, [eventId]);

    const fetchEvent = async () => {
        try {
            const eventData = await getEvent(eventId);
            setEvent(eventData);
            setLoading(false);
        } catch (err) {
            setError('Ошибка при загрузке мероприятия');
            setLoading(false);
        }
    };

    const handleStatusChange = async () => {
        try {
            await updateEvent(eventId, { status: selectedStatus });
            await fetchEvent();
            setShowStatusModal(false);
        } catch (err) {
            setError('Ошибка при изменении статуса');
        }
    };

    const handleDelete = async () => {
        try {
            await deleteEvent(eventId);
            navigate('/my-events');
        } catch (err) {
            setError('Ошибка при удалении мероприятия');
        }
    };

    const handleEdit = () => {
        navigate(`/events/${eventId}/edit`);
    };

    if (loading) return <div>Загрузка...</div>;
    if (error) return <Alert variant="danger">{error}</Alert>;
    if (!event) return <Alert variant="warning">Мероприятие не найдено</Alert>;

    const isCreator = user && event.creator_id === user.id;
    const isAdmin = user && user.role === 'admin';

    return (
        <div className="container mt-4">
            <Card>
                <Card.Header className="d-flex justify-content-between align-items-center">
                    <h2>{event.title}</h2>
                    {(isCreator || isAdmin) && (
                        <div>
                            <Button variant="primary" className="me-2" onClick={handleEdit}>
                                Редактировать
                            </Button>
                            <Button 
                                variant="warning" 
                                className="me-2" 
                                onClick={() => setShowStatusModal(true)}
                            >
                                Изменить статус
                            </Button>
                            <Button 
                                variant="danger" 
                                onClick={() => setShowDeleteModal(true)}
                            >
                                Удалить
                            </Button>
                        </div>
                    )}
                </Card.Header>
                <Card.Body>
                    <p><strong>Статус:</strong> {event.status}</p>
                    <p><strong>Описание:</strong> {event.description}</p>
                    <p><strong>Место:</strong> {event.location}</p>
                    <p><strong>Дата начала:</strong> {new Date(event.start_date).toLocaleString()}</p>
                    <p><strong>Дата окончания:</strong> {new Date(event.end_date).toLocaleString()}</p>
                    <p><strong>Максимум волонтеров:</strong> {event.max_volunteers}</p>
                    <p><strong>Текущее количество волонтеров:</strong> {event.current_volunteers_count}</p>
                </Card.Body>
            </Card>

            {/* Модальное окно изменения статуса */}
            <Modal show={showStatusModal} onHide={() => setShowStatusModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Изменить статус мероприятия</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group>
                            <Form.Label>Новый статус</Form.Label>
                            <Form.Select 
                                value={selectedStatus} 
                                onChange={(e) => setSelectedStatus(e.target.value)}
                            >
                                <option value="">Выберите статус</option>
                                <option value="draft">Черновик</option>
                                <option value="published">Опубликовано</option>
                                <option value="cancelled">Отменено</option>
                                <option value="completed">Завершено</option>
                            </Form.Select>
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowStatusModal(false)}>
                        Отмена
                    </Button>
                    <Button variant="primary" onClick={handleStatusChange}>
                        Сохранить
                    </Button>
                </Modal.Footer>
            </Modal>

            {/* Модальное окно подтверждения удаления */}
            <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Подтверждение удаления</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    Вы уверены, что хотите удалить это мероприятие?
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
                        Отмена
                    </Button>
                    <Button variant="danger" onClick={handleDelete}>
                        Удалить
                    </Button>
                </Modal.Footer>
            </Modal>
        </div>
    );
};

export default EventDetails; 