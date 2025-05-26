// frontend/src/App.jsx
import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import RegistrationForm from './components/RegistrationForm';
import HomePage from './pages/HomePage';
import ProfilePage from './pages/ProfilePage';
import EventsPage from './pages/EventsPage';
import EventDetailsPage from './pages/EventDetailsPage';
import MyRegistrationsPage from './pages/MyRegistrationsPage';
import CreateEventPage from './pages/CreateEventPage';
import LoadingSpinner from './components/LoadingSpinner';
import useTelegram from './hooks/useTelegram';
import AdminPanelPage from './pages/AdminPanelPage';
import { authenticateUser, refreshUserData, saveAuthData, getAuthData } from './services/auth';
import ManageEventsPage from './pages/ManageEventsPage';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRegistration, setShowRegistration] = useState(false);
  const [registrationStep, setRegistrationStep] = useState('welcome');

  const { tg, showAlert, isSupported } = useTelegram();

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      setLoading(true);
      setError(null);

      // 1. Пробуем взять пользователя из localStorage
      const savedAuth = getAuthData();
      if (savedAuth?.user) {
        setUser(savedAuth.user);
        setShowRegistration(false);
        setRegistrationStep('welcome');
        setLoading(false);
        return;
      }

      let initData = '';
      if (isSupported && tg?.initData) {
        initData = tg.initData;
        console.log('Using Telegram init data');
      } else {
        console.log('No Telegram data, using guest mode');
      }

      // Аутентификация пользователя
      const authResponse = await authenticateUser(initData);

      if (authResponse?.user) {
        setUser(authResponse.user);

        // Показываем приветствие для новых пользователей
        if (authResponse.is_new_user && showAlert) {
          showAlert(`Добро пожаловать, ${authResponse.user.first_name}! 🎉`);
        }

        // Определяем нужна ли регистрация
        if (authResponse.requires_registration || authResponse.is_new_user ||
            !authResponse.user.email || !authResponse.user.phone ||
            (authResponse.user.completion_percentage && authResponse.user.completion_percentage < 70)) {

          setShowRegistration(true);
          setRegistrationStep(authResponse.is_new_user ? 'welcome' : 'form');
        }
      } else {
        throw new Error('No user data received');
      }

    } catch (err) {
      console.error('Authentication error:', err);

      // Не показываем ошибку пользователю, создаем гостевого пользователя
      const guestUser = {
        id: 999,
        telegram_user_id: 999999999,
        first_name: 'Гость',
        last_name: 'Пользователь',
        role: 'volunteer',
        display_name: '@guest',
        profile_completed: false,
        completion_percentage: 0,
        full_name: 'Гость Пользователь'
      };

      setUser(guestUser);
      setShowRegistration(true);
      setRegistrationStep('welcome');

    } finally {
      setLoading(false);
    }
  };

  const handleRegistrationComplete = async (userData) => {
    try {
      setUser(userData);
      setShowRegistration(false);
      setRegistrationStep('welcome');

      // Обновляем данные пользователя
      const updatedUser = await refreshUserData(tg?.initData);
      if (updatedUser) {
        setUser(updatedUser);
        // Сохраняем в localStorage
        const prevAuth = getAuthData();
        if (prevAuth) saveAuthData({ ...prevAuth, user: updatedUser });
      }
    } catch (error) {
      console.error('Failed to reload user data:', error);
    }
  };

  const handleSkipRegistration = () => {
    setShowRegistration(false);
    setRegistrationStep('welcome');
  };

  const startRegistration = () => {
    setShowRegistration(true);
    setRegistrationStep('form');
  };

  // Loading screen
  if (loading) {
    return <LoadingSpinner message="Загрузка..." />;
  }

  // No user (shouldn't happen now)
  if (!user) {
    return (
      <div className="error-screen">
        <h2>🔄 Инициализация...</h2>
        <p>Подготовка приложения...</p>
        <button onClick={initializeApp} className="btn btn-primary">
          🔄 Повторить
        </button>
      </div>
    );
  }

  // Registration flow
  if (showRegistration) {
    if (registrationStep === 'welcome') {
      return (
        <div className="registration-welcome">
          <div className="welcome-icon">🤝</div>
          <h2>Добро пожаловать в систему волонтеров!</h2>
          <p>
            Привет, {user.first_name}! Для полноценного участия в мероприятиях
            нам нужно узнать о вас немного больше. Заполнение профиля займет
            всего несколько минут.
          </p>

          {user.completion_percentage > 0 && (
            <div className="profile-completion">
              <div className="completion-header">
                <span>Профиль заполнен:</span>
                <span className="completion-percentage">{user.completion_percentage}%</span>
              </div>
              <div className="completion-bar">
                <div
                  className="completion-fill"
                  style={{ width: `${user.completion_percentage}%` }}
                />
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button onClick={startRegistration} className="btn btn-primary">
              {user.completion_percentage > 0 ? 'Продолжить заполнение' : 'Заполнить профиль'}
            </button>
            <button onClick={handleSkipRegistration} className="btn btn-outline">
              Пропустить пока
            </button>
          </div>

          <p style={{ marginTop: '20px', fontSize: '14px', color: 'var(--tg-hint-color)' }}>
            💡 Вы всегда можете заполнить профиль позже в настройках
          </p>
        </div>
      );
    }

    return (
      <RegistrationForm
        user={user}
        onComplete={handleRegistrationComplete}
        onSkip={handleSkipRegistration}
      />
    );
  }

  // Main app
  return (
    <div className="app">
      <Router>
        <Layout user={user}>
          <Routes>
            <Route path="/" element={<HomePage user={user} />} />
            <Route path="/profile" element={<ProfilePage user={user} setUser={setUser} />} />
            <Route path="/events" element={<EventsPage user={user} />} />
            <Route path="/events/:id" element={<EventDetailsPage user={user} />} />
            <Route path="/my-registrations" element={<MyRegistrationsPage user={user} />} />
            <Route path="/create-event" element={<CreateEventPage user={user} />} />
            <Route path="/admin" element={<AdminPanelPage user={user} />} />
            <Route path="/manage-events" element={<ManageEventsPage user={user} />} />
          </Routes>
        </Layout>
      </Router>
    </div>
  );
}

export default App;