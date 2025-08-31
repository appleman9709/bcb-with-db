// Конфигурация для разных окружений
const config = {
    // Локальная разработка
    development: {
        API_BASE_URL: 'https://bcb-db.vercel.app/api'
    },
    // Продакшн (Vercel)
    production: {
        API_BASE_URL: 'https://bcb-db.vercel.app/api' // Измените на ваш API сервер
    }
};

// Определяем окружение
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const currentConfig = isDevelopment ? config.development : config.production;

// Экспортируем конфигурацию
window.APP_CONFIG = currentConfig;
