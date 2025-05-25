// frontend/src/pages/CreateEventPage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Calendar, MapPin, Users, Clock, Tag, FileText } from 'lucide-react';
import { createEvent, EVENT_CATEGORIES, EVENT_CATEGORY_LABELS } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import useTelegram from '../hooks/useTelegram';

const CreateEventPage = ({ user }) => {
  const navigate = useNavigate();
  const { showAlert, setBackButton, hideBackButton } = useTelegram();

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    short_description: '',
    category: 'other',
    tags: [],

    location: '',
    address: '',
    start_date: '',
    start_time: '',
    end_date: '',
    end_time: '',
    registration_deadline: '',

    max_volunteers: 10,
    min_volunteers: 1,

    required_skills: [],
    preferred_skills: [],
    min_age: '',
    max_age: '',
    requirements_description: '',

    what_to_bring: '',
    dress_code: '',
    meal_provided: false,
    transport_provided: false,

    contact_person: user?.full_name || '',
    contact_phone: user?.phone || '',
    contact_email: user?.email || ''
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [currentStep, setCurrentStep] = useState(1);

  const steps = [
    { id: 1, title: 'Основное', icon: FileText },
    { id: 2, title: 'Место и время', icon: Calendar },
    { id: 3, title: 'Участники', icon: Users },
    { id: 4, title: 'Детали', icon: Tag }
  ];

  const skillsOptions = [
    'Работа с детьми', 'Работа с пожилыми', 'Медицинские навыки', 'Психологическая поддержка',
    'Спортивная подготовка', 'Творческие навыки', 'Техническая поддержка', 'Переводы',
    'Фотография', 'Видеосъемка', 'Дизайн', 'Программирование', 'Кулинария', 'Вождение',
    'Музыкальные навыки', 'Педагогические навыки', 'Организаторские способности'
  ];

  React.useEffect(() => {
    setBackButton(() => navigate(-1));
    return () => hideBackButton();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Очистка ошибки
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleTagsChange = (e) => {
    const tags = e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag);
    setFormData(prev => ({ ...prev, tags }));
  };

  const handleSkillsChange = (skillType, skill) => {
    setFormData(prev => ({
      ...prev,
      [skillType]: prev[skillType].includes(skill)
        ? prev[skillType].filter(s => s !== skill)
        : [...prev[skillType], skill]
    }));
  };

  const validateStep = (step) => {
    const newErrors = {};

    switch (step) {
      case 1:
        if (!formData.title.trim()) newErrors.title = 'Название обязательно';
        if (!formData.description.trim()) newErrors.description = 'Описание обязательно';
        if (!formData.short_description.trim()) newErrors.short_description = 'Краткое описание обязательно';
        break;
      case 2:
        if (!formData.start_date) newErrors.start_date = 'Дата начала обязательна';
        if (!formData.start_time) newErrors.start_time = 'Время начала обязательно';
        if (!formData.end_date) newErrors.end_date = 'Дата окончания обязательна';
        if (!formData.end_time) newErrors.end_time = 'Время окончания обязательно';
        if (!formData.location.trim()) newErrors.location = 'Место проведения обязательно';

        // Проверка дат
        if (formData.start_date && formData.end_date) {
          const startDateTime = new Date(`${formData.start_date}T${formData.start_time}`);
          const endDateTime = new Date(`${formData.end_date}T${formData.end_time}`);
          if (startDateTime >= endDateTime) {
            newErrors.end_date = 'Дата окончания должна быть позже даты начала';
          }
        }
        break;
      case 3:
        if (formData.max_volunteers < formData.min_volunteers) {
          newErrors.max_volunteers = 'Максимум не может быть меньше минимума';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length));
    }
  };

  const handlePrev = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setLoading(true);

    try {
      // Формируем данные для отправки
      const eventData = {
        ...formData,
        start_date: new Date(`${formData.start_date}T${formData.start_time}`).toISOString(),
        end_date: new Date(`${formData.end_date}T${formData.end_time}`).toISOString(),
        registration_deadline: formData.registration_deadline
          ? new Date(formData.registration_deadline).toISOString()
          : null
      };

      const result = await createEvent(eventData);
      showAlert('Мероприятие создано успешно! 🎉');
      navigate(`/events/${result.id}`);

    } catch (error) {
      showAlert('Ошибка создания мероприятия: ' + error.message);
      setErrors({ general: error.message });
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="step-content">
            <h3 className="mb-4">📝 Основная информация</h3>

            <div className="form-group">
              <label htmlFor="title">Название мероприятия *</label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className={`form-control ${errors.title ? 'error' : ''}`}
                placeholder="Например: Уборка парка"
              />
              {errors.title && <span className="error-text">{errors.title}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="short_description">Краткое описание *</label>
              <input
                type="text"
                id="short_description"
                name="short_description"
                value={formData.short_description}
                onChange={handleChange}
                className={`form-control ${errors.short_description ? 'error' : ''}`}
                placeholder="Одной строкой - что это за мероприятие"
                maxLength="100"
              />
              {errors.short_description && <span className="error-text">{errors.short_description}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="description">Полное описание *</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                className={`form-control ${errors.description ? 'error' : ''}`}
                placeholder="Подробно опишите мероприятие, цели, задачи..."
                rows="5"
              />
              {errors.description && <span className="error-text">{errors.description}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="category">Категория</label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="form-control"
              >
                {Object.entries(EVENT_CATEGORY_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="tags">Теги (через запятую)</label>
              <input
                type="text"
                id="tags"
                name="tags"
                value={formData.tags.join(', ')}
                onChange={handleTagsChange}
                className="form-control"
                placeholder="экология, природа, уборка"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="step-content">
            <h3 className="mb-4">📍 Место и время</h3>

            <div className="form-group">
              <label htmlFor="location">Место проведения *</label>
              <input
                type="text"
                id="location"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className={`form-control ${errors.location ? 'error' : ''}`}
                placeholder="Центральный парк"
              />
              {errors.location && <span className="error-text">{errors.location}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="address">Адрес</label>
              <textarea
                id="address"
                name="address"
                value={formData.address}
                onChange={handleChange}
                className="form-control"
                placeholder="Полный адрес места проведения"
                rows="2"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="start_date">Дата начала *</label>
                <input
                  type="date"
                  id="start_date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleChange}
                  className={`form-control ${errors.start_date ? 'error' : ''}`}
                />
                {errors.start_date && <span className="error-text">{errors.start_date}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="start_time">Время начала *</label>
                <input
                  type="time"
                  id="start_time"
                  name="start_time"
                  value={formData.start_time}
                  onChange={handleChange}
                  className={`form-control ${errors.start_time ? 'error' : ''}`}
                />
                {errors.start_time && <span className="error-text">{errors.start_time}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="end_date">Дата окончания *</label>
                <input
                  type="date"
                  id="end_date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleChange}
                  className={`form-control ${errors.end_date ? 'error' : ''}`}
                />
                {errors.end_date && <span className="error-text">{errors.end_date}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="end_time">Время окончания *</label>
                <input
                  type="time"
                  id="end_time"
                  name="end_time"
                  value={formData.end_time}
                  onChange={handleChange}
                  className={`form-control ${errors.end_time ? 'error' : ''}`}
                />
                {errors.end_time && <span className="error-text">{errors.end_time}</span>}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="registration_deadline">Дедлайн регистрации</label>
              <input
                type="datetime-local"
                id="registration_deadline"
                name="registration_deadline"
                value={formData.registration_deadline}
                onChange={handleChange}
                className="form-control"
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="step-content">
            <h3 className="mb-4">👥 Участники</h3>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="min_volunteers">Минимум волонтеров</label>
                <input
                  type="number"
                  id="min_volunteers"
                  name="min_volunteers"
                  value={formData.min_volunteers}
                  onChange={handleChange}
                  className="form-control"
                  min="1"
                />
              </div>

              <div className="form-group">
                <label htmlFor="max_volunteers">Максимум волонтеров</label>
                <input
                  type="number"
                  id="max_volunteers"
                  name="max_volunteers"
                  value={formData.max_volunteers}
                  onChange={handleChange}
                  className={`form-control ${errors.max_volunteers ? 'error' : ''}`}
                  min="1"
                />
                {errors.max_volunteers && <span className="error-text">{errors.max_volunteers}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="min_age">Минимальный возраст</label>
                <input
                  type="number"
                  id="min_age"
                  name="min_age"
                  value={formData.min_age}
                  onChange={handleChange}
                  className="form-control"
                  min="14"
                  max="100"
                />
              </div>

              <div className="form-group">
                <label htmlFor="max_age">Максимальный возраст</label>
                <input
                  type="number"
                  id="max_age"
                  name="max_age"
                  value={formData.max_age}
                  onChange={handleChange}
                  className="form-control"
                  min="14"
                  max="100"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Обязательные навыки</label>
              <div className="skills-grid">
                {skillsOptions.map(skill => (
                  <label key={skill} className="skill-checkbox">
                    <input
                      type="checkbox"
                      checked={formData.required_skills.includes(skill)}
                      onChange={() => handleSkillsChange('required_skills', skill)}
                    />
                    <span>{skill}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Желательные навыки</label>
              <div className="skills-grid">
                {skillsOptions.map(skill => (
                  <label key={skill} className="skill-checkbox">
                    <input
                      type="checkbox"
                      checked={formData.preferred_skills.includes(skill)}
                      onChange={() => handleSkillsChange('preferred_skills', skill)}
                    />
                    <span>{skill}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="requirements_description">Дополнительные требования</label>
              <textarea
                id="requirements_description"
                name="requirements_description"
                value={formData.requirements_description}
                onChange={handleChange}
                className="form-control"
                placeholder="Особые требования к участникам..."
                rows="3"
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="step-content">
            <h3 className="mb-4">📋 Детали</h3>

            <div className="form-group">
              <label htmlFor="what_to_bring">Что брать с собой</label>
              <textarea
                id="what_to_bring"
                name="what_to_bring"
                value={formData.what_to_bring}
                onChange={handleChange}
                className="form-control"
                placeholder="Перчатки, удобная одежда, питьевая вода..."
                rows="3"
              />
            </div>

            <div className="form-group">
              <label htmlFor="dress_code">Дресс-код</label>
              <input
                type="text"
                id="dress_code"
                name="dress_code"
                value={formData.dress_code}
                onChange={handleChange}
                className="form-control"
                placeholder="Спортивная одежда, рабочая форма..."
              />
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  name="meal_provided"
                  checked={formData.meal_provided}
                  onChange={handleChange}
                />
                Питание предоставляется
              </label>
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  name="transport_provided"
                  checked={formData.transport_provided}
                  onChange={handleChange}
                />
                Транспорт предоставляется
              </label>
            </div>

            <h4 className="mb-3">Контактная информация</h4>

            <div className="form-group">
              <label htmlFor="contact_person">Контактное лицо</label>
              <input
                type="text"
                id="contact_person"
                name="contact_person"
                value={formData.contact_person}
                onChange={handleChange}
                className="form-control"
                placeholder="Имя ответственного"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="contact_phone">Телефон</label>
                <input
                  type="tel"
                  id="contact_phone"
                  name="contact_phone"
                  value={formData.contact_phone}
                  onChange={handleChange}
                  className="form-control"
                  placeholder="+7 (XXX) XXX-XX-XX"
                />
              </div>

              <div className="form-group">
                <label htmlFor="contact_email">Email</label>
                <input
                  type="email"
                  id="contact_email"
                  name="contact_email"
                  value={formData.contact_email}
                  onChange={handleChange}
                  className="form-control"
                  placeholder="contact@example.com"
                />
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return <LoadingSpinner message="Создание мероприятия..." />;
  }

  return (
    <div className="create-event-page">
      {/* Header */}
      <div className="page-header mb-4">
        <button onClick={() => navigate(-1)} className="btn btn-outline mb-3">
          <ArrowLeft size={16} /> Назад
        </button>
        <h2 className="mb-2">➕ Создать мероприятие</h2>
        <p className="text-muted">Заполните информацию о вашем мероприятии</p>
      </div>

      {/* Progress Bar */}
      <div className="progress-section mb-4">
        <div className="steps-indicator">
          {steps.map(step => (
            <div
              key={step.id}
              className={`step-indicator ${currentStep >= step.id ? 'active' : ''} ${currentStep === step.id ? 'current' : ''}`}
            >
              <div className="step-number">{step.id}</div>
              <div className="step-title">{step.title}</div>
            </div>
          ))}
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${(currentStep / steps.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Step Content */}
      <div className="form-container">
        {renderStep()}

        {errors.general && (
          <div className="error-message mb-4">
            {errors.general}
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="form-buttons">
          <div className="buttons-left">
            {currentStep > 1 && (
              <button
                type="button"
                onClick={handlePrev}
                className="btn btn-secondary"
                disabled={loading}
              >
                ← Назад
              </button>
            )}
          </div>

          <div className="buttons-right">
            {currentStep < steps.length ? (
              <button
                type="button"
                onClick={handleNext}
                className="btn btn-primary"
                disabled={loading}
              >
                Далее →
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Создание...' : 'Создать мероприятие'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateEventPage;