/**
 * Telegram CloudStorage Service
 * Заменяет localStorage для работы в Telegram WebApp
 */

class TelegramStorageService {
  constructor() {
    this.memoryStorage = {};
    this.isCloudStorageAvailable = window.Telegram?.WebApp?.CloudStorage;
    this.isInitialized = false;

    console.log('TelegramStorage initialized:', {
      cloudStorage: !!this.isCloudStorageAvailable,
      telegram: !!window.Telegram?.WebApp
    });
  }

  /**
   * Инициализация storage
   */
  async init() {
    if (this.isInitialized) return;

    try {
      if (this.isCloudStorageAvailable) {
        // Проверяем работоспособность CloudStorage
        await this.setItem('_test', 'test_value');
        const testValue = await this.getItem('_test');
        if (testValue === 'test_value') {
          await this.removeItem('_test');
          console.log('✅ CloudStorage is working');
        } else {
          throw new Error('CloudStorage test failed');
        }
      } else {
        console.warn('⚠️ CloudStorage not available, using memory storage');
      }
      this.isInitialized = true;
    } catch (error) {
      console.error('❌ Storage initialization failed:', error);
      this.isCloudStorageAvailable = false;
    }
  }

  /**
   * Сохранение данных
   */
  async setItem(key, value) {
    await this.init();

    const serializedData = JSON.stringify({
      value,
      timestamp: Date.now(),
      version: '1.0'
    });

    if (this.isCloudStorageAvailable) {
      return new Promise((resolve, reject) => {
        window.Telegram.WebApp.CloudStorage.setItem(key, serializedData, (error, success) => {
          if (error) {
            console.error(`CloudStorage.setItem error for key "${key}":`, error);
            // Fallback to memory
            this.memoryStorage[key] = serializedData;
            resolve();
          } else {
            console.log(`✅ CloudStorage.setItem success for key "${key}"`);
            resolve();
          }
        });
      });
    } else {
      this.memoryStorage[key] = serializedData;
      return Promise.resolve();
    }
  }

  /**
   * Получение данных
   */
  async getItem(key) {
    await this.init();

    if (this.isCloudStorageAvailable) {
      return new Promise((resolve) => {
        window.Telegram.WebApp.CloudStorage.getItem(key, (error, value) => {
          if (error) {
            console.error(`CloudStorage.getItem error for key "${key}":`, error);
            // Fallback to memory
            const memoryValue = this.memoryStorage[key];
            resolve(this._parseStorageValue(memoryValue));
          } else {
            resolve(this._parseStorageValue(value));
          }
        });
      });
    } else {
      const stored = this.memoryStorage[key];
      return Promise.resolve(this._parseStorageValue(stored));
    }
  }

  /**
   * Удаление данных
   */
  async removeItem(key) {
    await this.init();

    if (this.isCloudStorageAvailable) {
      return new Promise((resolve) => {
        window.Telegram.WebApp.CloudStorage.removeItem(key, (error) => {
          if (error) {
            console.error(`CloudStorage.removeItem error for key "${key}":`, error);
          }
          // Always remove from memory too
          delete this.memoryStorage[key];
          resolve();
        });
      });
    } else {
      delete this.memoryStorage[key];
      return Promise.resolve();
    }
  }

  /**
   * Получение всех ключей
   */
  async getKeys() {
    await this.init();

    if (this.isCloudStorageAvailable) {
      return new Promise((resolve) => {
        window.Telegram.WebApp.CloudStorage.getKeys((error, keys) => {
          if (error) {
            console.error('CloudStorage.getKeys error:', error);
            resolve(Object.keys(this.memoryStorage));
          } else {
            resolve(keys || []);
          }
        });
      });
    } else {
      return Promise.resolve(Object.keys(this.memoryStorage));
    }
  }

  /**
   * Очистка всех данных
   */
  async clear() {
    await this.init();

    try {
      const keys = await this.getKeys();
      await Promise.all(keys.map(key => this.removeItem(key)));
      this.memoryStorage = {};
      console.log('✅ Storage cleared');
    } catch (error) {
      console.error('❌ Storage clear error:', error);
      this.memoryStorage = {};
    }
  }

  /**
   * Получение размера хранилища
   */
  async getStorageInfo() {
    await this.init();

    const keys = await this.getKeys();
    let totalSize = 0;

    for (const key of keys) {
      const value = await this.getItem(key);
      if (value !== null) {
        totalSize += JSON.stringify(value).length;
      }
    }

    return {
      keysCount: keys.length,
      totalSize,
      maxKeys: 1024, // Telegram limit
      maxValueSize: 4096, // Telegram limit per value
      storageType: this.isCloudStorageAvailable ? 'CloudStorage' : 'Memory'
    };
  }

  /**
   * Парсинг значения из хранилища
   */
  _parseStorageValue(value) {
    if (!value) return null;

    try {
      const parsed = JSON.parse(value);

      // Проверяем структуру данных
      if (parsed && typeof parsed === 'object' && 'value' in parsed) {
        return parsed.value;
      }

      // Если данные в старом формате, возвращаем как есть
      return parsed;
    } catch (error) {
      console.warn('Failed to parse storage value:', error);
      return value;
    }
  }

  /**
   * Проверка валидности ключа для Telegram CloudStorage
   */
  _isValidKey(key) {
    return typeof key === 'string' && key.length >= 1 && key.length <= 128;
  }

  /**
   * Проверка размера значения для Telegram CloudStorage
   */
  _isValidValue(value) {
    const serialized = JSON.stringify(value);
    return serialized.length <= 4096;
  }
}

// Создаем единственный экземпляр
export const storage = new TelegramStorageService();

// Экспортируем также класс для тестирования
export { TelegramStorageService };

// Legacy методы для совместимости с localStorage API
export const localStorage = {
  setItem: (key, value) => storage.setItem(key, value),
  getItem: (key) => storage.getItem(key),
  removeItem: (key) => storage.removeItem(key),
  clear: () => storage.clear(),
  key: async (index) => {
    const keys = await storage.getKeys();
    return keys[index] || null;
  },
  get length() {
    return storage.getKeys().then(keys => keys.length);
  }
};