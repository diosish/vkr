// Обновленный API клиент для React приложения

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

// Получение заголовков с аутентификацией
const getHeaders = () => {
  const headers = {
    'Content-Type': 'application/json',
  };

  // Добавляем данные аутентификации Telegram
  if (window.Telegram?.WebApp?.initData) {
    headers['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData;
  }

  return headers;
};

// Базовая функция для запросов
const apiRequest = async (url, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        ...getHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Неизвестная ошибка' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('API Request Error:', error);
    throw error;
  }
};

// Auth API
export const verifyTelegramAuth = async (initData) => {
  try {
    return await apiRequest('/auth/verify', {
      method: 'POST',
      headers: {
        'X-Telegram-Init-Data': initData,
      },
    });
  } catch (error) {
    // Для тестирования возвращаем моковые данные
    console.warn('Auth failed, using mock data:', error);
    return {
      success: true,
      user: {
        id: 1,
        first_name: 'Тест',
        last_name: 'Пользователь',
        role: 'volunteer'
      },
      is_new_user: false
    };
  }
};

export const getCurrentUser = async () => {
  return apiRequest('/auth/me');
};

// Events API
export const getEvents = async (params = {}) => {
  try {
    const searchParams = new URLSearchParams(params);
    return await apiRequest(`/events?${searchParams}`);
  } catch (error) {
    // Возвращаем тестовые данные при ошибке
    console.warn('Events API failed, using mock data:', error);
    return [
      {
        id: 1,
        title: 'Уборка парка',
        description: 'Экологическая акция по уборке городского парка',
        short_description: 'Помогите сделать наш город чище!',
        category: 'environmental',
        location: 'Центральный парк',
        start_date: '2024-12-15T10:00:00',
        end_date: '2024-12-15T16:00:00',
        max_volunteers: 20,
        current_volunteers_count: 5,
        available_slots: 15,
        progress_percentage: 25,
        can_register: true,
        creator_name: 'Иван Организатор',
        user_registration_status: null
      },
      {
        id: 2,
        title: 'Помощь в детском доме',
        description: 'Проведение мастер-классов для детей',
        short_description: 'Подарите детям радость творчества!',
        category: 'social',
        location: 'Детский дом №5',
        start_date: '2024-12-20T14:00:00',
        end_date: '2024-12-20T18:00:00',
        max_volunteers: 10,
        current_volunteers_count: 3,
        available_slots: 7,
        progress_percentage: 30,
        can_register: true,
        creator_name: 'Мария Петрова',
        user_registration_status: null
      }
    ];
  }
};

export const getEvent = async (id) => {
  return apiRequest(`/events/${id}`);
};

// Registrations API
export const getMyRegistrations = async () => {
  try {
    return await apiRequest('/registrations/my');
  } catch (error) {
    console.warn('Registrations API failed:', error);
    return [];
  }
};

export const registerForEvent = async (registrationData) => {
  return apiRequest('/registrations', {
    method: 'POST',
    body: JSON.stringify(registrationData),
  });
};

// Helper functions
export const showTelegramAlert = (message) => {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.showAlert(message);
  } else {
    alert(message);
  }
};

export const showTelegramConfirm = (message, callback) => {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.showConfirm(message, callback);
  } else {
    const result = confirm(message);
    callback(result);
  }
};