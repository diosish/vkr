import React, { useState, useEffect } from 'react';
import { Search, Edit, Trash2, User, Building } from 'lucide-react';
import useTelegram from '../hooks/useTelegram';
import { EVENT_STATUS, apiRequest } from '../services/api';

const AdminPanelPage = () => {
  const [users, setUsers] = useState([]);
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const { showAlert } = useTelegram();
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [editingEvent, setEditingEvent] = useState(null);

  useEffect(() => {
    loadStats();
    loadUsers();
    loadOrganizations();
    loadEvents();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await fetch('/api/admin/users', {
        headers: {
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        }
      });
      if (!response.ok) throw new Error('Ошибка загрузки пользователей');
      const data = await response.json();
      setUsers(data);
    } catch (err) {
      setError(err.message);
      showAlert('Ошибка загрузки пользователей: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizations = async () => {
    try {
      const response = await fetch('/api/admin/organizations', {
        headers: {
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        }
      });
      if (!response.ok) throw new Error('Ошибка загрузки организаций');
      const data = await response.json();
      setOrganizations(data);
    } catch (err) {
      setError(err.message);
      showAlert('Ошибка загрузки организаций: ' + err.message);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/admin/stats', {
        headers: {
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        }
      });
      if (!response.ok) throw new Error('Ошибка загрузки статистики');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
      showAlert('Ошибка загрузки статистики: ' + err.message);
    }
  };

  const loadEvents = async () => {
    try {
      const response = await fetch('/api/admin/events', {
        headers: {
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        }
      });
      if (!response.ok) throw new Error('Ошибка загрузки событий');
      const data = await response.json();
      setEvents(data);
    } catch (err) {
      setError(err.message);
      showAlert('Ошибка загрузки событий: ' + err.message);
    }
  };

  const handleSearch = async () => {
    try {
      const response = await fetch(`/api/admin/users?search=${searchTerm}&role=${selectedRole}`, {
        headers: {
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        }
      });
      if (!response.ok) throw new Error('Ошибка поиска');
      const data = await response.json();
      setUsers(data);
    } catch (err) {
      showAlert('Ошибка поиска: ' + err.message);
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user);
  };

  const handleSave = async (userData) => {
    try {
      const response = await fetch(`/api/admin/users/${userData.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        },
        body: JSON.stringify(userData)
      });
      if (!response.ok) throw new Error('Ошибка сохранения');
      showAlert('Пользователь успешно обновлен');
      setEditingUser(null);
      loadUsers();
    } catch (err) {
      showAlert('Ошибка сохранения: ' + err.message);
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этого пользователя?')) return;
    
    try {
      const response = await fetch(`/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        }
      });
      if (!response.ok) throw new Error('Ошибка удаления');
      showAlert('Пользователь успешно удален');
      loadUsers();
    } catch (err) {
      showAlert('Ошибка удаления: ' + err.message);
    }
  };

  const handleEditEvent = (event) => {
    setEditingEvent(event);
  };

  const handleSaveEvent = async (eventData) => {
    try {
      const response = await fetch(`/api/admin/events/${eventData.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        },
        body: JSON.stringify(eventData)
      });
      if (!response.ok) throw new Error('Ошибка сохранения');
      showAlert('Мероприятие успешно обновлено');
      setEditingEvent(null);
      loadEvents();
    } catch (err) {
      showAlert('Ошибка сохранения: ' + err.message);
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!window.confirm('Вы уверены, что хотите удалить это мероприятие?')) return;
    try {
      const response = await fetch(`/api/admin/events/${eventId}`, {
        method: 'DELETE',
        headers: {
          'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
        }
      });
      if (!response.ok) throw new Error('Ошибка удаления');
      showAlert('Мероприятие успешно удалено');
      loadEvents();
    } catch (err) {
      showAlert('Ошибка удаления: ' + err.message);
    }
  };

  const handleChangeStatus = async (eventId, newStatus) => {
    try {
      await apiRequest(`/events/${eventId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      loadEvents();
    } catch (e) {
      alert('Ошибка смены статуса: ' + (e.message || e));
    }
  };

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка: {error}</div>;

  return (
    <div className="admin-panel-page">
      <h1>Админ-панель</h1>
      
      {/* Статистика */}
      {stats && (
        <div className="stats-box mb-4">
          <div>Всего пользователей: <b>{stats.users_total}</b></div>
          <div>Волонтёров: <b>{stats.volunteers_total}</b></div>
          <div>Организаторов: <b>{stats.organizers_total}</b></div>
          <div>Админов: <b>{stats.admins_total}</b></div>
          <div>Организаций: <b>{stats.organizations_total}</b></div>
          <div>Мероприятий: <b>{stats.events_total}</b></div>
        </div>
      )}

      {/* Поиск и фильтры */}
      <div className="search-section">
        <div className="search-box">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Поиск пользователей..."
          />
          <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)}>
            <option value="">Все роли</option>
            <option value="volunteer">Волонтёры</option>
            <option value="organizer">Организаторы</option>
            <option value="admin">Администраторы</option>
          </select>
          <button onClick={handleSearch} className="btn btn-primary">
            <Search size={16} /> Поиск
          </button>
        </div>
      </div>

      {/* Таблица пользователей */}
      <section>
        <h2><User size={20} /> Пользователи</h2>
        <div className="table-responsive">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Имя</th>
                <th>Email</th>
                <th>Телефон</th>
                <th>Роль</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>{user.first_name} {user.last_name}</td>
                  <td>{user.email}</td>
                  <td>{user.phone}</td>
                  <td>{user.role}</td>
                  <td>{user.is_active ? 'Активен' : 'Неактивен'}</td>
                  <td>
                    <button onClick={() => handleEdit(user)} className="btn btn-icon">
                      <Edit size={16} />
                    </button>
                    <button onClick={() => handleDelete(user.id)} className="btn btn-icon btn-danger">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Таблица организаций */}
      <section>
        <h2><Building size={20} /> Организации</h2>
        <div className="table-responsive">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Контактное лицо</th>
                <th>Email</th>
                <th>Телефон</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {organizations.map(org => (
                <tr key={org.id}>
                  <td>{org.id}</td>
                  <td>{org.organization_name}</td>
                  <td>{org.org_contact_name}</td>
                  <td>{org.org_email}</td>
                  <td>{org.org_phone}</td>
                  <td>
                    <button onClick={() => handleEdit(org)} className="btn btn-icon">
                      <Edit size={16} />
                    </button>
                    <button onClick={() => handleDelete(org.id)} className="btn btn-icon btn-danger">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Таблица событий */}
      <section>
        <h2>События</h2>
        <div className="table-responsive">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Название</th>
                <th>Категория</th>
                <th>Статус</th>
                <th>Дата начала</th>
                <th>Дата окончания</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {events.map(event => (
                <tr key={event.id}>
                  <td>{event.id}</td>
                  <td>{event.title}</td>
                  <td>{event.category}</td>
                  <td>
                    <select
                      value={event.status}
                      onChange={e => handleChangeStatus(event.id, e.target.value)}
                    >
                      <option value={EVENT_STATUS.DRAFT}>Черновик</option>
                      <option value={EVENT_STATUS.PUBLISHED}>Опубликовано</option>
                      <option value={EVENT_STATUS.CANCELLED}>Отменено</option>
                      <option value={EVENT_STATUS.COMPLETED}>Завершено</option>
                    </select>
                  </td>
                  <td>{event.start_date && new Date(event.start_date).toLocaleString()}</td>
                  <td>{event.end_date && new Date(event.end_date).toLocaleString()}</td>
                  <td>
                    <button onClick={() => handleEditEvent(event)} className="btn btn-icon">
                      <Edit size={16} />
                    </button>
                    <button onClick={() => handleDeleteEvent(event.id)} className="btn btn-icon btn-danger">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Модальное окно редактирования */}
      {editingUser && (
        <div className="modal">
          <div className="modal-content">
            <h3>Редактирование пользователя</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              handleSave(editingUser);
            }}>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={editingUser.email || ''}
                  onChange={(e) => setEditingUser({...editingUser, email: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Телефон</label>
                <input
                  type="tel"
                  value={editingUser.phone || ''}
                  onChange={(e) => setEditingUser({...editingUser, phone: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Роль</label>
                <select
                  value={editingUser.role}
                  onChange={(e) => setEditingUser({...editingUser, role: e.target.value})}
                >
                  <option value="volunteer">Волонтёр</option>
                  <option value="organizer">Организатор</option>
                  <option value="admin">Администратор</option>
                </select>
              </div>
              <div className="form-group">
                <label>Статус</label>
                <select
                  value={editingUser.is_active}
                  onChange={(e) => setEditingUser({...editingUser, is_active: e.target.value === 'true'})}
                >
                  <option value="true">Активен</option>
                  <option value="false">Неактивен</option>
                </select>
              </div>
              {editingUser.role === 'organizer' && (
                <>
                  <div className="form-group">
                    <label>Название организации</label>
                    <input
                      type="text"
                      value={editingUser.organization_name || ''}
                      onChange={(e) => setEditingUser({...editingUser, organization_name: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label>ИНН</label>
                    <input
                      type="text"
                      value={editingUser.inn || ''}
                      onChange={(e) => setEditingUser({...editingUser, inn: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label>ОГРН</label>
                    <input
                      type="text"
                      value={editingUser.ogrn || ''}
                      onChange={(e) => setEditingUser({...editingUser, ogrn: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label>Контактное лицо</label>
                    <input
                      type="text"
                      value={editingUser.org_contact_name || ''}
                      onChange={(e) => setEditingUser({...editingUser, org_contact_name: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label>Телефон организации</label>
                    <input
                      type="tel"
                      value={editingUser.org_phone || ''}
                      onChange={(e) => setEditingUser({...editingUser, org_phone: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label>Email организации</label>
                    <input
                      type="email"
                      value={editingUser.org_email || ''}
                      onChange={(e) => setEditingUser({...editingUser, org_email: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label>Адрес</label>
                    <input
                      type="text"
                      value={editingUser.org_address || ''}
                      onChange={(e) => setEditingUser({...editingUser, org_address: e.target.value})}
                    />
                  </div>
                </>
              )}
              <div className="modal-buttons">
                <button type="submit" className="btn btn-primary">Сохранить</button>
                <button type="button" className="btn btn-secondary" onClick={() => setEditingUser(null)}>
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Модальное окно редактирования события */}
      {editingEvent && (
        <div className="modal">
          <div className="modal-content">
            <h3>Редактирование события</h3>
            <form onSubmit={e => { e.preventDefault(); handleSaveEvent(editingEvent); }}>
              <div className="form-group">
                <label>Название</label>
                <input type="text" value={editingEvent.title || ''} onChange={e => setEditingEvent({...editingEvent, title: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Категория</label>
                <input type="text" value={editingEvent.category || ''} onChange={e => setEditingEvent({...editingEvent, category: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Статус</label>
                <input type="text" value={editingEvent.status || ''} onChange={e => setEditingEvent({...editingEvent, status: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Дата начала</label>
                <input type="datetime-local" value={editingEvent.start_date ? new Date(editingEvent.start_date).toISOString().slice(0,16) : ''} onChange={e => setEditingEvent({...editingEvent, start_date: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Дата окончания</label>
                <input type="datetime-local" value={editingEvent.end_date ? new Date(editingEvent.end_date).toISOString().slice(0,16) : ''} onChange={e => setEditingEvent({...editingEvent, end_date: e.target.value})} />
              </div>
              <div className="modal-buttons">
                <button type="submit" className="btn btn-primary">Сохранить</button>
                <button type="button" className="btn btn-secondary" onClick={() => setEditingEvent(null)}>Отмена</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanelPage; 