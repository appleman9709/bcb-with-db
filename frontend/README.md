# 📱 BabyCareBot Dashboard Frontend

Telegram Mini App для отображения дашборда BabyCareBot.

## ✨ Особенности

- 🎨 Современный и красивый интерфейс
- 📊 Статистика в реальном времени
- 📈 Графики истории событий
- 📱 Адаптивный дизайн для мобильных устройств
- 🌙 Поддержка темной темы Telegram
- ⚡ Быстрая загрузка и обновление данных

## 🚀 Быстрый старт

### Локальное тестирование

1. **Запустите API сервер:**
   ```bash
   cd ..
   python api.py
   ```

2. **Откройте index.html в браузере**

3. **Измените API URL в app.js:**
   ```javascript
   const API_BASE_URL = 'http://localhost:5000/api';
   ```

### Развертывание на Vercel

1. **Установите Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Войдите в Vercel:**
   ```bash
   vercel login
   ```

3. **Разверните приложение:**
   ```bash
   vercel --prod
   ```

4. **Обновите API URL на продакшн сервер**

## 🏗️ Структура проекта

```
frontend/
├── index.html          # Главная страница
├── styles.css          # Стили
├── app.js              # JavaScript логика
├── vercel.json         # Конфигурация Vercel
├── package.json        # Зависимости
└── README.md           # Документация
```

## 📱 Telegram Mini App

### Инициализация

Приложение автоматически инициализирует Telegram Web App:

```javascript
if (window.Telegram && window.Telegram.WebApp) {
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();
}
```

### Тема

Поддерживается автоматическое переключение темы:

```javascript
if (window.Telegram.WebApp.colorScheme === 'dark') {
    document.body.classList.add('dark-theme');
}
```

## 🎨 Дизайн

### Цветовая схема

- **Основной градиент:** `#667eea` → `#764ba2`
- **Фон:** Полупрозрачный белый с размытием
- **Текст:** Темно-серый для читаемости
- **Акценты:** Цветные статусы для событий

### Компоненты

- **Карточки:** Полупрозрачные с размытием
- **Иконки:** Эмодзи с градиентным фоном
- **Кнопки:** Современные с hover эффектами
- **Графики:** Chart.js с кастомными цветами

## 📊 API интеграция

### Эндпоинты

- `GET /api/families` - Список семей
- `GET /api/family/{id}/dashboard` - Данные дашборда
- `GET /api/family/{id}/history` - История событий
- `GET /api/family/{id}/members` - Члены семьи

### Автообновление

Данные обновляются каждые 30 секунд:

```javascript
setInterval(() => {
    if (currentFamilyId) {
        loadDashboard(currentFamilyId);
    }
}, 30000);
```

## 🔧 Настройка

### Конфигурация API

Измените `API_BASE_URL` в `app.js`:

```javascript
const API_BASE_URL = 'https://your-api-domain.com/api';
```

### Переменные окружения

Создайте `.env` файл для локальной разработки:

```env
API_BASE_URL=http://localhost:5000/api
```

## 📱 Адаптивность

### Breakpoints

- **Desktop:** > 768px
- **Tablet:** 480px - 768px  
- **Mobile:** < 480px

### Особенности

- Гибкая сетка для статистики
- Вертикальное расположение карточек на мобильных
- Адаптивные размеры шрифтов
- Оптимизированные отступы

## 🚀 Производительность

### Оптимизации

- Минимальные зависимости
- Ленивая загрузка графиков
- Кэширование данных
- Оптимизированные CSS анимации

### Метрики

- **First Contentful Paint:** < 1s
- **Largest Contentful Paint:** < 2s
- **Cumulative Layout Shift:** < 0.1

## 🧪 Тестирование

### Браузеры

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Устройства

- ✅ Desktop
- ✅ Tablet
- ✅ Mobile
- ✅ Telegram Web App

## 🔒 Безопасность

### CORS

Настроен для работы с Telegram доменами:

```json
{
  "Content-Security-Policy": "frame-ancestors 'self' https://web.telegram.org https://t.me;"
}
```

### Валидация

- Проверка ответов API
- Обработка ошибок сети
- Безопасные HTTP запросы

## 📚 Зависимости

### Внешние

- **Chart.js:** Графики и диаграммы
- **Telegram Web App:** Telegram API
- **Google Fonts:** Шрифт Inter

### Встроенные

- **Fetch API:** HTTP запросы
- **CSS Grid/Flexbox:** Макет
- **CSS Variables:** Динамические стили

## 🤝 Разработка

### Добавление новых функций

1. Обновите HTML структуру
2. Добавьте CSS стили
3. Реализуйте JavaScript логику
4. Протестируйте на разных устройствах

### Стиль кода

- ES6+ синтаксис
- Async/await для API вызовов
- Комментарии на русском языке
- Консистентное форматирование

## 📄 Лицензия

MIT License - свободно используйте и модифицируйте.
