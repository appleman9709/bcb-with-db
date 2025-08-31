# 🚀 Развертывание BabyCareBot Dashboard

Этот документ описывает, как развернуть Telegram Mini App с дашбордом для BabyCareBot.

## 📋 Требования

- Python 3.8+
- Node.js 16+ (для Vercel CLI)
- База данных SQLite (babybot.db)
- Telegram Bot Token

## 🏗️ Архитектура

```
BabyCareBot Dashboard
├── API (Flask) - Читает данные из babybot.db
├── Frontend (HTML/CSS/JS) - Telegram Mini App
└── Vercel - Хостинг фронтенда
```

## 🔧 Шаг 1: Настройка API

### 1.1 Установка зависимостей

```bash
pip install -r api_requirements.txt
```

### 1.2 Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
API_PORT=5000
# Другие переменные из основного бота
```

### 1.3 Запуск API

```bash
python api.py
```

API будет доступен на `http://localhost:5000`

## 🌐 Шаг 2: Развертывание фронтенда на Vercel

### 2.1 Установка Vercel CLI

```bash
npm install -g vercel
```

### 2.2 Вход в Vercel

```bash
vercel login
```

### 2.3 Развертывание

```bash
cd frontend
vercel --prod
```

### 2.4 Настройка домена

После развертывания получите URL вида: `https://your-app.vercel.app`

## 🤖 Шаг 3: Настройка Telegram Bot

### 3.1 Создание Mini App

1. Откройте [@BotFather](https://t.me/botfather)
2. Отправьте `/newapp`
3. Выберите вашего бота
4. Введите название Mini App
5. Загрузите иконку (512x512px)
6. Введите описание
7. Получите URL для Mini App

### 3.2 Настройка Web App

В вашем боте добавьте кнопку для открытия Mini App:

```python
from telethon import Button

# В main.py добавьте кнопку для открытия дашборда
dashboard_button = Button.url("📊 Дашборд", "https://your-app.vercel.app")

# Добавьте кнопку в меню
buttons = [
    [Button.text("🍼 Кормление"), Button.text("🧷 Смена подгузника")],
    [Button.text("😴 Сон"), Button.text("📜 История")],
    [Button.text("💡 Совет"), Button.text("⚙ Настройки")],
    [dashboard_button]  # Добавляем кнопку дашборда
]
```

## 🔒 Шаг 4: Безопасность

### 4.1 CORS настройки

API уже настроен для работы с фронтендом через CORS.

### 4.2 Ограничения доступа

API предоставляет только read-only доступ к данным:
- ✅ Чтение статистики
- ✅ Чтение истории
- ✅ Чтение настроек
- ❌ Запись/изменение данных

### 4.3 Валидация данных

Все запросы к API проходят валидацию:
- Проверка существования семьи
- Безопасные SQL-запросы
- Обработка ошибок

## 📱 Шаг 5: Тестирование

### 5.1 Локальное тестирование

1. Запустите API: `python api.py`
2. Откройте `frontend/index.html` в браузере
3. Измените `API_BASE_URL` в `app.js` на `http://localhost:5000/api`

### 5.2 Тестирование в Telegram

1. Разверните фронтенд на Vercel
2. Обновите `API_BASE_URL` на ваш сервер
3. Протестируйте через кнопку в боте

## 🚀 Шаг 6: Продакшн

### 6.1 Развертывание API

Для продакшна рекомендуется использовать:
- **Render**: `render.com`
- **Railway**: `railway.app`
- **Heroku**: `heroku.com`
- **DigitalOcean**: `digitalocean.com`

### 6.2 Обновление URL

После развертывания API обновите `API_BASE_URL` в `frontend/app.js`:

```javascript
const API_BASE_URL = 'https://your-api-domain.com/api';
```

### 6.3 Переразвертывание фронтенда

```bash
cd frontend
vercel --prod
```

## 📊 Мониторинг

### 6.1 Логи API

API выводит логи в консоль:
- Запросы к эндпоинтам
- Ошибки подключения к БД
- Статистика использования

### 6.2 Vercel Analytics

Включите аналитику в Vercel для отслеживания:
- Посещений
- Производительности
- Ошибок

## 🔧 Устранение неполадок

### Проблема: API не отвечает

**Решение:**
1. Проверьте, что API запущен
2. Проверьте порт в `.env`
3. Проверьте логи API

### Проблема: CORS ошибки

**Решение:**
1. Убедитесь, что CORS настроен в API
2. Проверьте домен фронтенда
3. Обновите `API_BASE_URL`

### Проблема: Данные не загружаются

**Решение:**
1. Проверьте подключение к БД
2. Проверьте права доступа к файлу БД
3. Проверьте структуру таблиц

### Проблема: Mini App не открывается

**Решение:**
1. Проверьте URL в BotFather
2. Убедитесь, что домен добавлен в белый список
3. Проверьте HTTPS сертификат

## 📚 Полезные ссылки

- [Telegram Mini Apps Documentation](https://core.telegram.org/bots/webapps)
- [Vercel Documentation](https://vercel.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Chart.js Documentation](https://www.chartjs.org/)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи API
2. Проверьте консоль браузера
3. Убедитесь, что все зависимости установлены
4. Проверьте настройки сети и файрвола
