import { useEffect, useState } from 'react';

const useTelegram = () => {
  const [tg, setTg] = useState(null);
  const [user, setUser] = useState(null);
  const [themeParams, setThemeParams] = useState({});

  useEffect(() => {
    const telegram = window.Telegram?.WebApp;

    if (telegram) {
      console.log('🤖 Telegram WebApp detected');
      setTg(telegram);

      try {
        // Инициализация
        telegram.ready();
        telegram.expand();

        // Получаем данные пользователя
        if (telegram.initDataUnsafe?.user) {
          setUser(telegram.initDataUnsafe.user);
          console.log('👤 Telegram user data:', telegram.initDataUnsafe.user);
        }

        // Получаем параметры темы
        setThemeParams(telegram.themeParams);

        // Применяем тему
        applyTheme(telegram.themeParams);

        // Настройка кнопок
        telegram.MainButton.hide();
        telegram.BackButton.hide();

        console.log('✅ Telegram Web App initialized successfully');
      } catch (error) {
        console.warn('⚠️ Telegram WebApp initialization error:', error);
      }
    } else {
      console.log('🌐 Running in browser mode (no Telegram WebApp)');
      // Применяем базовую тему для браузера
      applyTheme({
        bg_color: '#ffffff',
        text_color: '#000000',
        hint_color: '#999999',
        link_color: '#2481cc',
        button_color: '#2481cc',
        button_text_color: '#ffffff',
        secondary_bg_color: '#f1f1f1'
      });
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

    // Основные цвета с фоллбэком
    root.style.setProperty('--tg-bg-color', params.bg_color || '#ffffff');
    root.style.setProperty('--tg-text-color', params.text_color || '#000000');
    root.style.setProperty('--tg-hint-color', params.hint_color || '#999999');
    root.style.setProperty('--tg-link-color', params.link_color || '#2481cc');
    root.style.setProperty('--tg-button-color', params.button_color || '#2481cc');
    root.style.setProperty('--tg-button-text-color', params.button_text_color || '#ffffff');
    root.style.setProperty('--tg-secondary-bg-color', params.secondary_bg_color || '#f1f1f1');
  };

  const showAlert = (message) => {
    if (tg && tg.showAlert) {
      try {
        tg.showAlert(message);
      } catch (error) {
        console.warn('Telegram showAlert error:', error);
        alert(message);
      }
    } else {
      alert(message);
    }
  };

  const showConfirm = (message, callback) => {
    if (tg && tg.showConfirm) {
      try {
        tg.showConfirm(message, callback);
      } catch (error) {
        console.warn('Telegram showConfirm error:', error);
        const result = window.confirm(message);
        callback(result);
      }
    } else {
      const result = window.confirm(message);
      callback(result);
    }
  };

  const hapticFeedback = (type = 'impact', style = 'medium') => {
    if (tg?.HapticFeedback) {
      try {
        if (type === 'impact') {
          tg.HapticFeedback.impactOccurred(style);
        } else if (type === 'notification') {
          tg.HapticFeedback.notificationOccurred(style);
        } else if (type === 'selection') {
          tg.HapticFeedback.selectionChanged();
        }
      } catch (error) {
        console.warn('Haptic feedback error:', error);
      }
    }
    // В браузере не делаем ничего, это нормально
  };

  const setMainButton = (text, onClick) => {
    if (tg?.MainButton) {
      try {
        tg.MainButton.setText(text);
        tg.MainButton.onClick(onClick);
        tg.MainButton.show();
      } catch (error) {
        console.warn('Main button error:', error);
      }
    }
  };

  const hideMainButton = () => {
    if (tg?.MainButton) {
      try {
        tg.MainButton.hide();
      } catch (error) {
        console.warn('Hide main button error:', error);
      }
    }
  };

  const setBackButton = (onClick) => {
    if (tg?.BackButton) {
      try {
        tg.BackButton.onClick(onClick);
        tg.BackButton.show();
      } catch (error) {
        console.warn('Back button error:', error);
      }
    }
  };

  const hideBackButton = () => {
    if (tg?.BackButton) {
      try {
        tg.BackButton.hide();
      } catch (error) {
        console.warn('Hide back button error:', error);
      }
    }
  };

  const closeTelegramApp = () => {
    if (tg?.close) {
      try {
        tg.close();
      } catch (error) {
        console.warn('Close app error:', error);
      }
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
    closeTelegramApp,
    isSupported: !!window.Telegram?.WebApp,
    isTelegramEnvironment: !!window.Telegram?.WebApp,
    isBrowser: !window.Telegram?.WebApp
  };
};

export default useTelegram;