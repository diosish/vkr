import { useEffect, useState } from 'react';

const useTelegram = () => {
  const [tg, setTg] = useState(null);
  const [user, setUser] = useState(null);
  const [themeParams, setThemeParams] = useState({});

  useEffect(() => {
    const telegram = window.Telegram?.WebApp;

    if (telegram) {
      setTg(telegram);

      // Инициализация
      telegram.ready();
      telegram.expand();

      // Получаем данные пользователя
      if (telegram.initDataUnsafe?.user) {
        setUser(telegram.initDataUnsafe.user);
      }

      // Получаем параметры темы
      setThemeParams(telegram.themeParams);

      // Применяем тему
      applyTheme(telegram.themeParams);

      // Настройка кнопок
      telegram.MainButton.hide();
      telegram.BackButton.hide();

      console.log('Telegram Web App initialized:', telegram);
    }
  }, []);

  const applyTheme = (params) => {
    const root = document.documentElement;

    // Применяем CSS переменные
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        root.style.setProperty(`--tg-${key.replace(/_/g, '-')}`, value);
      }
    });

    // Основные цвета
    root.style.setProperty('--tg-bg-color', params.bg_color || '#ffffff');
    root.style.setProperty('--tg-text-color', params.text_color || '#000000');
    root.style.setProperty('--tg-hint-color', params.hint_color || '#999999');
    root.style.setProperty('--tg-link-color', params.link_color || '#2481cc');
    root.style.setProperty('--tg-button-color', params.button_color || '#2481cc');
    root.style.setProperty('--tg-button-text-color', params.button_text_color || '#ffffff');
    root.style.setProperty('--tg-secondary-bg-color', params.secondary_bg_color || '#f1f1f1');
  };

  const showAlert = (message) => {
    if (tg) {
      tg.showAlert(message);
    } else {
      alert(message);
    }
  };

  const showConfirm = (message, callback) => {
    if (tg) {
      tg.showConfirm(message, callback);
    } else {
      const result = confirm(message);
      callback(result);
    }
  };

  const hapticFeedback = (type = 'impact', style = 'medium') => {
    if (tg?.HapticFeedback) {
      if (type === 'impact') {
        tg.HapticFeedback.impactOccurred(style);
      } else if (type === 'notification') {
        tg.HapticFeedback.notificationOccurred(style);
      } else if (type === 'selection') {
        tg.HapticFeedback.selectionChanged();
      }
    }
  };

  const setMainButton = (text, onClick) => {
    if (tg?.MainButton) {
      tg.MainButton.setText(text);
      tg.MainButton.onClick(onClick);
      tg.MainButton.show();
    }
  };

  const hideMainButton = () => {
    if (tg?.MainButton) {
      tg.MainButton.hide();
    }
  };

  const setBackButton = (onClick) => {
    if (tg?.BackButton) {
      tg.BackButton.onClick(onClick);
      tg.BackButton.show();
    }
  };

  const hideBackButton = () => {
    if (tg?.BackButton) {
      tg.BackButton.hide();
    }
  };

  return {
    tg,
    user,
    themeParams,
    showAlert,
    showConfirm,
    hapticFeedback,
    setMainButton,
    hideMainButton,
    setBackButton,
    hideBackButton,
    isSupported: !!window.Telegram?.WebApp
  };
};

export default useTelegram;