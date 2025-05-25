import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import EventsPage from './pages/EventsPage';
import EventDetailsPage from './pages/EventDetailsPage';
import MyRegistrationsPage from './pages/MyRegistrationsPage';
import CreateEventPage from './pages/CreateEventPage';
import LoadingSpinner from './components/LoadingSpinner';
import useTelegram from './hooks/useTelegram';
import { verifyTelegramAuth, getCurrentUser } from './services/api';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { tg, user: telegramUser, showAlert, isSupported } = useTelegram();

  useEffect(() => {
    if (isSupported) {
      authenticateUser();
    } else {
      setError('Приложение должно запускаться в Telegram');
      setLoading(false);
    }
  }, [isSupported, tg]);

  const authenticateUser = async () => {
    try {
      if (tg?.initData) {
        // Верифицируем через API
        const authResponse = await verifyTelegramAuth(tg.initData);

        if (authResponse.success) {
          setUser(authResponse.user);

          // Показываем приветствие для новых пользователей
          if (authResponse.is_new_user) {
            showAlert(`Добро пожаловать, ${authResponse.user.first_name}! 🎉`);
          }
        } else {
          throw new Error('Ошибка аутентификации');
        }
      } else {
        // Для тестирования без Telegram
        const testUser = {
          id: 1,
          first_name: 'Тест',
          last_name: 'Пользователь',
          role: 'volunteer',
          display_name: 'Тест Пользователь'
        };
        setUser(testUser);
      }
    } catch (err) {
      console.error('Ошибка аутентификации:', err);
      setError('Ошибка аутентификации: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Загрузка..." />;
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
        <button onClick={authenticateUser} className="btn btn-primary">
          🔄 Попробовать снова
        </button>
      </div>
    );
  }

  return (
    <div className="app">
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
              <Route path="/create-event" element={<CreateEventPage user={user} />} />
            )}

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </Router>
    </div>
  );
}

export default App;