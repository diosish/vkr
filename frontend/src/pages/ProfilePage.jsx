// frontend/src/pages/ProfilePage.jsx
import React, { useState, useEffect } from 'react';
import { User, Edit, Save, X, Phone, Mail, MapPin, Calendar, Award, Heart } from 'lucide-react';
import { updateProfile } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import useTelegram from '../hooks/useTelegram';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProfilePage = () => {
  const { user, setUser, deleteProfile } = useAuth();
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
      await deleteProfile();
      navigate('/');
    } catch (e) {
      showAlert('Ошибка удаления профиля: ' + e.message);
    }
  };

  // --- Альтернативный рендеринг для organizer ---
  if (user?.role === 'organizer') {
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
        <button className="btn btn-danger" onClick={handleDeleteProfile} style={{ marginTop: 16 }}>Удалить профиль</button>
      </div>
    );
  }

  // --- Основной рендеринг для volunteer ---
  return (
    <div className="profile-page">
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
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
                <p className="text-muted mb-1">@{user?.telegram_username || 'volunteer'}</p>
                <p className="text-muted font-small">🤝 Волонтер</p>
              </div>
            </div>
          </div>

          {editMode ? (
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h3>Редактирование профиля</h3>
                <div>
                  <button className="btn btn-secondary me-2" onClick={handleCancel} disabled={saving}>
                    <X size={16} className="me-1" /> Отмена
                  </button>
                  <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                    {saving ? <LoadingSpinner size="sm" /> : <><Save size={16} className="me-1" /> Сохранить</>}
                  </button>
                </div>
              </div>
              <div className="card-body">
                {/* Форма редактирования */}
                <div className="row">
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Email</label>
                      <input
                        type="email"
                        className="form-control"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Телефон</label>
                      <input
                        type="tel"
                        className="form-control"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                </div>

                <div className="form-group mb-3">
                  <label>О себе</label>
                  <textarea
                    className="form-control"
                    name="bio"
                    value={formData.bio}
                    onChange={handleChange}
                    rows={3}
                  />
                </div>

                <div className="form-group mb-3">
                  <label>Местоположение</label>
                  <input
                    type="text"
                    className="form-control"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                  />
                </div>

                <h4 className="mt-4 mb-3">Экстренные контакты</h4>
                <div className="row">
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Имя контактного лица</label>
                      <input
                        type="text"
                        className="form-control"
                        name="emergency_contact_name"
                        value={formData.emergency_contact_name}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Телефон</label>
                      <input
                        type="tel"
                        className="form-control"
                        name="emergency_contact_phone"
                        value={formData.emergency_contact_phone}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Отношение</label>
                      <input
                        type="text"
                        className="form-control"
                        name="emergency_contact_relation"
                        value={formData.emergency_contact_relation}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                </div>

                <h4 className="mt-4 mb-3">Профессиональные данные</h4>
                <div className="row">
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Образование</label>
                      <input
                        type="text"
                        className="form-control"
                        name="education"
                        value={formData.education}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Профессия</label>
                      <input
                        type="text"
                        className="form-control"
                        name="occupation"
                        value={formData.occupation}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Организация</label>
                      <input
                        type="text"
                        className="form-control"
                        name="organization"
                        value={formData.organization}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                </div>

                <div className="form-group mb-3">
                  <label>Опыт волонтерства</label>
                  <textarea
                    className="form-control"
                    name="experience_description"
                    value={formData.experience_description}
                    onChange={handleChange}
                    rows={3}
                  />
                </div>

                <h4 className="mt-4 mb-3">Навыки и интересы</h4>
                <div className="row">
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Навыки</label>
                      <div className="skills-grid">
                        {skillsOptions.map(skill => (
                          <div
                            key={skill}
                            className={`skill-item ${formData.skills.includes(skill) ? 'active' : ''}`}
                            onClick={() => handleMultiSelect('skills', skill)}
                          >
                            {skill}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Интересы</label>
                      <div className="interests-grid">
                        {interestsOptions.map(interest => (
                          <div
                            key={interest}
                            className={`interest-item ${formData.interests.includes(interest) ? 'active' : ''}`}
                            onClick={() => handleMultiSelect('interests', interest)}
                          >
                            {interest}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <h4 className="mt-4 mb-3">Доступность</h4>
                <div className="row">
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Готовность к поездкам</label>
                      <div className="form-check">
                        <input
                          type="checkbox"
                          className="form-check-input"
                          name="travel_willingness"
                          checked={formData.travel_willingness}
                          onChange={handleChange}
                        />
                        <label className="form-check-label">Готов к поездкам</label>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Максимальное расстояние (км)</label>
                      <input
                        type="number"
                        className="form-control"
                        name="max_travel_distance"
                        value={formData.max_travel_distance}
                        onChange={handleChange}
                        min="0"
                        max="1000"
                      />
                    </div>
                  </div>
                </div>

                <div className="form-group mb-3">
                  <label>Предпочитаемые виды деятельности</label>
                  <div className="activities-grid">
                    {preferredActivitiesOptions.map(activity => (
                      <div
                        key={activity}
                        className={`activity-item ${formData.preferred_activities.includes(activity) ? 'active' : ''}`}
                        onClick={() => handleMultiSelect('preferred_activities', activity)}
                      >
                        {activity}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h3>Профиль волонтера</h3>
                <button className="btn btn-primary" onClick={() => setEditMode(true)}>
                  <Edit size={16} className="me-1" /> Редактировать
                </button>
              </div>
              <div className="card-body">
                <div className="row">
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label><Mail size={16} className="me-1" /> Email</label>
                      <p>{user?.email || 'Не указан'}</p>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label><Phone size={16} className="me-1" /> Телефон</label>
                      <p>{user?.phone || 'Не указан'}</p>
                    </div>
                  </div>
                </div>

                <div className="form-group mb-3">
                  <label><User size={16} className="me-1" /> О себе</label>
                  <p>{user?.bio || 'Не указано'}</p>
                </div>

                <div className="form-group mb-3">
                  <label><MapPin size={16} className="me-1" /> Местоположение</label>
                  <p>{user?.location || 'Не указано'}</p>
                </div>

                <h4 className="mt-4 mb-3">Экстренные контакты</h4>
                <div className="row">
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Имя контактного лица</label>
                      <p>{user?.emergency_contact_name || 'Не указано'}</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Телефон</label>
                      <p>{user?.emergency_contact_phone || 'Не указан'}</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Отношение</label>
                      <p>{user?.emergency_contact_relation || 'Не указано'}</p>
                    </div>
                  </div>
                </div>

                <h4 className="mt-4 mb-3">Профессиональные данные</h4>
                <div className="row">
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Образование</label>
                      <p>{user?.education || 'Не указано'}</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Профессия</label>
                      <p>{user?.occupation || 'Не указана'}</p>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="form-group mb-3">
                      <label>Организация</label>
                      <p>{user?.organization || 'Не указана'}</p>
                    </div>
                  </div>
                </div>

                <div className="form-group mb-3">
                  <label>Опыт волонтерства</label>
                  <p>{user?.experience_description || 'Не указан'}</p>
                </div>

                <h4 className="mt-4 mb-3">Навыки и интересы</h4>
                <div className="row">
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Навыки</label>
                      <div className="skills-list">
                        {user?.skills?.length > 0 ? (
                          user.skills.map(skill => (
                            <span key={skill} className="badge bg-primary me-1 mb-1">{skill}</span>
                          ))
                        ) : (
                          <p className="text-muted">Навыки не указаны</p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Интересы</label>
                      <div className="interests-list">
                        {user?.interests?.length > 0 ? (
                          user.interests.map(interest => (
                            <span key={interest} className="badge bg-info me-1 mb-1">{interest}</span>
                          ))
                        ) : (
                          <p className="text-muted">Интересы не указаны</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <h4 className="mt-4 mb-3">Доступность</h4>
                <div className="row">
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Готовность к поездкам</label>
                      <p>{user?.travel_willingness ? 'Да' : 'Нет'}</p>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="form-group mb-3">
                      <label>Максимальное расстояние</label>
                      <p>{user?.max_travel_distance ? `${user.max_travel_distance} км` : 'Не указано'}</p>
                    </div>
                  </div>
                </div>

                <div className="form-group mb-3">
                  <label>Предпочитаемые виды деятельности</label>
                  <div className="activities-list">
                    {user?.preferred_activities?.length > 0 ? (
                      user.preferred_activities.map(activity => (
                        <span key={activity} className="badge bg-secondary me-1 mb-1">{activity}</span>
                      ))
                    ) : (
                      <p className="text-muted">Виды деятельности не указаны</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          <button className="btn btn-danger" onClick={handleDeleteProfile} style={{ marginTop: 16 }}>Удалить профиль</button>
        </>
      )}
    </div>
  );
};

export default ProfilePage;