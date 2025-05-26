import { verifyTelegramAuth, getCurrentUser, apiRequest } from './api';

const AUTH_STORAGE_KEY = 'volunteer_auth_data';

export const saveAuthData = (authData) => {
  try {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({
      ...authData,
      timestamp: Date.now()
    }));
  } catch (error) {
    console.error('Error saving auth data:', error);
  }
};

export const getAuthData = () => {
  try {
    const data = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!data) return null;
    
    const parsedData = JSON.parse(data);
    // Проверяем срок действия (24 часа)
    if (Date.now() - parsedData.timestamp > 24 * 60 * 60 * 1000) {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      return null;
    }
    return parsedData;
  } catch (error) {
    console.error('Error reading auth data:', error);
    return null;
  }
};

export const clearAuthData = () => {
  try {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  } catch (error) {
    console.error('Error clearing auth data:', error);
  }
};

export const authenticateUser = async (initData) => {
  try {
    // Пробуем получить сохраненные данные
    const savedAuth = getAuthData();
    if (savedAuth?.user) {
      return savedAuth;
    }

    // Если нет сохраненных данных, делаем новую аутентификацию
    const authResponse = await verifyTelegramAuth(initData);
    if (authResponse?.user) {
      saveAuthData(authResponse);
    }
    return authResponse;
  } catch (error) {
    console.error('Authentication error:', error);
    return null;
  }
};

export const refreshUserData = async (initData) => {
  try {
    const userData = await getCurrentUser(initData);
    if (userData) {
      const savedAuth = getAuthData();
      if (savedAuth) {
        saveAuthData({
          ...savedAuth,
          user: userData
        });
      }
    }
    return userData;
  } catch (error) {
    console.error('Error refreshing user data:', error);
    return null;
  }
};

export const completeRegistration = async (registrationData) => {
  try {
    // Получаем Telegram user_id из initData, если есть
    let telegramUserId = null;
    if (window.Telegram?.WebApp?.initData) {
      try {
        const params = new URLSearchParams(window.Telegram.WebApp.initData);
        const userStr = params.get('user');
        if (userStr) {
          const userObj = JSON.parse(userStr);
          telegramUserId = userObj.id;
        }
      } catch (e) {
        console.warn('Не удалось получить telegram_user_id из initData:', e);
      }
    }
    const dataToSend = { ...registrationData };
    if (telegramUserId) {
      dataToSend.telegram_user_id = telegramUserId;
    }
    const response = await apiRequest('/auth/complete-registration', {
      method: 'POST',
      body: JSON.stringify(dataToSend),
    });
    return response;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
}; 