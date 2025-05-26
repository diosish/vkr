import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';
import useTelegram from '../hooks/useTelegram';

const RegisterPage = () => {
  const { user, setUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { showAlert } = useTelegram();

  const [formData, setFormData] = useState({
    role: 'volunteer',
    email: '',
    phone: '',
    bio: '',
    location: '',
    // Данные организации
    organization_name: '',
    inn: '',
    ogrn: '',
    org_contact_name: '',
    org_phone: '',
    org_email: '',
    org_address: '',
    // Данные волонтера
    middle_name: '',
    birth_date: '',
    gender: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relation: '',
    education: '',
    occupation: '',
    organization: '',
    experience_description: '',
    travel_willingness: false,
    max_travel_distance: 50,
    preferred_activities: []
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/auth/complete-registration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Ошибка при регистрации');
      }

      const data = await response.json();
      setUser(data);
      showAlert('Регистрация успешно завершена! ✅');
      navigate('/');
    } catch (error) {
      console.error('Ошибка регистрации:', error);
      setError(error.message);
      showAlert('Ошибка регистрации: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Регистрация..." />;
  }

  return (
    <div className="register-page">
      <div className="card">
        <div className="card-header">
          <h2>Завершение регистрации</h2>
          <p className="text-muted">Пожалуйста, заполните необходимые данные</p>
        </div>
        <div className="card-body">
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group mb-3">
              <label>Роль</label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="form-control"
              >
                <option value="volunteer">Волонтер</option>
                <option value="organizer">Организатор</option>
              </select>
            </div>

            <div className="form-group mb-3">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="form-control"
                required
              />
            </div>

            <div className="form-group mb-3">
              <label>Телефон</label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="form-control"
                required
              />
            </div>

            <div className="form-group mb-3">
              <label>О себе</label>
              <textarea
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                className="form-control"
                rows={3}
              />
            </div>

            <div className="form-group mb-3">
              <label>Местоположение</label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="form-control"
              />
            </div>

            {formData.role === 'organizer' && (
              <>
                <h4 className="mt-4 mb-3">Данные организации</h4>
                <div className="form-group mb-3">
                  <label>Название организации</label>
                  <input
                    type="text"
                    name="organization_name"
                    value={formData.organization_name}
                    onChange={handleChange}
                    className="form-control"
                    required
                  />
                </div>

                <div className="form-group mb-3">
                  <label>ИНН</label>
                  <input
                    type="text"
                    name="inn"
                    value={formData.inn}
                    onChange={handleChange}
                    className="form-control"
                    required
                  />
                </div>

                <div className="form-group mb-3">
                  <label>ОГРН</label>
                  <input
                    type="text"
                    name="ogrn"
                    value={formData.ogrn}
                    onChange={handleChange}
                    className="form-control"
                    required
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Контактное лицо</label>
                  <input
                    type="text"
                    name="org_contact_name"
                    value={formData.org_contact_name}
                    onChange={handleChange}
                    className="form-control"
                    required
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Телефон организации</label>
                  <input
                    type="tel"
                    name="org_phone"
                    value={formData.org_phone}
                    onChange={handleChange}
                    className="form-control"
                    required
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Email организации</label>
                  <input
                    type="email"
                    name="org_email"
                    value={formData.org_email}
                    onChange={handleChange}
                    className="form-control"
                    required
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Юридический адрес</label>
                  <input
                    type="text"
                    name="org_address"
                    value={formData.org_address}
                    onChange={handleChange}
                    className="form-control"
                    required
                  />
                </div>
              </>
            )}

            {formData.role === 'volunteer' && (
              <>
                <h4 className="mt-4 mb-3">Данные волонтера</h4>
                <div className="form-group mb-3">
                  <label>Отчество</label>
                  <input
                    type="text"
                    name="middle_name"
                    value={formData.middle_name}
                    onChange={handleChange}
                    className="form-control"
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Дата рождения</label>
                  <input
                    type="date"
                    name="birth_date"
                    value={formData.birth_date}
                    onChange={handleChange}
                    className="form-control"
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Пол</label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    className="form-control"
                  >
                    <option value="">Выберите</option>
                    <option value="male">Мужской</option>
                    <option value="female">Женский</option>
                  </select>
                </div>

                <h5 className="mt-4 mb-3">Экстренные контакты</h5>
                <div className="form-group mb-3">
                  <label>Имя контактного лица</label>
                  <input
                    type="text"
                    name="emergency_contact_name"
                    value={formData.emergency_contact_name}
                    onChange={handleChange}
                    className="form-control"
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Телефон контактного лица</label>
                  <input
                    type="tel"
                    name="emergency_contact_phone"
                    value={formData.emergency_contact_phone}
                    onChange={handleChange}
                    className="form-control"
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Отношение</label>
                  <input
                    type="text"
                    name="emergency_contact_relation"
                    value={formData.emergency_contact_relation}
                    onChange={handleChange}
                    className="form-control"
                  />
                </div>

                <h5 className="mt-4 mb-3">Профессиональные данные</h5>
                <div className="form-group mb-3">
                  <label>Образование</label>
                  <input
                    type="text"
                    name="education"
                    value={formData.education}
                    onChange={handleChange}
                    className="form-control"
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Профессия</label>
                  <input
                    type="text"
                    name="occupation"
                    value={formData.occupation}
                    onChange={handleChange}
                    className="form-control"
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Место работы/учебы</label>
                  <input
                    type="text"
                    name="organization"
                    value={formData.organization}
                    onChange={handleChange}
                    className="form-control"
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Опыт волонтерства</label>
                  <textarea
                    name="experience_description"
                    value={formData.experience_description}
                    onChange={handleChange}
                    className="form-control"
                    rows={3}
                  />
                </div>

                <div className="form-group mb-3">
                  <div className="form-check">
                    <input
                      type="checkbox"
                      name="travel_willingness"
                      checked={formData.travel_willingness}
                      onChange={handleChange}
                      className="form-check-input"
                    />
                    <label className="form-check-label">
                      Готов к поездкам
                    </label>
                  </div>
                </div>

                {formData.travel_willingness && (
                  <div className="form-group mb-3">
                    <label>Максимальное расстояние (км)</label>
                    <input
                      type="number"
                      name="max_travel_distance"
                      value={formData.max_travel_distance}
                      onChange={handleChange}
                      className="form-control"
                      min="0"
                      max="1000"
                    />
                  </div>
                )}
              </>
            )}

            <div className="form-buttons mt-4">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? 'Регистрация...' : 'Завершить регистрацию'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage; 