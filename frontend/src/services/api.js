// frontend/src/services/api.js
// Полноценный API клиент для системы волонтеров

const API_BASE_URL = '/api';

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

// ==========================================
// AUTH API
// ==========================================

export const verifyTelegramAuth = async (initData) => {
  return apiRequest('/auth/verify', {
    method: 'POST',
    headers: {
      'X-Telegram-Init-Data': initData,
    },
  });
};

export const getCurrentUser = async () => {
  return apiRequest('/auth/me');
};

export const completeRegistration = async (registrationData) => {
  return apiRequest('/auth/complete-registration', {
    method: 'POST',
    body: JSON.stringify(registrationData),
  });
};

export const updateProfile = async (profileData) => {
  return apiRequest('/auth/profile', {
    method: 'PUT',
    body: JSON.stringify(profileData),
  });
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

export const getEvents = async (params = {}) => {
  const searchParams = new URLSearchParams(params);
  return apiRequest(`/events?${searchParams}`);
};

export const getEvent = async (id) => {
  return apiRequest(`/events/${id}`);
};

export const createEvent = async (eventData) => {
  return apiRequest('/events', {
    method: 'POST',
    body: JSON.stringify(eventData),
  });
};

export const updateEvent = async (id, eventData) => {
  return apiRequest(`/events/${id}`, {
    method: 'PUT',
    body: JSON.stringify(eventData),
  });
};

export const deleteEvent = async (id) => {
  return apiRequest(`/events/${id}`, {
    method: 'DELETE',
  });
};

export const getMyEvents = async () => {
  return apiRequest('/events/my/created');
};

// ==========================================
// REGISTRATIONS API
// ==========================================

export const getMyRegistrations = async () => {
  return apiRequest('/registrations/my');
};

export const registerForEvent = async (registrationData) => {
  return apiRequest('/registrations', {
    method: 'POST',
    body: JSON.stringify(registrationData),
  });
};

export const updateRegistration = async (registrationId, updateData) => {
  return apiRequest(`/registrations/${registrationId}`, {
    method: 'PUT',
    body: JSON.stringify(updateData),
  });
};

export const cancelRegistration = async (registrationId) => {
  return apiRequest(`/registrations/${registrationId}`, {
    method: 'DELETE',
  });
};

export const getEventRegistrations = async (eventId) => {
  return apiRequest(`/registrations/event/${eventId}`);
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
  SOCIAL: 'social',
  ENVIRONMENTAL: 'environmental',
  EDUCATION: 'education',
  HEALTH: 'health',
  COMMUNITY: 'community',
  EMERGENCY: 'emergency',
  SPORTS: 'sports',
  CULTURE: 'culture',
  OTHER: 'other'
};

export const EVENT_CATEGORY_LABELS = {
  [EVENT_CATEGORIES.SOCIAL]: 'Социальные',
  [EVENT_CATEGORIES.ENVIRONMENTAL]: 'Экология',
  [EVENT_CATEGORIES.EDUCATION]: 'Образование',
  [EVENT_CATEGORIES.HEALTH]: 'Здравоохранение',
  [EVENT_CATEGORIES.COMMUNITY]: 'Сообщество',
  [EVENT_CATEGORIES.EMERGENCY]: 'Экстренные',
  [EVENT_CATEGORIES.SPORTS]: 'Спорт',
  [EVENT_CATEGORIES.CULTURE]: 'Культура',
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
  REJECTED: 'rejected',
  CANCELLED: 'cancelled',
  COMPLETED: 'completed'
};

export const USER_ROLES = {
  VOLUNTEER: 'volunteer',
  ORGANIZER: 'organizer',
  ADMIN: 'admin'
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
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatDateShort = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// ==========================================
// ERROR HANDLING
// ==========================================

export const handleApiError = (error, showAlert = true) => {
  console.error('API Error:', error);

  let message = 'Произошла ошибка';

  if (error.message) {
    message = error.message;
  } else if (typeof error === 'string') {
    message = error;
  }

  if (showAlert) {
    showTelegramAlert(message);
  }

  return message;
};