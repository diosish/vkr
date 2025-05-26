// frontend/src/services/api.js
// Полноценный API клиент для системы волонтеров

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Добавляем перехватчик для добавления токена и данных Telegram
apiClient.interceptors.request.use((config) => {
    // Добавляем JWT токен если есть
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    // Добавляем данные Telegram если есть
    if (window.Telegram?.WebApp?.initData) {
        config.headers['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData;
    }

    return config;
});

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
export const apiRequest = async (url, options = {}) => {
  try {
    const response = await fetch(`${API_URL}${url}`, {
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

// ==========================================
// AUTH API
// ==========================================

export const verifyTelegramAuth = async (initData) => {
    const response = await apiClient.post('/api/auth/verify', null, {
        headers: {
            'X-Telegram-Init-Data': initData
        }
    });
    return response.data;
};

export const getCurrentUser = async () => {
    const response = await apiClient.get('/api/auth/me');
    return response.data;
};

export const completeRegistration = async (registrationData) => {
    const response = await apiClient.post('/api/auth/complete-registration', registrationData);
    return response.data;
};

export const updateProfile = async (userData) => {
    const response = await apiClient.put('/api/auth/profile', userData);
    return response.data;
};

export const changeUserRole = async (userId, newRole) => {
  return apiRequest(`/auth/change-role/${userId}`, {
    method: 'POST',
    body: JSON.stringify({ role: newRole }),
  });
};

export const getUsers = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  return apiRequest(`/auth/users?${params}`);
};

// ==========================================
// EVENTS API
// ==========================================

export const getEvents = async () => {
    const response = await apiClient.get('/api/events');
    return response.data;
};

export const getEvent = async (eventId) => {
    const response = await apiClient.get(`/api/events/${eventId}`);
    return response.data;
};

export const createEvent = async (eventData) => {
    const response = await apiClient.post('/api/events', eventData);
    return response.data;
};

export const updateEvent = async (eventId, eventData) => {
    const response = await apiClient.put(`/api/events/${eventId}`, eventData);
    return response.data;
};

export const deleteEvent = async (eventId) => {
    const response = await apiClient.delete(`/api/events/${eventId}`);
    return response.data;
};

export const getMyEvents = async () => {
    const response = await apiClient.get('/api/events/my/created');
    return response.data;
};

export const publishEvent = async (eventId) => {
    const response = await apiClient.patch(`/api/events/${eventId}/status`, { status: 'published' });
    return response.data;
};

export const cancelEvent = async (eventId) => {
    const response = await apiClient.patch(`/api/events/${eventId}/status`, { status: 'cancelled' });
    return response.data;
};

// ==========================================
// REGISTRATIONS API
// ==========================================

export const registerForEvent = async (registrationData) => {
    const response = await apiClient.post('/api/registrations', registrationData);
    return response.data;
};

export const getMyRegistrations = async () => {
    const response = await apiClient.get('/api/registrations/my');
    return response.data;
};

export const cancelRegistration = async (registrationId) => {
    const response = await apiClient.post(`/api/registrations/${registrationId}/cancel`);
    return response.data;
};

export const getEventRegistrations = async (eventId) => {
    const response = await apiClient.get(`/api/registrations/event/${eventId}`);
    return response.data;
};

// ==========================================
// LEGACY VOLUNTEERS API (for compatibility)
// ==========================================

export const getVolunteers = async () => {
  return apiRequest('/volunteers');
};

export const createVolunteer = async (volunteerData) => {
  return apiRequest('/volunteers', {
    method: 'POST',
    body: JSON.stringify(volunteerData),
  });
};

export const updateVolunteer = async (id, volunteerData) => {
  return apiRequest(`/volunteers/${id}`, {
    method: 'PUT',
    body: JSON.stringify(volunteerData),
  });
};

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

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
        const result = window.confirm(message);
        callback(result);
    }
};

export const closeTelegramApp = () => {
    if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.close();
    }
};

export const expandTelegramApp = () => {
    if (window.Telegram?.WebApp) {
        window.Telegram.WebApp.expand();
    }
};

// ==========================================
// EVENT CATEGORIES AND CONSTANTS
// ==========================================

export const EVENT_CATEGORIES = {
    ENVIRONMENTAL: 'environmental',
    SOCIAL: 'social',
    EDUCATION: 'education',
    HEALTH: 'health',
    COMMUNITY: 'community',
    CULTURE: 'culture',
    SPORTS: 'sports',
    EMERGENCY: 'emergency',
    OTHER: 'other'
};

export const EVENT_CATEGORY_LABELS = {
    [EVENT_CATEGORIES.ENVIRONMENTAL]: 'Экология',
    [EVENT_CATEGORIES.SOCIAL]: 'Социальные',
    [EVENT_CATEGORIES.EDUCATION]: 'Образование',
    [EVENT_CATEGORIES.HEALTH]: 'Здоровье',
    [EVENT_CATEGORIES.COMMUNITY]: 'Сообщество',
    [EVENT_CATEGORIES.CULTURE]: 'Культура',
    [EVENT_CATEGORIES.SPORTS]: 'Спорт',
    [EVENT_CATEGORIES.EMERGENCY]: 'Экстренные',
    [EVENT_CATEGORIES.OTHER]: 'Другое'
};

export const EVENT_STATUS = {
  DRAFT: 'draft',
  PUBLISHED: 'published',
  CANCELLED: 'cancelled',
  COMPLETED: 'completed'
};

export const REGISTRATION_STATUS = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  CANCELLED: 'cancelled'
};

export const USER_ROLES = {
  ADMIN: 'admin',
  ORGANIZER: 'organizer',
  VOLUNTEER: 'volunteer'
};

// ==========================================
// VALIDATION HELPERS
// ==========================================

export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const validatePhone = (phone) => {
  const re = /^[\+]?[1-9][\d]{0,15}$/;
  return re.test(phone.replace(/[\s\-\(\)]/g, ''));
};

export const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
};

export const formatDateShort = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
};

// ==========================================
// ERROR HANDLING
// ==========================================

export const handleApiError = (error, showAlert = true) => {
    console.error('API Error:', error);
    
    let message = 'Произошла ошибка при выполнении запроса';
    
    if (error.response) {
        message = error.response.data?.detail || error.response.data?.message || message;
    } else if (error.message) {
        message = error.message;
    }
    
    if (showAlert) {
        showTelegramAlert(message);
    }
    
    return message;
};