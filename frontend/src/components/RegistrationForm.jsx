// frontend/src/components/RegistrationForm.jsx
import React, { useState } from 'react';
import { User, Phone, Mail, Calendar, MapPin, Briefcase, Heart, Globe } from 'lucide-react';
import useTelegram from '../hooks/useTelegram';

const RegistrationForm = ({ user, onComplete, onSkip }) => {
  const [formData, setFormData] = useState({
    // Основные данные
    email: '',
    phone: '',
    bio: '',
    location: '',

    // Профиль волонтера
    middle_name: '',
    birth_date: '',
    gender: '',

    // Экстренные контакты
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relation: '',

    // Профессиональные данные
    education: '',
    occupation: '',
    organization: '',

    // Навыки и интересы
    skills: [],
    interests: [],
    languages: ['ru'],
    experience_description: '',

    // Доступность
    travel_willingness: false,
    max_travel_distance: 50,
    preferred_activities: []
  });

  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const { showAlert } = useTelegram();

  const steps = [
    { id: 1, title: 'Основная информация', icon: User },
    { id: 2, title: 'Личные данные', icon: Calendar },
    { id: 3, title: 'Экстренные контакты', icon: Phone },
    { id: 4, title: 'Опыт и навыки', icon: Briefcase },
    { id: 5, title: 'Интересы', icon: Heart }
  ];

  const skillsOptions = [
    'Работа с детьми', 'Работа с пожилыми', 'Медицинские навыки', 'Психологическая поддержка',
    'Спортивная подготовка', 'Творческие навыки', 'Техническая поддержка', 'Переводы',
    'Фотография', 'Видеосъемка', 'Дизайн', 'Программирование', 'Кулинария', 'Вождение',
    'Музыкальные навыки', 'Педагогические навыки', 'Организаторские способности'
  ];

  const interestsOptions = [
    'Экология', 'Социальная помощь', 'Образование', 'Здравоохранение', 'Культура',
    'Спорт', 'Животные', 'Пожилые люди', 'Дети', 'Люди с ОВЗ', 'Бездомные',
    'Беженцы', 'Природа', 'Искусство', 'Технологии', 'Наука'
  ];

  const preferredActivitiesOptions = [
    'Разовые мероприятия', 'Регулярная помощь', 'Выездные мероприятия', 'Офисная работа',
    'Физическая работа', 'Интеллектуальная работа', 'Работа в команде', 'Индивидуальная работа',
    'Работа с документами', 'Публичные выступления', 'Консультирование'
  ];

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

  const handleMultiSelect = (name, value) => {
    setFormData(prev => ({
      ...prev,
      [name]: prev[name].includes(value)
        ? prev[name].filter(item => item !== value)
        : [...prev[name], value]
    }));
  };

  const validateStep = (step) => {
    const newErrors = {};

    switch (step) {
      case 1:
        if (!formData.email.trim()) {
          newErrors.email = 'Email обязателен';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
          newErrors.email = 'Некорректный email';
        }
        if (!formData.phone.trim()) {
          newErrors.phone = 'Телефон обязателен';
        }
        break;
      case 2:
        if (!formData.birth_date) {
          newErrors.birth_date = 'Дата рождения обязательна';
        }
        break;
      case 3:
        if (!formData.emergency_contact_name.trim()) {
          newErrors.emergency_contact_name = 'Имя контактного лица обязательно';
        }
        if (!formData.emergency_contact_phone.trim()) {
          newErrors.emergency_contact_phone = 'Телефон контактного лица обязателен';
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
      const response = await fetch('/api/auth/complete-registration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Ошибка регистрации');
      }

      const userData = await response.json();
      showAlert('Регистрация завершена успешно! 🎉');
      onComplete(userData);

    } catch (error) {
      showAlert('Ошибка: ' + error.message);
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
            <h3 className="mb-4">📧 Основная информация</h3>

            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`form-control ${errors.email ? 'error' : ''}`}
                placeholder="your@example.com"
              />
              {errors.email && <span className="error-text">{errors.email}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="phone">Телефон *</label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className={`form-control ${errors.phone ? 'error' : ''}`}
                placeholder="+7 (XXX) XXX-XX-XX"
              />
              {errors.phone && <span className="error-text">{errors.phone}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="location">Город</label>
              <input
                type="text"
                id="location"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="form-control"
                placeholder="Ваш город"
              />
            </div>

            <div className="form-group">
              <label htmlFor="bio">О себе</label>
              <textarea
                id="bio"
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                className="form-control"
                placeholder="Расскажите о себе..."
                rows="3"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="step-content">
            <h3 className="mb-4">👤 Личные данные</h3>

            <div className="form-group">
              <label htmlFor="middle_name">Отчество</label>
              <input
                type="text"
                id="middle_name"
                name="middle_name"
                value={formData.middle_name}
                onChange={handleChange}
                className="form-control"
                placeholder="Введите отчество"
              />
            </div>

            <div className="form-group">
              <label htmlFor="birth_date">Дата рождения *</label>
              <input
                type="date"
                id="birth_date"
                name="birth_date"
                value={formData.birth_date}
                onChange={handleChange}
                className={`form-control ${errors.birth_date ? 'error' : ''}`}
              />
              {errors.birth_date && <span className="error-text">{errors.birth_date}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="gender">Пол</label>
              <select
                id="gender"
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="form-control"
              >
                <option value="">Выберите</option>
                <option value="male">Мужской</option>
                <option value="female">Женский</option>
                <option value="other">Другой</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="education">Образование</label>
              <input
                type="text"
                id="education"
                name="education"
                value={formData.education}
                onChange={handleChange}
                className="form-control"
                placeholder="Ваше образование"
              />
            </div>

            <div className="form-group">
              <label htmlFor="occupation">Профессия</label>
              <input
                type="text"
                id="occupation"
                name="occupation"
                value={formData.occupation}
                onChange={handleChange}
                className="form-control"
                placeholder="Чем занимаетесь"
              />
            </div>
          </div>
        );

      case 3:
        return (
          <div className="step-content">
            <h3 className="mb-4">🚨 Экстренные контакты</h3>

            <div className="form-group">
              <label htmlFor="emergency_contact_name">Контактное лицо *</label>
              <input
                type="text"
                id="emergency_contact_name"
                name="emergency_contact_name"
                value={formData.emergency_contact_name}
                onChange={handleChange}
                className={`form-control ${errors.emergency_contact_name ? 'error' : ''}`}
                placeholder="ФИО контактного лица"
              />
              {errors.emergency_contact_name && <span className="error-text">{errors.emergency_contact_name}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="emergency_contact_phone">Телефон контакта *</label>
              <input
                type="tel"
                id="emergency_contact_phone"
                name="emergency_contact_phone"
                value={formData.emergency_contact_phone}
                onChange={handleChange}
                className={`form-control ${errors.emergency_contact_phone ? 'error' : ''}`}
                placeholder="+7 (XXX) XXX-XX-XX"
              />
              {errors.emergency_contact_phone && <span className="error-text">{errors.emergency_contact_phone}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="emergency_contact_relation">Степень родства</label>
              <select
                id="emergency_contact_relation"
                name="emergency_contact_relation"
                value={formData.emergency_contact_relation}
                onChange={handleChange}
                className="form-control"
              >
                <option value="">Выберите</option>
                <option value="parent">Родитель</option>
                <option value="spouse">Супруг(а)</option>
                <option value="sibling">Брат/Сестра</option>
                <option value="child">Ребенок</option>
                <option value="friend">Друг</option>
                <option value="relative">Родственник</option>
                <option value="other">Другое</option>
              </select>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="step-content">
            <h3 className="mb-4">💼 Опыт и навыки</h3>

            <div className="form-group">
              <label>Навыки</label>
              <div className="skills-grid">
                {skillsOptions.map(skill => (
                  <label key={skill} className="skill-checkbox">
                    <input
                      type="checkbox"
                      checked={formData.skills.includes(skill)}
                      onChange={() => handleMultiSelect('skills', skill)}
                    />
                    <span>{skill}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="experience_description">Опыт волонтерства</label>
              <textarea
                id="experience_description"
                name="experience_description"
                value={formData.experience_description}
                onChange={handleChange}
                className="form-control"
                placeholder="Расскажите о своем опыте волонтерской работы..."
                rows="4"
              />
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  name="travel_willingness"
                  checked={formData.travel_willingness}
                  onChange={handleChange}
                />
                Готов(а) к выездным мероприятиям
              </label>
            </div>

            {formData.travel_willingness && (
              <div className="form-group">
                <label htmlFor="max_travel_distance">Максимальное расстояние (км)</label>
                <input
                  type="number"
                  id="max_travel_distance"
                  name="max_travel_distance"
                  value={formData.max_travel_distance}
                  onChange={handleChange}
                  className="form-control"
                  min="1"
                  max="1000"
                />
              </div>
            )}
          </div>
        );

      case 5:
        return (
          <div className="step-content">
            <h3 className="mb-4">❤️ Интересы и предпочтения</h3>

            <div className="form-group">
              <label>Области интересов</label>
              <div className="interests-grid">
                {interestsOptions.map(interest => (
                  <label key={interest} className="interest-checkbox">
                    <input
                      type="checkbox"
                      checked={formData.interests.includes(interest)}
                      onChange={() => handleMultiSelect('interests', interest)}
                    />
                    <span>{interest}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Предпочитаемые виды деятельности</label>
              <div className="activities-grid">
                {preferredActivitiesOptions.map(activity => (
                  <label key={activity} className="activity-checkbox">
                    <input
                      type="checkbox"
                      checked={formData.preferred_activities.includes(activity)}
                      onChange={() => handleMultiSelect('preferred_activities', activity)}
                    />
                    <span>{activity}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="registration-form">
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
                ←  Назад
              </button>
            )}
          </div>

          <div className="buttons-right">
            {onSkip && currentStep === 1 && (
              <button
                type="button"
                onClick={onSkip}
                className="btn btn-outline"
                disabled={loading}
              >
                Пропустить
              </button>
            )}

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
                {loading ? 'Сохранение...' : 'Завершить регистрацию'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegistrationForm;