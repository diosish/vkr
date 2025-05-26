// frontend/src/pages/ProfilePage.jsx
import React, { useState, useEffect } from 'react';
import { User, Edit, Save, X, Phone, Mail, MapPin, Calendar, Award, Heart } from 'lucide-react';
import { updateProfile, getCurrentUser } from '../services/api';
import { saveAuthData, getAuthData, clearAuthData } from '../services/auth';
import LoadingSpinner from '../components/LoadingSpinner';
import useTelegram from '../hooks/useTelegram';
import { useNavigate } from 'react-router-dom';

const ProfilePage = ({ user, setUser }) => {
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});
  const { showAlert } = useTelegram();
  const navigate = useNavigate();

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

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email || '',
        phone: user.phone || '',
        bio: user.bio || '',
        location: user.location || '',
        middle_name: user.middle_name || '',
        birth_date: user.birth_date || '',
        gender: user.gender || '',
        emergency_contact_name: user.emergency_contact_name || '',
        emergency_contact_phone: user.emergency_contact_phone || '',
        emergency_contact_relation: user.emergency_contact_relation || '',
        education: user.education || '',
        occupation: user.occupation || '',
        organization: user.organization || '',
        skills: user.skills || [],
        interests: user.interests || [],
        languages: user.languages || ['ru'],
        experience_description: user.experience_description || '',
        travel_willingness: user.travel_willingness || false,
        max_travel_distance: user.max_travel_distance || 50,
        preferred_activities: user.preferred_activities || []
      });
    }
  }, [user]);

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

  const handleSave = async () => {
    setSaving(true);
    setErrors({});

    try {
      const updatedUser = await updateProfile(formData);
      setUser(updatedUser);
      // Сохраняем в localStorage
      const prevAuth = getAuthData();
      if (prevAuth) saveAuthData({ ...prevAuth, user: updatedUser });
      setEditMode(false);
      showAlert('Профиль обновлен! ✅');
    } catch (error) {
      showAlert('Ошибка обновления профиля: ' + error.message);
      setErrors({ general: error.message });
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditMode(false);
    setErrors({});
    // Восстанавливаем данные из пропса user
    if (user) {
      setFormData({
        email: user.email || '',
        phone: user.phone || '',
        bio: user.bio || '',
        location: user.location || '',
        middle_name: user.middle_name || '',
        birth_date: user.birth_date || '',
        gender: user.gender || '',
        emergency_contact_name: user.emergency_contact_name || '',
        emergency_contact_phone: user.emergency_contact_phone || '',
        emergency_contact_relation: user.emergency_contact_relation || '',
        education: user.education || '',
        occupation: user.occupation || '',
        organization: user.organization || '',
        skills: user.skills || [],
        interests: user.interests || [],
        languages: user.languages || ['ru'],
        experience_description: user.experience_description || '',
        travel_willingness: user.travel_willingness || false,
        max_travel_distance: user.max_travel_distance || 50,
        preferred_activities: user.preferred_activities || []
      });
    }
  };

  const getCompletionPercentage = () => {
    const fields = [
      formData.email, formData.phone, formData.birth_date,
      formData.emergency_contact_name, formData.emergency_contact_phone,
      formData.education, formData.skills.length > 0, formData.experience_description
    ];
    const filledFields = fields.filter(field => field).length;
    return Math.round((filledFields / fields.length) * 100);
  };

  const handleDeleteProfile = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить профиль? Это действие необратимо!')) return;
    try {
      const response = await fetch('/api/auth/delete-profile', {
        method: 'DELETE',
        headers: {
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        }
      });
      if (!response.ok) throw new Error('Ошибка удаления профиля');
      setUser(null);
      clearAuthData();
      navigate('/');
    } catch (e) {
      alert('Ошибка удаления профиля: ' + e.message);
    }
  };

  // --- Альтернативный рендеринг для organizer ---
  if (user?.role === 'organizer') {
    console.log('ORGANIZER USER:', user);
    return (
      <div className="profile-page">
        <div className="profile-header card mb-4">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div className="avatar" style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: 'var(--tg-button-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px', color: 'white' }}>
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', borderRadius: '50%' }} />
              ) : (
                <User size={40} />
              )}
            </div>
            <div>
              <h2 className="mb-1">{user?.first_name} {user?.last_name}</h2>
              <p className="text-muted mb-1">@{user?.telegram_username || 'organizer'}</p>
              <p className="text-muted font-small">👔 Организатор</p>
            </div>
          </div>
        </div>
        <div className="card mb-4">
          <h3 className="mb-3">🏢 Данные организации</h3>
          <div className="form-group"><b>Название:</b> {user.organization_name || 'Не указано'}</div>
          <div className="form-group"><b>ИНН:</b> {user.inn || 'Не указан'}</div>
          <div className="form-group"><b>ОГРН:</b> {user.ogrn || 'Не указан'}</div>
          <div className="form-group"><b>Контактное лицо:</b> {user.org_contact_name || 'Не указано'}</div>
          <div className="form-group"><b>Телефон:</b> {user.org_phone || 'Не указан'}</div>
          <div className="form-group"><b>Email:</b> {user.org_email || 'Не указан'}</div>
          <div className="form-group"><b>Юр. адрес:</b> {user.org_address || 'Не указан'}</div>
        </div>
        <button className="btn btn-danger" onClick={handleDeleteProfile} style={{ marginTop: 16 }}>Удалить профиль</button>
      </div>
    );
  }

  // --- Альтернативный рендеринг для admin ---
  if (user?.role === 'admin') {
    return (
      <div className="profile-page">
        <div className="profile-header card mb-4">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div className="avatar" style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: 'var(--tg-button-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px', color: 'white' }}>
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', borderRadius: '50%' }} />
              ) : (
                <User size={40} />
              )}
            </div>
            <div>
              <h2 className="mb-1">{user?.first_name} {user?.last_name}</h2>
              <p className="text-muted mb-1">@{user?.telegram_username || 'admin'}</p>
              <p className="text-muted font-small">🔧 Администратор</p>
            </div>
          </div>
        </div>
        <div className="card mb-4">
          <h3 className="mb-3">Права администратора</h3>
          <p>У вас есть полный доступ к управлению пользователями, организациями и событиями.</p>
          <button className="btn btn-primary" onClick={() => navigate('/admin')}>Перейти в админ-панель</button>
        </div>
      </div>
    );
  }

  if (loading) {
    return <LoadingSpinner message="Загрузка профиля..." />;
  }

  return (
    <div className="profile-page">
      {/* Header */}
      <div className="profile-header card mb-4">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div className="avatar" style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              backgroundColor: 'var(--tg-button-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '32px',
              color: 'white'
            }}>
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', borderRadius: '50%' }} />
              ) : (
                <User size={40} />
              )}
            </div>

            <div>
              <h2 className="mb-1">{user?.first_name} {user?.last_name}</h2>
              <p className="text-muted mb-1">@{user?.telegram_username || 'volunteer'}</p>
              <p className="text-muted font-small">
                {user?.role === 'volunteer' && '🤝 Волонтер'}
                {user?.role === 'organizer' && '👔 Организатор'}
                {user?.role === 'admin' && '🔧 Администратор'}
              </p>
            </div>
          </div>

          <button
            onClick={() => editMode ? handleCancel() : setEditMode(true)}
            className={`btn ${editMode ? 'btn-outline' : 'btn-primary'}`}
            disabled={saving}
          >
            {editMode ? <X size={16} /> : <Edit size={16} />}
            <span className="ml-2">{editMode ? 'Отмена' : 'Редактировать'}</span>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="profile-completion mt-4">
          <div className="completion-header">
            <span>Заполненность профиля:</span>
            <span className="completion-percentage">{getCompletionPercentage()}%</span>
          </div>
          <div className="completion-bar">
            <div
              className="completion-fill"
              style={{ width: `${getCompletionPercentage()}%` }}
            />
          </div>
        </div>
      </div>

      {errors.general && (
        <div className="error-message mb-4">
          {errors.general}
        </div>
      )}

      {/* Main Info */}
      <div className="card mb-4">
        <h3 className="mb-3">📧 Основная информация</h3>

        <div className="form-row">
          <div className="form-group">
            <label>Email</label>
            {editMode ? (
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="form-control"
                placeholder="your@example.com"
              />
            ) : (
              <p className="form-value">{formData.email || 'Не указан'}</p>
            )}
          </div>

          <div className="form-group">
            <label>Телефон</label>
            {editMode ? (
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className="form-control"
                placeholder="+7 (XXX) XXX-XX-XX"
              />
            ) : (
              <p className="form-value">{formData.phone || 'Не указан'}</p>
            )}
          </div>
        </div>

        <div className="form-group">
          <label>О себе</label>
          {editMode ? (
            <textarea
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              className="form-control"
              placeholder="Расскажите о себе..."
              rows="3"
            />
          ) : (
            <p className="form-value">{formData.bio || 'Не указано'}</p>
          )}
        </div>

        <div className="form-group">
          <label>Город</label>
          {editMode ? (
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              className="form-control"
              placeholder="Ваш город"
            />
          ) : (
            <p className="form-value">{formData.location || 'Не указан'}</p>
          )}
        </div>
      </div>

      {/* Personal Info */}
      <div className="card mb-4">
        <h3 className="mb-3">👤 Личные данные</h3>

        <div className="form-group">
          <label>Отчество</label>
          {editMode ? (
            <input
              type="text"
              name="middle_name"
              value={formData.middle_name}
              onChange={handleChange}
              className="form-control"
              placeholder="Введите отчество"
            />
          ) : (
            <p className="form-value">{formData.middle_name || 'Не указано'}</p>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Дата рождения</label>
            {editMode ? (
              <input
                type="date"
                name="birth_date"
                value={formData.birth_date}
                onChange={handleChange}
                className="form-control"
              />
            ) : (
              <p className="form-value">
                {formData.birth_date
                  ? new Date(formData.birth_date).toLocaleDateString('ru-RU')
                  : 'Не указана'
                }
              </p>
            )}
          </div>

          <div className="form-group">
            <label>Пол</label>
            {editMode ? (
              <select
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
            ) : (
              <p className="form-value">
                {formData.gender === 'male' && 'Мужской'}
                {formData.gender === 'female' && 'Женский'}
                {formData.gender === 'other' && 'Другой'}
                {!formData.gender && 'Не указан'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Emergency Contacts */}
      <div className="card mb-4">
        <h3 className="mb-3">🚨 Экстренные контакты</h3>

        <div className="form-group">
          <label>Контактное лицо</label>
          {editMode ? (
            <input
              type="text"
              name="emergency_contact_name"
              value={formData.emergency_contact_name}
              onChange={handleChange}
              className="form-control"
              placeholder="ФИО контактного лица"
            />
          ) : (
            <p className="form-value">{formData.emergency_contact_name || 'Не указано'}</p>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Телефон контакта</label>
            {editMode ? (
              <input
                type="tel"
                name="emergency_contact_phone"
                value={formData.emergency_contact_phone}
                onChange={handleChange}
                className="form-control"
                placeholder="+7 (XXX) XXX-XX-XX"
              />
            ) : (
              <p className="form-value">{formData.emergency_contact_phone || 'Не указан'}</p>
            )}
          </div>

          <div className="form-group">
            <label>Степень родства</label>
            {editMode ? (
              <select
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
            ) : (
              <p className="form-value">
                {formData.emergency_contact_relation === 'parent' && 'Родитель'}
                {formData.emergency_contact_relation === 'spouse' && 'Супруг(а)'}
                {formData.emergency_contact_relation === 'sibling' && 'Брат/Сестра'}
                {formData.emergency_contact_relation === 'child' && 'Ребенок'}
                {formData.emergency_contact_relation === 'friend' && 'Друг'}
                {formData.emergency_contact_relation === 'relative' && 'Родственник'}
                {formData.emergency_contact_relation === 'other' && 'Другое'}
                {!formData.emergency_contact_relation && 'Не указано'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Professional Info */}
      <div className="card mb-4">
        <h3 className="mb-3">💼 Профессиональные данные</h3>

        <div className="form-group">
          <label>Образование</label>
          {editMode ? (
            <input
              type="text"
              name="education"
              value={formData.education}
              onChange={handleChange}
              className="form-control"
              placeholder="Ваше образование"
            />
          ) : (
            <p className="form-value">{formData.education || 'Не указано'}</p>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Профессия</label>
            {editMode ? (
              <input
                type="text"
                name="occupation"
                value={formData.occupation}
                onChange={handleChange}
                className="form-control"
                placeholder="Чем занимаетесь"
              />
            ) : (
              <p className="form-value">{formData.occupation || 'Не указано'}</p>
            )}
          </div>

          <div className="form-group">
            <label>Организация</label>
            {editMode ? (
              <input
                type="text"
                name="organization"
                value={formData.organization}
                onChange={handleChange}
                className="form-control"
                placeholder="Место работы/учебы"
              />
            ) : (
              <p className="form-value">{formData.organization || 'Не указано'}</p>
            )}
          </div>
        </div>
      </div>

      {/* Skills & Experience */}
      <div className="card mb-4">
        <h3 className="mb-3">💪 Навыки и опыт</h3>

        <div className="form-group">
          <label>Навыки</label>
          {editMode ? (
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
          ) : (
            <div className="skills-display">
              {formData.skills.length > 0 ? (
                formData.skills.map(skill => (
                  <span key={skill} className="skill-tag">{skill}</span>
                ))
              ) : (
                <p className="form-value">Не указаны</p>
              )}
            </div>
          )}
        </div>

        <div className="form-group">
          <label>Опыт волонтерства</label>
          {editMode ? (
            <textarea
              name="experience_description"
              value={formData.experience_description}
              onChange={handleChange}
              className="form-control"
              placeholder="Расскажите о своем опыте волонтерской работы..."
              rows="4"
            />
          ) : (
            <p className="form-value">{formData.experience_description || 'Не указан'}</p>
          )}
        </div>
      </div>

      {/* Save Button */}
      {editMode && (
        <div className="form-buttons mb-4">
          <button
            onClick={handleSave}
            className="btn btn-primary"
            disabled={saving}
          >
            <Save size={16} />
            <span className="ml-2">{saving ? 'Сохранение...' : 'Сохранить изменения'}</span>
          </button>
        </div>
      )}

      <button className="btn btn-danger" onClick={handleDeleteProfile} style={{marginTop: 24}}>
        Удалить профиль
      </button>
    </div>
  );
};

export default ProfilePage;