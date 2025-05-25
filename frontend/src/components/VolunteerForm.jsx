import React, { useState } from 'react';
import { createVolunteer, updateVolunteer } from '../services/api';

const VolunteerForm = ({ volunteer = null, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    first_name: volunteer?.first_name || '',
    last_name: volunteer?.last_name || '',
    middle_name: volunteer?.middle_name || '',
    email: volunteer?.email || '',
    phone: volunteer?.phone || '',
    birth_date: volunteer?.birth_date || '',
    address: volunteer?.address || '',
    skills: volunteer?.skills?.join(', ') || '',
    experience: volunteer?.experience || '',
    emergency_contact: volunteer?.emergency_contact || '',
    emergency_phone: volunteer?.emergency_phone || '',
    notes: volunteer?.notes || ''
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Очистка ошибки при изменении поля
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'Имя обязательно';
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Фамилия обязательна';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email обязателен';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Некорректный email';
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'Телефон обязателен';
    }

    if (!formData.birth_date) {
      newErrors.birth_date = 'Дата рождения обязательна';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const submitData = {
        ...formData,
        skills: formData.skills.split(',').map(s => s.trim()).filter(s => s)
      };

      let result;
      if (volunteer) {
        result = await updateVolunteer(volunteer.id, submitData);
      } else {
        result = await createVolunteer(submitData);
      }

      onSave(result);

      // Показываем уведомление в Telegram
      if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.showAlert(
          volunteer ? 'Данные волонтера обновлены!' : 'Волонтер успешно зарегистрирован!'
        );
      }

    } catch (error) {
      setErrors({ general: error.message });

      if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.showAlert('Ошибка: ' + error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="volunteer-form">
      <div className="form-section">
        <h3>Основная информация</h3>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="first_name">Имя *</label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              className={errors.first_name ? 'error' : ''}
              placeholder="Введите имя"
            />
            {errors.first_name && <span className="error-text">{errors.first_name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="last_name">Фамилия *</label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              className={errors.last_name ? 'error' : ''}
              placeholder="Введите фамилию"
            />
            {errors.last_name && <span className="error-text">{errors.last_name}</span>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="middle_name">Отчество</label>
          <input
            type="text"
            id="middle_name"
            name="middle_name"
            value={formData.middle_name}
            onChange={handleChange}
            placeholder="Введите отчество"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={errors.email ? 'error' : ''}
              placeholder="example@email.com"
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
              className={errors.phone ? 'error' : ''}
              placeholder="+7 (XXX) XXX-XX-XX"
            />
            {errors.phone && <span className="error-text">{errors.phone}</span>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="birth_date">Дата рождения *</label>
          <input
            type="date"
            id="birth_date"
            name="birth_date"
            value={formData.birth_date}
            onChange={handleChange}
            className={errors.birth_date ? 'error' : ''}
          />
          {errors.birth_date && <span className="error-text">{errors.birth_date}</span>}
        </div>
      </div>

      <div className="form-section">
        <h3>Дополнительная информация</h3>

        <div className="form-group">
          <label htmlFor="address">Адрес</label>
          <textarea
            id="address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            placeholder="Адрес проживания"
            rows="2"
          />
        </div>

        <div className="form-group">
          <label htmlFor="skills">Навыки</label>
          <input
            type="text"
            id="skills"
            name="skills"
            value={formData.skills}
            onChange={handleChange}
            placeholder="Навыки через запятую"
          />
        </div>

        <div className="form-group">
          <label htmlFor="experience">Опыт</label>
          <textarea
            id="experience"
            name="experience"
            value={formData.experience}
            onChange={handleChange}
            placeholder="Опыт волонтерской работы"
            rows="3"
          />
        </div>
      </div>

      <div className="form-section">
        <h3>Экстренные контакты</h3>

        <div className="form-group">
          <label htmlFor="emergency_contact">Контактное лицо</label>
          <input
            type="text"
            id="emergency_contact"
            name="emergency_contact"
            value={formData.emergency_contact}
            onChange={handleChange}
            placeholder="ФИО контактного лица"
          />
        </div>

        <div className="form-group">
          <label htmlFor="emergency_phone">Телефон</label>
          <input
            type="tel"
            id="emergency_phone"
            name="emergency_phone"
            value={formData.emergency_phone}
            onChange={handleChange}
            placeholder="+7 (XXX) XXX-XX-XX"
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="notes">Заметки</label>
        <textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          placeholder="Дополнительные заметки"
          rows="3"
        />
      </div>

      {errors.general && (
        <div className="error-message">
          {errors.general}
        </div>
      )}

      <div className="form-buttons">
        <button
          type="button"
          onClick={onCancel}
          className="btn btn-secondary"
          disabled={loading}
        >
          Отмена
        </button>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Сохранение...' : (volunteer ? 'Обновить' : 'Создать')}
        </button>
      </div>
    </form>
  );
};

export default VolunteerForm;