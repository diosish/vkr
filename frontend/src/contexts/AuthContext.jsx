import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const resetAuth = () => {
        console.log('Сброс состояния аутентификации...');
        localStorage.removeItem('token');
        setUser(null);
        setError(null);
        setLoading(false);
    };

    useEffect(() => {
        const initializeAuth = async () => {
            try {
                console.log('Инициализация аутентификации...');
                const token = localStorage.getItem('token');
                console.log('Токен:', token ? 'найден' : 'не найден');

                if (!token) {
                    console.log('Токен не найден, завершаем инициализацию');
                    resetAuth();
                    return;
                }

                console.log('Отправляем запрос к /api/auth/me...');
                const response = await fetch('/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
                    }
                });

                console.log('Статус ответа:', response.status);
                if (!response.ok) {
                    if (response.status === 401) {
                        console.log('Получен 401, очищаем токен');
                        resetAuth();
                        return;
                    }
                    throw new Error('Ошибка аутентификации');
                }

                const userData = await response.json();
                console.log('Получены данные пользователя:', userData);
                setUser(userData);
                setLoading(false);

                if (!userData.is_registered) {
                    console.log('Пользователь не зарегистрирован, перенаправляем на /register');
                    navigate('/register');
                }
            } catch (error) {
                console.error('Ошибка инициализации аутентификации:', error);
                resetAuth();
            }
        };

        initializeAuth();
    }, [navigate]);

    const login = async (telegramData) => {
        try {
            console.log('Начало входа...');
            setLoading(true);
            setError(null);

            console.log('Отправляем запрос к /api/auth/telegram...');
            const response = await fetch('/api/auth/telegram', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(telegramData)
            });

            console.log('Статус ответа:', response.status);
            if (!response.ok) {
                throw new Error('Ошибка входа');
            }

            const data = await response.json();
            console.log('Получены данные:', data);
            localStorage.setItem('token', data.access_token);
            setUser(data.user);
            setLoading(false);

            // Заменить строку 103-107:
            const response = await fetch('/api/auth/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Telegram-Init-Data': telegramData || window.Telegram?.WebApp?.initData || ''
                }
            });
        } catch (error) {
            console.error('Ошибка входа:', error);
            setError(error.message);
            setLoading(false);
            throw error;
        }
    };

    const logout = () => {
        console.log('Выход из системы...');
        resetAuth();
        navigate('/');
    };

    const deleteProfile = async () => {
        try {
            console.log('Удаление профиля...');
            setLoading(true);
            setError(null);

            const response = await fetch('/api/auth/delete-profile', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
                }
            });

            console.log('Статус ответа:', response.status);
            if (!response.ok) {
                throw new Error('Ошибка удаления профиля');
            }

            resetAuth();
            navigate('/');
        } catch (error) {
            console.error('Ошибка удаления профиля:', error);
            setError(error.message);
            setLoading(false);
            throw error;
        }
    };

    const value = {
        user,
        setUser,
        loading,
        error,
        login,
        logout,
        deleteProfile,
        isAuthenticated: !!user
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}; 