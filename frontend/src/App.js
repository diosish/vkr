import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import EventsPage from './pages/EventsPage';
import EventDetailsPage from './pages/EventDetailsPage';
import MyRegistrationsPage from './pages/MyRegistrationsPage';
import CreateEventPage from './pages/CreateEventPage';
import ManageEventsPage from './pages/ManageEventsPage';
import { verifyTelegramAuth, getCurrentUser } from './services/api';
import './App.css';

// Telegram Web App
const tg = window.Telegram?.WebApp;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Инициализация Telegram Web App
    if (tg) {
      tg.ready();
      tg.expand();

      // Применяем тему Telegram
      applyTelegramTheme();

      // Аутентификация
      authenticateUser();
    } else {
      setError('Приложение должно запускаться в Telegram');
      setLoading(false);
    }
  }, []);

  const applyTelegramTheme = () => {
    const root = document.documentElement;

    // Применяем цвета темы Telegram
    root.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
    root.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
    root.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
    root.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#2481cc');
    root.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
    root.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
    root.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f1f1f1');

    // Применяем к body
    document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';
    document.body.style.color = tg.themeParams.text_color || '#000000';
  };

  const authenticateUser = async () => {
    try {
      if (tg?.initData) {
        // Верифицируем через API
        const authResponse = await verifyTelegramAuth(tg.initData);

        // Получаем полную информацию о пользователе
        const userInfo = await getCurrentUser(tg.initData);

        setUser(userInfo);

        // Показываем приветствие для новых пользователей
        if (authResponse.is_new_user) {
          tg.showAlert(`Добро пожаловать, ${userInfo.first_name}! 🎉`);
        }

      } else {
        throw new Error('Нет данных аутентификации Telegram');
      }
    } catch (err) {
      console.error('Ошибка аутентификации:', err);
      setError('Ошибка аутентификации: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Загрузка...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <h2>❌ Ошибка</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()} className="btn btn-primary">
          🔄 Перезагрузить
        </button>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="error-screen">
        <h2>🔐 Требуется аутентификация</h2>
        <p>Не удалось получить данные пользователя</p>
        <button onClick={() => window.location.reload()} className="btn btn-primary">
          🔄 Попробовать снова
        </button>
      </div>
    );
  }

  return (
    <Router>
      <Layout user={user}>
        <Routes>
          <Route path="/" element={<HomePage user={user} />} />
          <Route path="/profile" element={<ProfilePage user={user} />} />
          <Route path="/events" element={<EventsPage user={user} />} />
          <Route path="/events/:id" element={<EventDetailsPage user={user} />} />

          {/* Маршруты для волонтеров */}
          {user.role === 'volunteer' && (
            <Route path="/my-registrations" element={<MyRegistrationsPage user={user} />} />
          )}

          {/* Маршруты для организаторов и админов */}
          {(user.role === 'organizer' || user.role === 'admin') && (
            <>
              <Route path="/create-event" element={<CreateEventPage user={user} />} />
              <Route path="/manage-events" element={<ManageEventsPage user={user} />} />
            </>
          )}

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;