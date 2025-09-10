// Конфигурация для разных окружений
const config = {
    // Локальная разработка
    development: {
        API_BASE_URL: 'http://localhost:3000/api'
    },
    // Продакшн (Vercel) - замените на ваш URL API
    production: {
        API_BASE_URL: 'https://your-api-project.vercel.app/api'
    }
};

// Определяем окружение
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const currentConfig = isDevelopment ? config.development : config.production;

// Экспортируем конфигурацию
window.APP_CONFIG = currentConfig;
