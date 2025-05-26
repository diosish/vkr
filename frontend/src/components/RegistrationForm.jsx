// frontend/src/components/RegistrationForm.jsx
import React, { useState } from 'react';
import { User, Phone, Mail, Calendar, MapPin, Briefcase, Heart, Globe } from 'lucide-react';
import useTelegram from '../hooks/useTelegram';
import { completeRegistration } from '../services/api';
import { refreshUserData } from '../services/auth';

const RegistrationForm = ({ user, onComplete, onSkip }) => {
  const [formData, setFormData] = useState({
    // Основные данные
    email: '',
    phone: '',
    bio: '',
    location: '',
    role: 'volunteer',

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
    experience_description: '',

    // Доступность
    travel_willingness: false,
    max_travel_distance: 50,
    preferred_activities: [],

    // Данные организации
    organization_name: '',
    inn: '',
    ogrn: '',
    org_contact_name: '',
    org_phone: '',
    org_email: '',
    org_address: '',
  });

  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const { showAlert } = useTelegram();

  const steps = [
    { id: 1, title: 'Основная информация', icon: User },
    { id: 2, title: 'Личные данные', icon: Calendar },
    { id: 3, title: 'Экстренные контакты', icon: Phone },
    { id: 4, title: 'Опыт и предпочтения', icon: Briefcase }
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
    if (formData.role === 'organizer') {
      if (!formData.organization_name || !formData.organization_name.trim()) newErrors.organization_name = 'Название организации обязательно';
      if (!formData.inn || !formData.inn.trim()) newErrors.inn = 'ИНН обязателен';
      if (!formData.org_contact_name || !formData.org_contact_name.trim()) newErrors.org_contact_name = 'Контактное лицо обязательно';
      if (!formData.org_phone || !formData.org_phone.trim()) newErrors.org_phone = 'Телефон обязателен';
      if (!formData.org_email || !formData.org_email.trim()) {
        newErrors.org_email = 'Email обязателен';
      } else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(formData.org_email)) {
        newErrors.org_email = 'Некорректный email';
      }
      setErrors(newErrors);
      return Object.keys(newErrors).length === 0;
    }
    if (formData.role === 'admin') {
      setErrors({});
      return true;
    }
    // volunteer
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

  const nullifyEmptyStrings = (obj) => {
    return Object.fromEntries(
      Object.entries(obj).map(([k, v]) =>
        typeof v === 'string' && v.trim() === '' ? [k, null] : [k, v]
      )
    );
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;
    setLoading(true);
    try {
      const cleanData = nullifyEmptyStrings(formData);
      const userData = await completeRegistration(cleanData);
      
      if (userData) {
        // Обновляем данные пользователя
        const updatedUser = await refreshUserData(window.Telegram?.WebApp?.initData);
        if (updatedUser) {
          showAlert('Регистрация завершена успешно! 🎉');
          onComplete(updatedUser);
        } else {
          onComplete(userData);
        }
      }
    } catch (error) {
      showAlert('Ошибка: ' + error.message);
      setErrors({ general: error.message });
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    // Всегда первым — выбор типа пользователя
    const roleSelect = (
      <div className="form-group">
        <label htmlFor="role">Тип пользователя *</label>
        <select id="role" name="role" value={formData.role} onChange={handleChange} className="form-control">
          <option value="volunteer">Волонтёр</option>
          <option value="organizer">Организатор</option>
          <option value="admin">Администратор</option>
        </select>
      </div>
    );
    if (formData.role === 'admin') {
      return (
        <div className="step-content">
          {roleSelect}
          <h3 className="mb-4">🔧 Администратор</h3>
          <p>После регистрации вы попадёте в административную панель.</p>
        </div>
      );
    }
    if (formData.role === 'organizer') {
      return (
        <div className="step-content">
          {roleSelect}
          <h3 className="mb-4">Данные организации</h3>
          <div className="form-group">
            <label htmlFor="organization_name">Название организации *</label>
            <input type="text" id="organization_name" name="organization_name" value={formData.organization_name || ''} onChange={handleChange} className="form-control" required />
          </div>
          <div className="form-group">
            <label htmlFor="inn">ИНН *</label>
            <input type="text" id="inn" name="inn" value={formData.inn || ''} onChange={handleChange} className="form-control" required />
          </div>
          <div className="form-group">
            <label htmlFor="ogrn">ОГРН</label>
            <input type="text" id="ogrn" name="ogrn" value={formData.ogrn || ''} onChange={handleChange} className="form-control" />
          </div>
          <div className="form-group">
            <label htmlFor="org_contact_name">Контактное лицо *</label>
            <input type="text" id="org_contact_name" name="org_contact_name" value={formData.org_contact_name || ''} onChange={handleChange} className="form-control" required />
          </div>
          <div className="form-group">
            <label htmlFor="org_phone">Телефон организации *</label>
            <input type="tel" id="org_phone" name="org_phone" value={formData.org_phone || ''} onChange={handleChange} className="form-control" required />
          </div>
          <div className="form-group">
            <label htmlFor="org_email">Email организации *</label>
            <input type="email" id="org_email" name="org_email" value={formData.org_email || ''} onChange={handleChange} className="form-control" required />
          </div>
          <div className="form-group">
            <label htmlFor="org_address">Юридический адрес</label>
            <input type="text" id="org_address" name="org_address" value={formData.org_address || ''} onChange={handleChange} className="form-control" />
          </div>
        </div>
      );
    }
    // VOLUNTEER
    switch (currentStep) {
      case 1:
        return (
          <div className="step-content">
            {roleSelect}
            <h3 className="mb-4">📧 Основная информация</h3>
            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} className={`form-control ${errors.email ? 'error' : ''}`} placeholder="your@example.com" />
              {errors.email && <span className="error-text">{errors.email}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="phone">Телефон *</label>
              <input type="tel" id="phone" name="phone" value={formData.phone} onChange={handleChange} className={`form-control ${errors.phone ? 'error' : ''}`} placeholder="+7 (XXX) XXX-XX-XX" />
              {errors.phone && <span className="error-text">{errors.phone}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="location">Город</label>
              <input type="text" id="location" name="location" value={formData.location} onChange={handleChange} className="form-control" placeholder="Ваш город" />
            </div>
            <div className="form-group">
              <label htmlFor="bio">О себе</label>
              <textarea id="bio" name="bio" value={formData.bio} onChange={handleChange} className="form-control" placeholder="Расскажите о себе..." rows="3" />
            </div>
          </div>
        );
      case 2:
        return (
          <div className="step-content">
            {roleSelect}
            <h3 className="mb-4">👤 Личные данные</h3>
            <div className="form-group">
              <label htmlFor="middle_name">Отчество</label>
              <input type="text" id="middle_name" name="middle_name" value={formData.middle_name} onChange={handleChange} className="form-control" placeholder="Введите отчество" />
            </div>
            <div className="form-group">
              <label htmlFor="birth_date">Дата рождения *</label>
              <input type="date" id="birth_date" name="birth_date" value={formData.birth_date} onChange={handleChange} className={`form-control ${errors.birth_date ? 'error' : ''}`} />
              {errors.birth_date && <span className="error-text">{errors.birth_date}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="gender">Пол</label>
              <select id="gender" name="gender" value={formData.gender} onChange={handleChange} className="form-control">
                <option value="">Выберите</option>
                <option value="male">Мужской</option>
                <option value="female">Женский</option>
              </select>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="step-content">
            {roleSelect}
            <h3 className="mb-4">🚨 Экстренные контакты</h3>
            <div className="form-group">
              <label htmlFor="emergency_contact_name">Контактное лицо *</label>
              <input type="text" id="emergency_contact_name" name="emergency_contact_name" value={formData.emergency_contact_name} onChange={handleChange} className={`form-control ${errors.emergency_contact_name ? 'error' : ''}`} placeholder="ФИО контактного лица" />
              {errors.emergency_contact_name && <span className="error-text">{errors.emergency_contact_name}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="emergency_contact_phone">Телефон контакта *</label>
              <input type="tel" id="emergency_contact_phone" name="emergency_contact_phone" value={formData.emergency_contact_phone} onChange={handleChange} className={`form-control ${errors.emergency_contact_phone ? 'error' : ''}`} placeholder="+7 (XXX) XXX-XX-XX" />
              {errors.emergency_contact_phone && <span className="error-text">{errors.emergency_contact_phone}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="emergency_contact_relation">Степень родства</label>
              <select id="emergency_contact_relation" name="emergency_contact_relation" value={formData.emergency_contact_relation} onChange={handleChange} className="form-control">
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
            {roleSelect}
            <h3 className="mb-4">💼 Опыт и предпочтения</h3>
            <div className="form-group">
              <label htmlFor="experience_description">Опыт волонтерства</label>
              <textarea id="experience_description" name="experience_description" value={formData.experience_description} onChange={handleChange} className="form-control" placeholder="Расскажите о своем опыте волонтерской работы..." rows="4" />
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
      {formData.role === 'volunteer' && (
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
      )}
      {/* Step Content */}
      <div className="form-container">
        {renderStep()}
        {errors.general && (
          <div className="error-message mb-4">{errors.general}</div>
        )}
        {/* Navigation Buttons только для volunteer */}
        {formData.role === 'volunteer' && (
          <div className="form-buttons">
            <div className="buttons-left">
              {currentStep > 1 && (
                <button type="button" onClick={handlePrev} className="btn btn-secondary" disabled={loading}>
                  ←  Назад
                </button>
              )}
            </div>
            <div className="buttons-right">
              {onSkip && currentStep === 1 && (
                <button type="button" onClick={onSkip} className="btn btn-outline" disabled={loading}>
                  Пропустить
                </button>
              )}
              {currentStep < steps.length ? (
                <button type="button" onClick={handleNext} className="btn btn-primary" disabled={loading}>
                  Далее →
                </button>
              ) : (
                <button type="button" onClick={handleSubmit} className="btn btn-primary" disabled={loading}>
                  {loading ? 'Сохранение...' : 'Завершить регистрацию'}
                </button>
              )}
            </div>
          </div>
        )}
        {/* Для organizer — одна кнопка регистрации */}
        {formData.role === 'organizer' && (
          <div className="form-buttons">
            <button type="button" onClick={handleSubmit} className="btn btn-primary" disabled={loading}>
              {loading ? 'Сохранение...' : 'Зарегистрироваться'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RegistrationForm;