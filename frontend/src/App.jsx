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
import './App.css';

// API functions
const verifyTelegramAuth = async (initData) => {
  try {
    const response = await fetch('/api/auth/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': initData
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Authentication failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Auth error:', error);
    throw error;
  }
};

const getCurrentUser = async (initData) => {
  try {
    const response = await fetch('/api/auth/me', {
      headers: {
        'X-Telegram-Init-Data': initData
      }
    });

    if (!response.ok) {
      throw new Error('Failed to get user info');
    }

    return await response.json();
  } catch (error) {
    console.error('Get user error:', error);
    throw error;
  }
};

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRegistration, setShowRegistration] = useState(false);
  const [registrationStep, setRegistrationStep] = useState('welcome');

  const { tg, showAlert, isSupported } = useTelegram();

  useEffect(() => {
    if (isSupported) {
      authenticateUser();
    } else {
      // Режим разработки без Telegram
      setUser({
        id: 1,
        first_name: 'Тест',
        last_name: 'Пользователь',
        role: 'volunteer',
        display_name: 'Тест Пользователь',
        profile_completed: false,
        completion_percentage: 30
      });
      setLoading(false);
    }
  }, [isSupported, tg]);

  const authenticateUser = async () => {
    try {
      setLoading(true);

      if (tg?.initData) {
        // Верифицируем через API
        const authResponse = await verifyTelegramAuth(tg.initData);

        if (authResponse.success) {
          setUser(authResponse.user);

          // Показываем приветствие для новых пользователей
          if (authResponse.is_new_user) {
            showAlert(`Добро пожаловать, ${authResponse.user.first_name}! 🎉`);
            setShowRegistration(true);
            setRegistrationStep('welcome');
          } else if (authResponse.requires_registration) {
            // Пользователь существует, но профиль не заполнен
            setShowRegistration(true);
            setRegistrationStep('form');
          }
        } else {
          throw new Error('Authentication failed');
        }
      } else {
        throw new Error('No Telegram data available');
      }
    } catch (err) {
      console.error('Authentication error:', err);
      setError('Ошибка аутентификации: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegistrationComplete = async (userData) => {
    setUser(userData);
    setShowRegistration(false);
    setRegistrationStep('welcome');

    // Перезагружаем данные пользователя
    try {
      const updatedUser = await getCurrentUser(tg?.initData);
      setUser(updatedUser);
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

  // Error screen
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

  // No user
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

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <button onClick={startRegistration} className="btn btn-primary">
              {user.completion_percentage > 0 ? 'Продолжить заполнение' : 'Заполнить профиль'}
            </button>
            <button onClick={handleSkipRegistration} className="btn btn-outline">
              Пропустить пока
            </button>
          </div>
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