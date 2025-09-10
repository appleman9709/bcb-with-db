# 🚀 Развертывание BabyCareBot на Vercel + Supabase

Пошаговая инструкция по развертыванию вашего Telegram бота на Vercel с использованием Supabase в качестве базы данных.

## 📋 Предварительные требования

1. **GitHub аккаунт** - для хранения кода
2. **Vercel аккаунт** - для хостинга
3. **Supabase аккаунт** - для базы данных
4. **Telegram Bot Token** - от @BotFather

## 🗄️ Шаг 1: Настройка Supabase

### 1.1 Создание проекта
1. Перейдите на [supabase.com](https://supabase.com)
2. Нажмите "New Project"
3. Выберите организацию и создайте новый проект
4. Дождитесь завершения создания (2-3 минуты)

### 1.2 Настройка базы данных
1. В панели Supabase перейдите в **SQL Editor**
2. Скопируйте содержимое файла `supabase_schema.sql`
3. Вставьте и выполните SQL скрипт
4. Проверьте, что все таблицы созданы в разделе **Table Editor**

### 1.3 Получение ключей API
1. Перейдите в **Settings** → **API**
2. Скопируйте:
   - **Project URL** (SUPABASE_URL)
   - **anon public** ключ (SUPABASE_ANON_KEY)

## 🤖 Шаг 2: Настройка Telegram бота

### 2.1 Создание бота
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный **BOT_TOKEN**

### 2.2 Получение API ключей
1. Перейдите на [my.telegram.org](https://my.telegram.org)
2. Войдите в аккаунт
3. Перейдите в **API development tools**
4. Создайте новое приложение
5. Сохраните **API_ID** и **API_HASH**

## 🌐 Шаг 3: Развертывание на Vercel

### 3.1 Подготовка репозитория
1. Создайте новый репозиторий на GitHub
2. Загрузите все файлы проекта
3. Убедитесь, что структура следующая:
   ```
   your-repo/
   ├── api/                    # Vercel API функции
   │   ├── api/
   │   ├── lib/
   │   ├── package.json
   │   └── vercel.json
   ├── frontend/               # Фронтенд приложение
   │   ├── index.html
   │   ├── styles.css
   │   ├── app.js
   │   ├── config.js
   │   └── vercel.json
   ├── main_supabase.py        # Telegram бот
   ├── migrate_to_supabase.py  # Скрипт миграции
   ├── vercel.json            # Конфигурация Vercel
   └── requirements_vercel.txt
   ```

### 3.2 Развертывание API
1. Перейдите на [vercel.com](https://vercel.com)
2. Нажмите "New Project"
3. Подключите ваш GitHub репозиторий
4. Настройте проект:
   - **Framework Preset**: Other
   - **Root Directory**: `api`
   - **Build Command**: `npm install`
   - **Output Directory**: (оставить пустым)

### 3.3 Настройка переменных окружения
В настройках проекта Vercel добавьте:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3.4 Развертывание фронтенда
1. Создайте второй проект в Vercel
2. Настройте:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`
   - **Build Command**: (оставить пустым)
   - **Output Directory**: (оставить пустым)

## 🔄 Шаг 4: Миграция данных

### 4.1 Подготовка
1. Убедитесь, что у вас есть локальная база данных `babybot.db`
2. Установите зависимости:
   ```bash
   pip install -r requirements_vercel.txt
   ```

### 4.2 Выполнение миграции
1. Создайте файл `.env` на основе `env_example_vercel.txt`
2. Заполните переменные Supabase
3. Запустите миграцию:
   ```bash
   python migrate_to_supabase.py
   ```

## 🚀 Шаг 5: Запуск бота

### 5.1 Локальный запуск (для тестирования)
1. Создайте файл `.env` с переменными:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   DASHBOARD_URL=https://your-dashboard.vercel.app
   ```
2. Запустите бота:
   ```bash
   python main_supabase.py
   ```

### 5.2 Продакшн запуск
Для постоянной работы бота рекомендуется использовать:
- **Railway** - railway.app
- **Render** - render.com
- **Heroku** - heroku.com
- **DigitalOcean** - digitalocean.com

## 🔧 Шаг 6: Настройка Mini App

### 6.1 Создание Mini App
1. Найдите [@BotFather](https://t.me/botfather)
2. Отправьте `/newapp`
3. Выберите вашего бота
4. Настройте:
   - **Title**: BabyCareBot Dashboard
   - **Description**: Красивый дашборд для отслеживания ухода за малышом
   - **Photo**: Загрузите иконку
   - **Web App URL**: `https://your-dashboard.vercel.app`

### 6.2 Обновление бота
В коде бота обновите `DASHBOARD_URL` на URL вашего фронтенда.

## 📊 Шаг 7: Проверка работы

### 7.1 Тестирование API
1. Откройте `https://your-api.vercel.app/api/health`
2. Должен вернуться JSON с `{"status": "healthy"}`

### 7.2 Тестирование фронтенда
1. Откройте `https://your-dashboard.vercel.app`
2. Проверьте загрузку данных

### 7.3 Тестирование бота
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Протестируйте все функции

## 🛠️ Устранение неполадок

### Проблема: API не отвечает
**Решение:**
- Проверьте переменные окружения в Vercel
- Убедитесь, что Supabase URL и ключ правильные
- Проверьте логи в панели Vercel

### Проблема: Бот не работает
**Решение:**
- Проверьте BOT_TOKEN
- Убедитесь, что API_ID и API_HASH правильные
- Проверьте подключение к Supabase

### Проблема: Данные не загружаются
**Решение:**
- Проверьте миграцию данных
- Убедитесь, что таблицы созданы в Supabase
- Проверьте RLS политики в Supabase

## 📈 Мониторинг

### Vercel
- **Analytics**: Статистика использования
- **Functions**: Логи API функций
- **Speed Insights**: Производительность

### Supabase
- **Database**: Статистика запросов
- **Logs**: Логи базы данных
- **API**: Использование API

## 🔒 Безопасность

### Supabase RLS
1. В панели Supabase перейдите в **Authentication** → **Policies**
2. Настройте политики Row Level Security
3. Ограничьте доступ к данным по необходимости

### Vercel
1. Используйте переменные окружения для секретов
2. Настройте CORS правильно
3. Регулярно обновляйте зависимости

## 📚 Дополнительные ресурсы

- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telethon Documentation](https://docs.telethon.dev/)

## 🎉 Готово!

Ваш BabyCareBot теперь работает на Vercel с Supabase! 

**Преимущества этого решения:**
- ✅ Масштабируемость
- ✅ Надежность
- ✅ Простота развертывания
- ✅ Автоматические обновления
- ✅ Глобальная доступность
- ✅ Бесплатный тариф для небольших проектов

**Следующие шаги:**
1. Настройте мониторинг
2. Добавьте резервное копирование
3. Настройте уведомления об ошибках
4. Оптимизируйте производительность

Удачи с вашим проектом! 🚀
