from telethon import TelegramClient, events, Button
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import sqlite3
import random
import threading
import time
import http.server
import socketserver
import pytz

# Конфигурация (загружается из переменных окружения)
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем данные из переменных окружения
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Проверяем наличие всех необходимых переменных
if not all([API_ID, API_HASH, BOT_TOKEN]):
    print("❌ ОШИБКА: Не все необходимые переменные окружения установлены!")
    print("📝 Убедитесь, что в .env файле или переменных окружения установлены:")
    print("   • API_ID")
    print("   • API_HASH") 
    print("   • BOT_TOKEN")
    print("🔧 Создайте .env файл на основе env.example")
    exit(1)

# Преобразуем API_ID в число
try:
    API_ID = int(API_ID)
except ValueError:
    print("❌ ОШИБКА: API_ID должен быть числом!")
    exit(1)

print("✅ Все переменные окружения загружены успешно")

# Функция для получения тайского времени
def get_thai_time():
    """Получить текущее время в тайском часовом поясе"""
    thai_tz = pytz.timezone('Asia/Bangkok')
    utc_now = datetime.now(pytz.UTC)
    thai_now = utc_now.astimezone(thai_tz)
    return thai_now

def get_thai_date():
    """Получить текущую дату в тайском часовом поясе"""
    return get_thai_time().date()

# Функция для внешнего keep-alive (для Render)
def external_keep_alive():
    """Функция для внешнего keep-alive через Render"""
    try:
        import urllib.request
        import urllib.error
        
        # Получаем внешний URL из переменных окружения
        external_url = os.getenv('RENDER_EXTERNAL_URL')
        if external_url:
            # Убираем trailing slash если есть
            if external_url.endswith('/'):
                external_url = external_url[:-1]
            
            # Пингуем внешний URL
            try:
                response = urllib.request.urlopen(f'{external_url}/ping', timeout=10)
                if response.getcode() == 200:
                    print(f"✅ External keep-alive successful: {time.strftime('%H:%M:%S')}")
                else:
                    print(f"⚠️ External keep-alive returned status: {response.getcode()}")
            except urllib.error.URLError as e:
                print(f"⚠️ External keep-alive failed: {e}")
            except Exception as e:
                print(f"⚠️ External keep-alive error: {e}")
        else:
            print("ℹ️ RENDER_EXTERNAL_URL not set, skipping external keep-alive")
            
    except Exception as e:
        print(f"❌ External keep-alive critical error: {e}")

client = TelegramClient('babybot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Создание таблиц (если их нет)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS families (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS family_members (
            family_id INTEGER,
            user_id INTEGER,
            role TEXT DEFAULT 'Родитель',
            name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedings (
            id INTEGER PRIMARY KEY,
            family_id INTEGER,
            author_id INTEGER,
            timestamp TEXT NOT NULL,
            author_role TEXT DEFAULT 'Родитель',
            author_name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS diapers (
            id INTEGER PRIMARY KEY,
            family_id INTEGER,
            author_id INTEGER,
            timestamp TEXT NOT NULL,
            author_role TEXT DEFAULT 'Родитель',
            author_name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    # Новая таблица для купания
    cur.execute("""
        CREATE TABLE IF NOT EXISTS baths (
            id INTEGER PRIMARY KEY,
            family_id INTEGER,
            author_id INTEGER,
            timestamp TEXT NOT NULL,
            author_role TEXT DEFAULT 'Родитель',
            author_name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    # Новая таблица для игр и выкладывания на живот
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY,
            family_id INTEGER,
            author_id INTEGER,
            timestamp TEXT NOT NULL,
            activity_type TEXT DEFAULT 'tummy_time',
            author_role TEXT DEFAULT 'Родитель',
            author_name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    # Новая таблица для сна
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sleep_sessions (
            id INTEGER PRIMARY KEY,
            family_id INTEGER,
            author_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT,
            is_active INTEGER DEFAULT 1,
            author_role TEXT DEFAULT 'Родитель',
            author_name TEXT DEFAULT 'Неизвестно',
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            family_id INTEGER,
            feed_interval INTEGER DEFAULT 3,
            diaper_interval INTEGER DEFAULT 2,
            tips_enabled INTEGER DEFAULT 1,
            tips_time_hour INTEGER DEFAULT 9,
            tips_time_minute INTEGER DEFAULT 0,
            bath_reminder_enabled INTEGER DEFAULT 1,
            bath_reminder_hour INTEGER DEFAULT 19,
            bath_reminder_minute INTEGER DEFAULT 0,
            bath_reminder_period INTEGER DEFAULT 1,
            activity_reminder_enabled INTEGER DEFAULT 1,
            activity_reminder_interval INTEGER DEFAULT 2,
            sleep_monitoring_enabled INTEGER DEFAULT 1,
            baby_age_months INTEGER DEFAULT 0,
            baby_birth_date TEXT,
            FOREIGN KEY (family_id) REFERENCES families (id)
        )
    """)
    
    # Добавляем новые колонки к существующей таблице settings, если их нет
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN tips_time_hour INTEGER DEFAULT 9")
        print("✅ Добавлена колонка tips_time_hour")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка tips_time_hour уже существует")
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN tips_time_minute INTEGER DEFAULT 0")
        print("✅ Добавлена колонка tips_time_minute")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка tips_time_minute уже существует")
    
    # Добавляем новые колонки для купания
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN bath_reminder_enabled INTEGER DEFAULT 1")
        print("✅ Добавлена колонка bath_reminder_enabled")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка bath_reminder_enabled уже существует")
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN bath_reminder_hour INTEGER DEFAULT 19")
        print("✅ Добавлена колонка bath_reminder_hour")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка bath_reminder_hour уже существует")
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN bath_reminder_minute INTEGER DEFAULT 0")
        print("✅ Добавлена колонка bath_reminder_minute")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка bath_reminder_minute уже существует")
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN bath_reminder_period INTEGER DEFAULT 1")
        print("✅ Добавлена колонка bath_reminder_period")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка bath_reminder_period уже существует")
    
    # Добавляем колонки для игр
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN activity_reminder_enabled INTEGER DEFAULT 1")
        print("✅ Добавлена колонка activity_reminder_enabled")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка activity_reminder_enabled уже существует")
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN activity_reminder_interval INTEGER DEFAULT 2")
        print("✅ Добавлена колонка activity_reminder_interval")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка activity_reminder_interval уже существует")
    
    # Добавляем колонки для сна
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN sleep_monitoring_enabled INTEGER DEFAULT 1")
        print("✅ Добавлена колонка sleep_monitoring_enabled")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка sleep_monitoring_enabled уже существует")
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN baby_age_months INTEGER DEFAULT 0")
        print("✅ Добавлена колонка baby_age_months")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка baby_age_months уже существует")
    
    try:
        cur.execute("ALTER TABLE settings ADD COLUMN baby_birth_date TEXT")
        print("✅ Добавлена колонка baby_birth_date")
    except sqlite3.OperationalError:
        print("ℹ️ Колонка baby_birth_date уже существует")
    
    # Обновляем существующие записи, устанавливая значения по умолчанию
    cur.execute("UPDATE settings SET tips_time_hour = 9 WHERE tips_time_hour IS NULL")
    cur.execute("UPDATE settings SET tips_time_minute = 0 WHERE tips_time_minute IS NULL")
    cur.execute("UPDATE settings SET bath_reminder_enabled = 1 WHERE bath_reminder_enabled IS NULL")
    cur.execute("UPDATE settings SET bath_reminder_hour = 19 WHERE bath_reminder_hour IS NULL")
    cur.execute("UPDATE settings SET bath_reminder_minute = 0 WHERE bath_reminder_minute IS NULL")
    cur.execute("UPDATE settings SET bath_reminder_period = 1 WHERE bath_reminder_period IS NULL")
    cur.execute("UPDATE settings SET activity_reminder_enabled = 1 WHERE activity_reminder_enabled IS NULL")
    cur.execute("UPDATE settings SET activity_reminder_interval = 2 WHERE activity_reminder_enabled IS NULL")
    cur.execute("UPDATE settings SET sleep_monitoring_enabled = 1 WHERE sleep_monitoring_enabled IS NULL")
    cur.execute("UPDATE settings SET baby_age_months = 0 WHERE baby_age_months IS NULL")
    
    # Миграция таблиц feedings и diapers
    try:
        # Проверяем, есть ли колонка family_id в таблице feedings
        cur.execute("PRAGMA table_info(feedings)")
        columns = [col[1] for col in cur.fetchall()]
        
        if 'family_id' not in columns:
            print("🔄 Мигрируем таблицу feedings...")
            # Создаем временную таблицу с новой структурой
            cur.execute("""
                CREATE TABLE feedings_new (
                    id INTEGER PRIMARY KEY,
                    family_id INTEGER,
                    author_id INTEGER,
                    timestamp TEXT NOT NULL,
                    author_role TEXT DEFAULT 'Родитель',
                    author_name TEXT DEFAULT 'Неизвестно',
                    FOREIGN KEY (family_id) REFERENCES families (id)
                )
            """)
            
            # Копируем данные из старой таблицы
            cur.execute("SELECT id, user_id, timestamp FROM feedings")
            old_data = cur.fetchall()
            
            for row in old_data:
                # Для каждой записи создаем временную семью
                temp_family_id = create_family(f"Миграция {row[0]}", row[1])
                cur.execute("INSERT INTO feedings_new (family_id, author_id, timestamp, author_role, author_name) VALUES (?, ?, ?, ?, ?)",
                           (temp_family_id, row[1], row[2], 'Родитель', 'Неизвестно'))
            
            # Удаляем старую таблицу и переименовываем новую
            cur.execute("DROP TABLE feedings")
            cur.execute("ALTER TABLE feedings_new RENAME TO feedings")
            print("✅ Таблица feedings мигрирована")
        else:
            print("ℹ️ Таблица feedings уже имеет правильную структуру")
            
    except sqlite3.OperationalError as e:
        print(f"ℹ️ Миграция feedings: {e}")
    
    try:
        # Проверяем, есть ли колонка family_id в таблице diapers
        cur.execute("PRAGMA table_info(diapers)")
        columns = [col[1] for col in cur.fetchall()]
        
        if 'family_id' not in columns:
            print("🔄 Мигрируем таблицу diapers...")
            # Создаем временную таблицу с новой структурой
            cur.execute("""
                CREATE TABLE diapers_new (
                    id INTEGER PRIMARY KEY,
                    family_id INTEGER,
                    author_id INTEGER,
                    timestamp TEXT NOT NULL,
                    author_role TEXT DEFAULT 'Родитель',
                    author_name TEXT DEFAULT 'Неизвестно',
                    FOREIGN KEY (family_id) REFERENCES families (id)
                )
            """)
            
            # Копируем данные из старой таблицы
            cur.execute("SELECT id, user_id, timestamp FROM diapers")
            old_data = cur.fetchall()
            
            for row in old_data:
                # Для каждой записи создаем временную семью
                temp_family_id = create_family(f"Миграция {row[0]}", row[1])
                cur.execute("INSERT INTO diapers_new (family_id, author_id, timestamp, author_role, author_name) VALUES (?, ?, ?, ?, ?)",
                           (temp_family_id, row[1], row[2], 'Родитель', 'Неизвестно'))
            
            # Удаляем старую таблицу и переименовываем новую
            cur.execute("DROP TABLE diapers")
            cur.execute("ALTER TABLE diapers_new RENAME TO diapers")
            print("✅ Таблица diapers мигрирована")
        else:
            print("ℹ️ Таблица diapers уже имеет правильную структуру")
            
    except sqlite3.OperationalError as e:
        print(f"ℹ️ Миграция diapers: {e}")
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована/обновлена")

# Функции для работы с базой данных
def get_family_id(user_id):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT family_id FROM family_members WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    family_id = result[0] if result else None
    print(f"DEBUG: get_family_id({user_id}) = {family_id}")
    return family_id

def create_family(name, user_id):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    cur.execute("INSERT INTO families (name) VALUES (?)", (name,))
    family_id = cur.lastrowid
    
    cur.execute("INSERT INTO family_members (family_id, user_id) VALUES (?, ?)", (family_id, user_id))
    cur.execute("INSERT INTO settings (family_id) VALUES (?)", (family_id,))
    
    conn.commit()
    conn.close()
    return family_id

def join_family_by_code(code, user_id):
    """Присоединить пользователя к семье по коду приглашения"""
    try:
        family_id = int(code)
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        
        # Проверяем, существует ли семья
        cur.execute("SELECT id, name FROM families WHERE id = ?", (family_id,))
        family = cur.fetchone()
        
        if not family:
            conn.close()
            return None, "Семья не найдена"
        
        # Проверяем, не состоит ли пользователь уже в семье
        cur.execute("SELECT family_id FROM family_members WHERE user_id = ?", (user_id,))
        existing = cur.fetchone()
        
        if existing:
            conn.close()
            return None, "Вы уже состоите в семье"
        
        # Добавляем пользователя в семью
        cur.execute("INSERT INTO family_members (family_id, user_id) VALUES (?, ?)", (family_id, user_id))
        conn.commit()
        conn.close()
        
        return family_id, family[1]  # family_id, family_name
    except ValueError:
        return None, "Неверный код приглашения"
    except Exception as e:
        return None, f"Ошибка: {str(e)}"

def invite_code_for(family_id):
    # В существующей базе нет колонки invite_code, возвращаем ID семьи
    return str(family_id)

def get_family_name(family_id):
    """Получить название семьи по ID"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM families WHERE id = ?", (family_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else "Неизвестная семья"

def get_member_info(user_id):
    """Получить информацию о члене семьи"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT role, name FROM family_members WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result[0], result[1]  # role, name
    return "Родитель", "Неизвестно"

def set_member_role(user_id, role, name):
    """Установить роль и имя для члена семьи"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("UPDATE family_members SET role = ?, name = ? WHERE user_id = ?", (role, name, user_id))
    conn.commit()
    conn.close()

def get_family_members_with_roles(family_id):
    """Получить всех членов семьи с ролями"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, role, name FROM family_members WHERE family_id = ?", (family_id,))
    members = cur.fetchall()
    conn.close()
    return members

def add_feeding(user_id, minutes_ago=0):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Получаем family_id пользователя
    family_id = get_family_id(user_id)
    if not family_id:
        # Если пользователь не в семье, создаем временную семью
        family_id = create_family("Временная семья", user_id)
    
    # Получаем информацию об авторе
    role, name = get_member_info(user_id)
    
    timestamp = get_thai_time() - timedelta(minutes=minutes_ago)
    cur.execute("INSERT INTO feedings (family_id, author_id, timestamp, author_role, author_name) VALUES (?, ?, ?, ?, ?)", 
                (family_id, user_id, timestamp.isoformat(), role, name))
    conn.commit()
    conn.close()

def add_diaper_change(user_id, minutes_ago=0):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Получаем family_id пользователя
    family_id = get_family_id(user_id)
    if not family_id:
        # Если пользователь не в семье, создаем временную семью
        family_id = create_family("Временная семья", user_id)
    
    # Получаем информацию об авторе
    role, name = get_member_info(user_id)
    
    timestamp = get_thai_time() - timedelta(minutes=minutes_ago)
    cur.execute("INSERT INTO diapers (family_id, author_id, timestamp, author_role, author_name) VALUES (?, ?, ?, ?, ?)", 
                (family_id, user_id, timestamp.isoformat(), role, name))
    conn.commit()
    conn.close()

def get_last_feeding_time(user_id):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Получаем family_id пользователя
    family_id = get_family_id(user_id)
    if not family_id:
        return None
    
    cur.execute("SELECT timestamp FROM feedings WHERE family_id = ? ORDER BY timestamp DESC LIMIT 1", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return datetime.fromisoformat(result[0])
    return None

def get_last_diaper_change_for_family(family_id):
    """Получить время последней смены подгузника для семьи"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    cur.execute("SELECT timestamp FROM diapers WHERE family_id = ? ORDER BY timestamp DESC LIMIT 1", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return datetime.fromisoformat(result[0])
    return None

def get_last_feeding_time_for_family(family_id):
    """Получить время последнего кормления для семьи"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    cur.execute("SELECT timestamp FROM feedings WHERE family_id = ? ORDER BY timestamp DESC LIMIT 1", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return datetime.fromisoformat(result[0])
    return None

def get_user_intervals(family_id):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT feed_interval, diaper_interval FROM settings WHERE family_id = ?", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    return 3, 2

def set_user_interval(family_id, feed_interval=None, diaper_interval=None):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    if feed_interval is not None:
        cur.execute("UPDATE settings SET feed_interval = ? WHERE family_id = ?", (feed_interval, family_id))
    if diaper_interval is not None:
        cur.execute("UPDATE settings SET diaper_interval = ? WHERE family_id = ?", (diaper_interval, family_id))
    conn.commit()
    conn.close()

def is_tips_enabled(family_id):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT tips_enabled FROM settings WHERE family_id = ?", (family_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 1

def toggle_tips(family_id):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("UPDATE settings SET tips_enabled = CASE WHEN tips_enabled = 1 THEN 0 ELSE 1 END WHERE family_id = ?", (family_id,))
    conn.commit()
    conn.close()

def set_tips_time(family_id, hour, minute):
    """Установить время рассылки советов"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("UPDATE settings SET tips_time_hour = ?, tips_time_minute = ? WHERE family_id = ?", (hour, minute, family_id))
    conn.commit()
    conn.close()

def get_tips_time(family_id):
    """Получить время рассылки советов"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT tips_time_hour, tips_time_minute FROM settings WHERE family_id = ?", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    return 9, 0  # значения по умолчанию

def get_feedings_by_day(user_id, date):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Получаем family_id пользователя
    family_id = get_family_id(user_id)
    if not family_id:
        return []
    
    start_date = datetime.combine(date, datetime.min.time()).isoformat()
    end_date = datetime.combine(date, datetime.max.time()).isoformat()
    cur.execute("SELECT id, timestamp, author_role, author_name FROM feedings WHERE family_id = ? AND timestamp BETWEEN ? AND ? ORDER BY timestamp", 
                (family_id, start_date, end_date))
    result = cur.fetchall()
    conn.close()
    return result

def get_diapers_by_day(user_id, date):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Получаем family_id пользователя
    family_id = get_family_id(user_id)
    if not family_id:
        return []
    
    start_date = datetime.combine(date, datetime.min.time()).isoformat()
    end_date = datetime.combine(date, datetime.max.time()).isoformat()
    cur.execute("SELECT id, timestamp, author_role, author_name FROM diapers WHERE family_id = ? AND timestamp BETWEEN ? AND ? ORDER BY timestamp", 
                (family_id, start_date, end_date))
    result = cur.fetchall()
    conn.close()
    return result

def delete_entry(table, entry_id):
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

# Функция для получения случайного совета
def get_random_tip():
    try:
        import csv
        tips = []
        
        # Читаем советы из CSV файла
        with open("data/advice.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tips.append(row["tip"])
        
        if tips:
            return random.choice(tips)
        else:
            return "Пока нет доступных советов."
            
    except Exception as e:
        print(f"Ошибка при чтении советов: {e}")
        # Возвращаем запасной совет в случае ошибки
        return "Помните, что каждый ребенок уникален и развивается в своем темпе."

# Новые функции для купания
def add_bath(user_id, minutes_ago=0):
    """Добавить запись о купании"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    family_id = get_family_id(user_id)
    if not family_id:
        family_id = create_family("Временная семья", user_id)
    
    role, name = get_member_info(user_id)
    timestamp = get_thai_time() - timedelta(minutes=minutes_ago)
    
    cur.execute("INSERT INTO baths (family_id, author_id, timestamp, author_role, author_name) VALUES (?, ?, ?, ?, ?)", 
                (family_id, user_id, timestamp.isoformat(), role, name))
    conn.commit()
    conn.close()

def get_last_bath_time_for_family(family_id):
    """Получить время последнего купания для семьи"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    cur.execute("SELECT timestamp FROM baths WHERE family_id = ? ORDER BY timestamp DESC LIMIT 1", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return datetime.fromisoformat(result[0])
    return None

def get_bath_settings(family_id):
    """Получить настройки напоминаний о купании"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT bath_reminder_enabled, bath_reminder_hour, bath_reminder_minute, bath_reminder_period FROM settings WHERE family_id = ?", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result[0], result[1], result[2], result[3]
    return 1, 19, 0, 1  # значения по умолчанию

def set_bath_settings(family_id, enabled=None, hour=None, minute=None, period=None):
    """Установить настройки напоминаний о купании"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    if enabled is not None:
        cur.execute("UPDATE settings SET bath_reminder_enabled = ? WHERE family_id = ?", (enabled, family_id))
    if hour is not None:
        cur.execute("UPDATE settings SET bath_reminder_hour = ? WHERE family_id = ?", (hour, family_id))
    if minute is not None:
        cur.execute("UPDATE settings SET bath_reminder_minute = ? WHERE family_id = ?", (minute, family_id))
    if period is not None:
        cur.execute("UPDATE settings SET bath_reminder_period = ? WHERE family_id = ?", (period, family_id))
    
    conn.commit()
    conn.close()

# Новые функции для игр и активностей
def add_activity(user_id, activity_type="tummy_time", minutes_ago=0):
    """Добавить запись об активности"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    family_id = get_family_id(user_id)
    if not family_id:
        family_id = create_family("Временная семья", user_id)
    
    role, name = get_member_info(user_id)
    timestamp = get_thai_time() - timedelta(minutes=minutes_ago)
    
    cur.execute("INSERT INTO activities (family_id, author_id, timestamp, activity_type, author_role, author_name) VALUES (?, ?, ?, ?, ?, ?)", 
                (family_id, user_id, timestamp.isoformat(), activity_type, role, name))
    conn.commit()
    conn.close()

def get_last_activity_time_for_family(family_id, activity_type="tummy_time"):
    """Получить время последней активности для семьи"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    cur.execute("SELECT timestamp FROM activities WHERE family_id = ? AND activity_type = ? ORDER BY timestamp DESC LIMIT 1", 
                (family_id, activity_type))
    result = cur.fetchone()
    conn.close()
    if result:
        return datetime.fromisoformat(result[0])
    return None

def get_activity_settings(family_id):
    """Получить настройки напоминаний об активностях"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT activity_reminder_enabled, activity_reminder_interval, baby_age_months FROM settings WHERE family_id = ?", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result[0], result[1], result[2]
    return 1, 2, 0  # значения по умолчанию

def set_activity_settings(family_id, enabled=None, interval=None, age_months=None):
    """Установить настройки напоминаний об активностях"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    if enabled is not None:
        cur.execute("UPDATE settings SET activity_reminder_enabled = ? WHERE family_id = ?", (enabled, family_id))
    if interval is not None:
        cur.execute("UPDATE settings SET activity_reminder_interval = ? WHERE family_id = ?", (interval, family_id))
    if age_months is not None:
        cur.execute("UPDATE settings SET baby_age_months = ? WHERE family_id = ?", (age_months, family_id))
    
    conn.commit()
    conn.close()

def set_baby_birth_date(family_id, birth_date):
    """Установить дату рождения малыша"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("UPDATE settings SET baby_birth_date = ? WHERE family_id = ?", (birth_date, family_id))
    conn.commit()
    conn.close()

def get_baby_birth_date(family_id):
    """Получить дату рождения малыша"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT baby_birth_date FROM settings WHERE family_id = ?", (family_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def calculate_baby_age_months(birth_date_str):
    """Вычислить возраст малыша в месяцах по дате рождения"""
    if not birth_date_str:
        return 0
    
    try:
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        current_date = get_thai_date()
        age_delta = current_date - birth_date.date()
        age_months = age_delta.days / 30.44  # Среднее количество дней в месяце
        return int(age_months)
    except ValueError:
        return 0

def get_age_appropriate_activities(age_months):
    """Получить рекомендации по активностям в зависимости от возраста"""
    if age_months < 1:
        return {
            "tummy_time": "Выкладывание на живот 2-3 раза в день по 3-5 минут",
            "play": "Черно-белые картинки, погремушки на расстоянии 20-30 см",
            "massage": "Легкий массаж ручек и ножек"
        }
    elif age_months < 3:
        return {
            "tummy_time": "Выкладывание на живот 3-4 раза в день по 5-10 минут",
            "play": "Цветные игрушки, подвесные мобили, песенки",
            "massage": "Массаж всего тела, гимнастика"
        }
    elif age_months < 6:
        return {
            "tummy_time": "Выкладывание на живот 4-5 раз в день по 10-15 минут",
            "play": "Игрушки для хватания, зеркало, прятки",
            "massage": "Активная гимнастика, упражнения на перевороты"
        }
    elif age_months < 9:
        return {
            "tummy_time": "Ползание, упражнения на координацию",
            "play": "Пирамидки, кубики, игры в прятки",
            "massage": "Упражнения для подготовки к ходьбе"
        }
    else:
        return {
            "tummy_time": "Ходьба с поддержкой, активные игры",
            "play": "Строительство, рисование, ролевые игры",
            "massage": "Спортивные упражнения, танцы"
        }

# Новые функции для сна
def start_sleep_session(user_id):
    """Начать сессию сна"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    family_id = get_family_id(user_id)
    if not family_id:
        family_id = create_family("Временная семья", user_id)
    
    role, name = get_member_info(user_id)
    start_time = get_thai_time()
    
    # Завершаем предыдущую активную сессию сна
    cur.execute("UPDATE sleep_sessions SET is_active = 0, end_time = ? WHERE family_id = ? AND is_active = 1", 
                (start_time.isoformat(), family_id))
    
    # Создаем новую сессию
    cur.execute("INSERT INTO sleep_sessions (family_id, author_id, start_time, is_active, author_role, author_name) VALUES (?, ?, ?, 1, ?, ?)", 
                (family_id, user_id, start_time.isoformat(), role, name))
    conn.commit()
    conn.close()

def end_sleep_session(user_id):
    """Завершить сессию сна"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    family_id = get_family_id(user_id)
    if not family_id:
        return False
    
    end_time = get_thai_time()
    
    cur.execute("UPDATE sleep_sessions SET is_active = 0, end_time = ? WHERE family_id = ? AND is_active = 1", 
                (end_time.isoformat(), family_id))
    conn.commit()
    conn.close()
    
    # Возвращаем длительность сна
    cur.execute("SELECT start_time FROM sleep_sessions WHERE family_id = ? AND end_time = ? ORDER BY id DESC LIMIT 1", 
                (family_id, end_time.isoformat()))
    result = cur.fetchone()
    conn.close()
    
    if result:
        start_time = datetime.fromisoformat(result[0])
        duration = end_time - start_time
        return duration
    return None

def get_active_sleep_session(family_id):
    """Получить активную сессию сна для семьи"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    cur.execute("SELECT id, start_time, author_role, author_name FROM sleep_sessions WHERE family_id = ? AND is_active = 1 ORDER BY start_time DESC LIMIT 1", (family_id,))
    result = cur.fetchone()
    conn.close()
    
    if result:
        return {
            "id": result[0],
            "start_time": datetime.fromisoformat(result[1]),
            "author_role": result[2],
            "author_name": result[3]
        }
    return None

def get_sleep_settings(family_id):
    """Получить настройки мониторинга сна"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT sleep_monitoring_enabled FROM settings WHERE family_id = ?", (family_id,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result[0]
    return 1  # значение по умолчанию

def set_sleep_settings(family_id, enabled):
    """Установить настройки мониторинга сна"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("UPDATE settings SET sleep_monitoring_enabled = ? WHERE family_id = ?", (enabled, family_id))
    conn.commit()
    conn.close()

def should_wake_for_feeding(sleep_start_time, feed_interval_hours):
    """Проверить, нужно ли разбудить для кормления"""
    current_time = get_thai_time()
    sleep_duration = current_time - sleep_start_time
    sleep_hours = sleep_duration.total_seconds() / 3600
    
    # Если сон длится дольше интервала кормления, нужно разбудить
    return sleep_hours >= feed_interval_hours

# Функции для отображения настроек
async def show_bath_settings(event):
    """Показать настройки купания"""
    uid = event.sender_id
    fid = get_family_id(uid)
    
    if not fid:
        await event.respond("❌ Сначала создайте семью.")
        return
    
    enabled, hour, minute, period = get_bath_settings(fid)
    status = "🔔 Включены" if enabled else "🔕 Отключены"
    
    message = (
        f"🛁 **Настройки напоминаний о купании**\n\n"
        f"📊 Статус: {status}\n"
        f"🕐 Время: {hour:02d}:{minute:02d}\n"
        f"📅 Период: {period} день(ей)\n\n"
        f"💡 Выберите, что хотите изменить:"
    )
    
    buttons = [
        [Button.inline("🕐 Изменить время", b"bath_change_time")],
        [Button.inline("📅 Изменить период", b"bath_change_period")],
        [Button.inline("🔙 Назад к настройкам", b"back_to_settings")]
    ]
    
    await event.edit(message, buttons=buttons)

async def show_activity_settings(event):
    """Показать настройки игр"""
    uid = event.sender_id
    fid = get_family_id(uid)
    
    if not fid:
        await event.respond("❌ Сначала создайте семью.")
        return
    
    enabled, interval, age_months = get_activity_settings(fid)
    status = "🔔 Включены" if enabled else "🔕 Отключены"
    
    activities = get_age_appropriate_activities(age_months)
    
    # Проверяем, есть ли дата рождения
    baby_birth_date = get_baby_birth_date(fid)
    age_info = ""
    if baby_birth_date:
        age_info = f"👶 Возраст: {age_months} мес. (автоматически по дате рождения: {baby_birth_date})"
    else:
        age_info = f"👶 Возраст: {age_months} мес. (установите дату рождения в 'Управление семьей')"
    
    message = (
        f"🎮 **Настройки напоминаний об играх**\n\n"
        f"📊 Статус: {status}\n"
        f"⏰ Интервал: {interval} ч.\n"
        f"{age_info}\n\n"
        f"💡 **Рекомендации для возраста {age_months} мес.:**\n"
        f"🦵 Выкладывание на живот: {activities['tummy_time']}\n"
        f"🎯 Игры: {activities['play']}\n"
        f"💆 Массаж: {activities['massage']}\n\n"
        f"💡 Выберите, что хотите изменить:"
    )
    
    buttons = [
        [Button.inline("⏰ Изменить интервал", b"activity_change_interval")],
        [Button.inline("🔙 Назад к настройкам", b"back_to_settings")]
    ]
    
    await event.edit(message, buttons=buttons)

async def show_sleep_status(event):
    """Показать статус сна"""
    uid = event.sender_id
    fid = get_family_id(uid)
    
    if not fid:
        await event.respond("❌ Сначала создайте семью.")
        return
    
    active_sleep = get_active_sleep_session(fid)
    feed_interval, _ = get_user_intervals(fid)
    
    if active_sleep:
        sleep_duration = get_thai_time() - active_sleep["start_time"]
        hours = int(sleep_duration.total_seconds() // 3600)
        minutes = int((sleep_duration.total_seconds() % 3600) // 60)
        
        # Проверяем, нужно ли разбудить для кормления
        should_wake = should_wake_for_feeding(active_sleep["start_time"], feed_interval)
        
        if should_wake:
            status = "⚠️ **ВНИМАНИЕ!** Малыш спит дольше интервала кормления!"
            recommendation = "💡 Рекомендуется разбудить для кормления"
        else:
            status = "😴 Малыш спит спокойно"
            remaining = feed_interval - (sleep_duration.total_seconds() / 3600)
            recommendation = f"💡 Можно не будить еще {remaining:.1f} ч."
        
        message = (
            f"😴 **Статус сна**\n\n"
            f"{status}\n\n"
            f"⏰ Начало сна: {active_sleep['start_time'].strftime('%H:%M')}\n"
            f"🕐 Длительность: {hours}ч {minutes}м\n"
            f"👤 Уложил: {active_sleep['author_role']} {active_sleep['author_name']}\n"
            f"🔄 Интервал кормления: {feed_interval} ч.\n\n"
            f"{recommendation}"
        )
    else:
        message = (
            f"😴 **Статус сна**\n\n"
            f"🌅 Малыш не спит\n"
            f"💡 Нажмите кнопку ниже, когда малыш заснет"
        )
    
    buttons = [
        [Button.inline("🌙 Малыш заснул", b"sleep_start")],
        [Button.inline("🔙 Назад", b"back_to_sleep")]
    ]
    
    await event.edit(message, buttons=buttons)

async def show_sleep_history(event):
    """Показать историю сна"""
    uid = event.sender_id
    fid = get_family_id(uid)
    
    if not fid:
        await event.respond("❌ Сначала создайте семью.")
        return
    
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Получаем последние 5 сессий сна
    cur.execute("""
        SELECT start_time, end_time, author_role, author_name 
        FROM sleep_sessions 
        WHERE family_id = ? AND end_time IS NOT NULL 
        ORDER BY start_time DESC LIMIT 5
    """, (fid,))
    
    sessions = cur.fetchall()
    conn.close()
    
    if sessions:
        message = "😴 **История сна (последние 5 сессий):**\n\n"
        
        for i, session in enumerate(sessions, 1):
            start_time = datetime.fromisoformat(session[0])
            end_time = datetime.fromisoformat(session[1])
            duration = end_time - start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            message += (
                f"{i}. {start_time.strftime('%d.%m %H:%M')} - "
                f"{end_time.strftime('%H:%M')} "
                f"({hours}ч {minutes}м)\n"
                f"   👤 {session[2]} {session[3]}\n\n"
            )
    else:
        message = "😴 **История сна**\n\nПока нет завершенных сессий сна."
    
    buttons = [
        [Button.inline("🔙 Назад", b"back_to_sleep")]
    ]
    
    await event.edit(message, buttons=buttons)



# ... existing code ...

# Инициализация
init_db()
scheduler = AsyncIOScheduler()

# Добавляем задачу для поддержания активности (каждые 5 минут)
def keep_alive_ping():
    """Функция для поддержания активности бота"""
    try:
        import urllib.request
        import urllib.error
        
        # Пингуем собственный health check сервер
        try:
            response = urllib.request.urlopen('http://localhost:8000/ping', timeout=5)
            if response.getcode() == 200:
                print(f"✅ Keep-alive ping successful: {time.strftime('%H:%M:%S')}")
            else:
                print(f"⚠️ Keep-alive ping returned status: {response.getcode()}")
        except urllib.error.URLError as e:
            print(f"⚠️ Keep-alive ping failed: {e}")
        except Exception as e:
            print(f"⚠️ Keep-alive ping error: {e}")
            
    except Exception as e:
        print(f"❌ Keep-alive ping critical error: {e}")

# Добавляем задачу в планировщик (каждые 5 минут)
scheduler.add_job(keep_alive_ping, 'interval', minutes=5, id='keep_alive_ping')
print("⏰ Keep-alive ping scheduled every 5 minutes")

# Добавляем внешний keep-alive для Render (каждые 3 минуты)
scheduler.add_job(external_keep_alive, 'interval', minutes=3, id='external_keep_alive')
print("⏰ External keep-alive scheduled every 3 minutes")

# Состояния ожидания
family_creation_pending = {}
manual_feeding_pending = {}
join_pending = {}
edit_pending = {}
edit_role_pending = {}
bath_pending = {}
activity_pending = {}
sleep_pending = {}
baby_birth_pending = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    fid = get_family_id(uid)
    
    if fid:
        # Пользователь уже в семье
        family_name = get_family_name(fid)
        role, name = get_member_info(uid)
        
        welcome_message = (
            f"👶 **Добро пожаловать в BabyCareBot!**\n\n"
            f"🏠 **Ваша семья:** {family_name}\n"
            f"👤 **Ваша роль:** {role} {name}\n\n"
            f"💡 Я помогу следить за малышом и координировать уход в семье!"
        )
    else:
        # Пользователь не в семье
        welcome_message = (
            f"👶 **Добро пожаловать в BabyCareBot!**\n\n"
            f"🎯 **Что я умею:**\n"
            f"• 🍼 Отслеживать и записывать кормления\n"
            f"• 🧷 Записывать смены подгузников\n"
            f"• 🛁 Настраивать напоминания о купании в настройках\n"
            f"• 🎮 Умные напоминания об играх (не раньше чем за 20 мин до еды)\n"
            f"• 😴 Мониторить сон и предупреждать о кормлении\n"
            f"• 📊 Показывать историю и статистику\n"
            f"• ⏰ Напоминать о важных событиях\n"
            f"• 👥 Координировать уход в семье\n\n"
            f"🚀 **Для начала работы:**\n"
            f"1️⃣ Создайте семью или присоединитесь к существующей\n"
            f"2️⃣ Настройте роли членов семьи\n"
            f"3️⃣ Начните записывать события\n\n"
            f"💡 Нажмите '⚙ Настройки' для создания семьи!"
        )
    
    # Всегда показываем полное меню
    buttons = [
        [Button.text("🍼 Кормление"), Button.text("🧷 Смена подгузника")],
        [Button.text("😴 Сон"), Button.text("📜 История")],
        [Button.text("💡 Совет"), Button.text("⚙ Настройки")],
        [Button.url("📊 Дашборд", "https://babycarebot-dashboard.vercel.app")]
    ]
    
    await event.respond(welcome_message, buttons=buttons)

@client.on(events.NewMessage(pattern='🍼 Кормление'))
async def feeding_menu(event):
    """Показать статус кормления с возможностью отметить кормление"""
    uid = event.sender_id
    fid = get_family_id(uid)
    
    if not fid:
        await event.respond("❌ Сначала создайте семью.")
        return
    
    # Получаем интервал кормления
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    cur.execute("SELECT feed_interval FROM settings WHERE family_id = ?", (fid,))
    interval_result = cur.fetchone()
    feed_interval = interval_result[0] if interval_result else 3
    
    # Получаем время последнего кормления
    last_feeding = get_last_feeding_time_for_family(fid)
    
    if last_feeding:
        time_since_last = get_thai_time() - last_feeding
        hours_since_last = time_since_last.total_seconds() / 3600
        minutes_since_last = time_since_last.total_seconds() / 60
        
        # Определяем статус
        if hours_since_last < feed_interval:
            status = "✅ Время кормления еще не подошло"
            remaining = feed_interval - hours_since_last
            status_emoji = "🟢"
        elif hours_since_last < (feed_interval + 0.5):
            status = "⚠️ Пора кормить!"
            remaining = 0
            status_emoji = "🟡"
        else:
            status = "🚨 Долго не кормили!"
            remaining = 0
            status_emoji = "🔴"
        
        message = (
            f"{status_emoji} **Статус кормления**\n\n"
            f"⏰ Последнее кормление: {last_feeding.strftime('%H:%M')}\n"
            f"🕐 Прошло: {hours_since_last:.1f} ч. ({minutes_since_last:.0f} мин.)\n"
            f"🔄 Интервал: {feed_interval} ч.\n"
            f"📊 Статус: {status}\n"
        )
        
        if remaining > 0:
            message += f"⏳ До следующего кормления: {remaining:.1f} ч."
        else:
            message += f"💡 Рекомендуется покормить сейчас!"
    else:
        message = (
            f"🍼 **Статус кормления**\n\n"
            f"👶 Кормлений еще не было\n"
            f"🔄 Рекомендуемый интервал: {feed_interval} ч.\n"
            f"💡 Запишите первое кормление!"
        )
    
    conn.close()
    
    # Добавляем кнопки для быстрых действий
    buttons = [
        [Button.inline("🍼 Кормить сейчас", b"feed_now")],
        [Button.inline("15 мин назад", b"feed_15")],
        [Button.inline("30 мин назад", b"feed_30")],
        [Button.inline("🕒 Указать время", b"feed_manual")]
    ]
    
    await event.respond(message, buttons=buttons)

@client.on(events.NewMessage(pattern='🧷 Смена подгузника'))
async def diaper_menu(event):
    buttons = [
        [Button.inline("Сейчас", b"diaper_now")],
        [Button.inline("🕒 Указать вручную", b"diaper_manual")],
    ]
    await event.respond("🧷 Когда была смена подгузника?", buttons=buttons)

@client.on(events.NewMessage(pattern='⏰ Когда ел?'))
async def last_feed(event):
    time = get_last_feeding_time(event.sender_id)
    if time:
        delta = datetime.now() - time
        h, m = divmod(int(delta.total_seconds() // 60), 60)
        await event.respond(f"🍼 Последнее кормление было {h}ч {m}м назад.")
    else:
        await event.respond("❌ Пока нет записей о кормлении.")

@client.on(events.NewMessage(pattern='💡 Совет'))
async def tip_command(event):
    tip = get_random_tip()
    await event.respond(tip)

@client.on(events.NewMessage(pattern='ℹ️ Как это работает'))
async def how_it_works(event):
    """Показать инструкцию по использованию бота"""
    message = (
        f"📚 **Как работает BabyCareBot**\n\n"
        f"🎯 **Основные функции:**\n\n"
        f"🍼 **Кормление:**\n"
        f"• Записывайте время кормления\n"
        f"• Получайте напоминания\n"
        f"• Отслеживайте интервалы\n\n"
        f"🧷 **Смена подгузников:**\n"
        f"• Фиксируйте время смены\n"
        f"• Контролируйте регулярность\n"
        f"• Анализируйте паттерны\n\n"
        f"👥 **Семейная координация:**\n"
        f"• Создайте семью\n"
        f"• Назначьте роли (Мама, Папа, Бабушка)\n"
        f"• Отслеживайте, кто что делал\n\n"
        f"📊 **История и статистика:**\n"
        f"• Просматривайте записи по дням\n"
        f"• Анализируйте тенденции\n"
        f"• Планируйте уход\n\n"
        f"⚙️ **Настройки:**\n"
        f"• Интервалы кормления и смен\n"
        f"• Время рассылки советов\n"
        f"• Управление семьей\n\n"
        f"🚀 **Начните с создания семьи в настройках!**"
    )
    
    buttons = [
        [Button.inline("⚙️ Настройки", b"settings")]
    ]
    
    await event.respond(message, buttons=buttons)

@client.on(events.NewMessage(pattern='👤 Моя роль'))
async def my_role_command(event):
    """Показать и изменить роль пользователя"""
    uid = event.sender_id
    fid = get_family_id(uid)
    
    if not fid:
        await event.respond("❌ Сначала создайте семью.")
        return
    
    role, name = get_member_info(uid)
    
    message = (
        f"👤 **Ваша роль в семье:**\n\n"
        f"🎭 Роль: {role}\n"
        f"📝 Имя: {name}\n\n"
        f"💡 Нажмите кнопку ниже, чтобы изменить"
    )
    
    buttons = [
        [Button.inline("✏️ Изменить роль", b"edit_role")],
        [Button.inline("🔙 Назад", b"back_to_main")]
    ]
    
    await event.respond(message, buttons=buttons)



@client.on(events.NewMessage(pattern='⚙ Настройки'))
async def settings_menu(event):
    fid = get_family_id(event.sender_id)
    if not fid:
        # Если пользователь не в семье, показываем опции для работы с семьей
        buttons = [
            [Button.inline("👨‍👩‍👧 Создать семью", b"create_family")],
            [Button.inline("👨‍👩‍👧 Управление семьей", b"family_management")]
        ]
        await event.respond("⚙ Настройки:\n\n❗ Сначала создайте семью или присоединитесь к существующей:", buttons=buttons)
        return
    
    feed_i, diaper_i = get_user_intervals(fid)
    tips_on = is_tips_enabled(fid)
    tips_label = "🔕 Отключить советы" if tips_on else "🔔 Включить советы"
    tips_hour, tips_minute = get_tips_time(fid)
    
    # Получаем настройки купания
    bath_enabled, bath_hour, bath_minute, bath_period = get_bath_settings(fid)
    bath_label = "🔕 Отключить купание" if bath_enabled else "🔔 Включить купание"
    
    # Получаем настройки игр
    activity_enabled, activity_interval, baby_age = get_activity_settings(fid)
    activity_label = "🔕 Отключить игры" if activity_enabled else "🔔 Включить игры"
    
    buttons = [
        [Button.inline(f"🍽 Интервал кормления: {feed_i}ч", b"set_feed")],
        [Button.inline(f"🧷 Интервал подгузника: {diaper_i}ч", b"set_diaper")],
        [Button.inline(tips_label, b"toggle_tips")],
        [Button.inline(f"🕐 Время советов: {tips_hour:02d}:{tips_minute:02d}", b"set_tips_time")],
        [Button.inline(bath_label, b"toggle_bath")],
        [Button.inline(f"🛁 Купание: {bath_hour:02d}:{bath_minute:02d} / {bath_period}д", b"bath_settings")],
        [Button.inline(activity_label, b"activity_toggle")],
        [Button.inline(f"🎮 Игры: {activity_interval}ч / {baby_age}мес", b"activity_settings")],
        [Button.inline("👤 Моя роль", b"my_role")],
        [Button.inline("👨‍👩‍👧 Управление семьей", b"family_management")]
    ]
    await event.respond("⚙ Настройки:", buttons=buttons)

async def create_family_cmd(event):
    await event.respond("👨‍👩‍👧 Введите название новой семьи:")
    family_creation_pending[event.sender_id] = True

async def family_management_cmd(event):
    uid = event.sender_id
    fid = get_family_id(uid)
    
    print(f"DEBUG: family_management_cmd для пользователя {uid}, family_id: {fid}")
    
    if fid:
        code = invite_code_for(fid)
        
        # Получаем информацию о малыше
        baby_birth_date = get_baby_birth_date(fid)
        baby_age_months = get_activity_settings(fid)[2]  # Получаем возраст из настроек игр
        
        baby_info = ""
        if baby_birth_date:
            baby_info = f"👶 Дата рождения: {baby_birth_date}\n"
            # Автоматически вычисляем возраст по дате рождения
            calculated_age = calculate_baby_age_months(baby_birth_date)
            if calculated_age != baby_age_months:
                # Обновляем возраст если он изменился
                set_activity_settings(fid, age_months=calculated_age)
                baby_age_months = calculated_age
            
            baby_info += f"👶 Возраст: {baby_age_months} мес.\n"
        elif baby_age_months > 0:
            baby_info = f"👶 Возраст: {baby_age_months} мес.\n"
        else:
            baby_info = "👶 Возраст малыша не указан\n"
        
        buttons = [
            [Button.inline("👶 Установить дату рождения", b"set_baby_birth")],
            [Button.inline("👥 Члены семьи", b"family_members")],
            [Button.inline("🔙 Назад к настройкам", b"back_to_settings")]
        ]
        await event.respond(
            f"👨‍👩‍👧 **Управление семьей**\n\n"
            f"Название: {get_family_name(fid)}\n"
            f"Код для приглашения: `{code}`\n\n"
            f"{baby_info}\n"
            f"Выберите действие:",
            buttons=buttons
        )
    else:
        # Пользователь не в семье - показываем опции
        print(f"DEBUG: Пользователь {uid} не в семье, показываем опции присоединения")
        buttons = [
            [Button.inline("👨‍👩‍👧 Создать семью", b"create_family")],
            [Button.inline("🔗 Присоединиться к семье", b"join_family")],
            [Button.inline("🔙 Назад к настройкам", b"back_to_settings")]
        ]
        await event.respond(
            f"👨‍👩‍👧 **Управление семьей**\n\n"
            f"У вас пока нет семьи. Выберите действие:",
            buttons=buttons
        )

async def family_members_cmd(event):
    fid = get_family_id(event.sender_id)
    if fid:
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        # Получаем user_id, role и name для всех членов семьи
        cur.execute("SELECT user_id, role, name FROM family_members WHERE family_id = ?", (fid,))
        members = cur.fetchall()
        conn.close()
        
        if members:
            text = "👥 **Члены семьи:**\n\n"
            for i, (user_id, role, name) in enumerate(members, 1):
                text += f"{i}. {role} {name} (ID: {user_id})\n"
        else:
            text = "👥 В семье пока нет членов."
        
        buttons = [
            [Button.inline("🔙 Назад к управлению семьей", b"back_to_family_management")]
        ]
        await event.respond(text, buttons=buttons)
    else:
        await event.respond("❌ Ошибка: семья не найдена.")



@client.on(events.NewMessage(pattern='📜 История'))
async def history_menu(event):
    print(f"DEBUG: Обработка команды '📜 История' для пользователя {event.sender_id}")
    today = get_thai_date()
    buttons = [
        [Button.inline(f"📅 {today - timedelta(days=i)}", f"hist_{i}".encode())] for i in range(3)
    ]
    await event.respond("📖 Выберите день для просмотра истории:", buttons=buttons)

@client.on(events.NewMessage(pattern='🛁 Купание'))
async def bath_menu(event):
    """Меню купания"""
    buttons = [
        [Button.inline("🛁 Купать сейчас", b"bath_now")],
        [Button.inline("15 мин назад", b"bath_15")],
        [Button.inline("30 мин назад", b"bath_30")],
        [Button.inline("🕒 Указать вручную", b"bath_manual")],
        [Button.inline("⚙️ Настройки купания", b"bath_settings")]
    ]
    await event.respond("🛁 Когда было купание?", buttons=buttons)

@client.on(events.NewMessage(pattern='🎮 Игры'))
async def games_menu(event):
    """Меню игр и активностей"""
    buttons = [
        [Button.inline("🦵 Выкладывание на живот", b"activity_tummy")],
        [Button.inline("🎯 Играть сейчас", b"activity_play")],
        [Button.inline("💆 Массаж", b"activity_massage")],
        [Button.inline("⚙️ Настройки игр", b"activity_settings")]
    ]
    await event.respond("🎮 Выберите активность:", buttons=buttons)

@client.on(events.NewMessage(pattern='😴 Сон'))
async def sleep_menu(event):
    """Меню сна"""
    uid = event.sender_id
    fid = get_family_id(uid)
    
    if not fid:
        await event.respond("❌ Сначала создайте семью.")
        return
    
    active_sleep = get_active_sleep_session(fid)
    
    if active_sleep:
        # Малыш спит
        sleep_duration = get_thai_time() - active_sleep["start_time"]
        hours = int(sleep_duration.total_seconds() // 3600)
        minutes = int((sleep_duration.total_seconds() % 3600) // 60)
        
        message = (
            f"😴 **Малыш спит**\n\n"
            f"⏰ Начало сна: {active_sleep['start_time'].strftime('%H:%M')}\n"
            f"🕐 Длительность: {hours}ч {minutes}м\n"
            f"👤 Уложил: {active_sleep['author_role']} {active_sleep['author_name']}\n\n"
            f"💡 Нажмите кнопку ниже, когда малыш проснется"
        )
        
        buttons = [
            [Button.inline("🌅 Малыш проснулся", b"sleep_end")],
            [Button.inline("📊 Статус сна", b"sleep_status")]
        ]
    else:
        # Малыш не спит
        message = (
            f"😴 **Малыш не спит**\n\n"
            f"💡 Нажмите кнопку ниже, когда малыш заснет"
        )
        
        buttons = [
            [Button.inline("🌙 Малыш заснул", b"sleep_start")],
            [Button.inline("📊 История сна", b"sleep_history")]
        ]
    
    await event.respond(message, buttons=buttons)



@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()

    if data == "feed_now":
        add_feeding(event.sender_id)
        await event.edit("🍼 Кормление зафиксировано.")
    elif data == "feed_15":
        add_feeding(event.sender_id, 15)
        await event.edit("🍼 Кормление (15 мин назад) зафиксировано.")
    elif data == "feed_30":
        add_feeding(event.sender_id, 30)
        await event.edit("🍼 Кормление (30 мин назад) зафиксировано.")
    elif data == "feed_manual":
        manual_feeding_pending[event.sender_id] = True
        await event.respond("🕒 Введите время кормления в формате ЧЧ:ММ (например, 14:30):")

    elif data == "diaper_now":
        add_diaper_change(event.sender_id)
        await event.edit("🧷 Смена подгузника зафиксирована.")
    elif data == "diaper_15":
        add_diaper_change(event.sender_id, 15)
        await event.edit("🧷 Смена подгузника (15 мин назад) зафиксирована.")
    elif data == "diaper_30":
        add_diaper_change(event.sender_id, 30)
        await event.edit("🧷 Смена подгузника (30 мин назад) зафиксирована.")
    elif data == "diaper_manual":
        manual_feeding_pending[event.sender_id] = "diaper"
        await event.respond("🕒 Введите время смены подгузника в формате ЧЧ:ММ (например, 14:30):")

    elif data == "set_feed":
        buttons = [[Button.inline(f"{i} ч", f"feed_{i}".encode())] for i in range(1, 7)]
        await event.edit("🍽 Выберите интервал кормления:", buttons=buttons)
    elif data == "set_diaper":
        buttons = [[Button.inline(f"{i} ч", f"diaper_{i}".encode())] for i in range(1, 7)]
        await event.edit("🧷 Выберите интервал смены подгузника:", buttons=buttons)
    elif data.startswith("feed_yesterday_"):
        minutes_ago = int(data.split("_")[-1])
        uid = event.sender_id
        
        print(f"DEBUG: Обработка feed_yesterday_ для пользователя {uid}")
        print(f"DEBUG: manual_feeding_pending[{uid}] = {manual_feeding_pending.get(uid, 'не найдено')}")
        
        if uid in manual_feeding_pending and isinstance(manual_feeding_pending[uid], dict):
            time_str = manual_feeding_pending[uid]["time"]
            add_feeding(uid, minutes_ago=minutes_ago)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%d.%m')
            await event.edit(f"✅ Кормление за вчера ({yesterday}) в {time_str} зафиксировано.")
            del manual_feeding_pending[uid]
        else:
            await event.edit("❌ Ошибка: данные о времени не найдены.")
    
    elif data.startswith("diaper_yesterday_"):
        minutes_ago = int(data.split("_")[-1])
        uid = event.sender_id
        
        print(f"DEBUG: Обработка diaper_yesterday_ для пользователя {uid}")
        print(f"DEBUG: manual_feeding_pending[{uid}] = {manual_feeding_pending.get(uid, 'не найдено')}")
        
        if uid in manual_feeding_pending and isinstance(manual_feeding_pending[uid], dict):
            time_str = manual_feeding_pending[uid]["time"]
            add_diaper_change(uid, minutes_ago=minutes_ago)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%d.%m')
            await event.edit(f"✅ Смена подгузника за вчера ({yesterday}) в {time_str} зафиксирована.")
            del manual_feeding_pending[uid]
        else:
            await event.edit("❌ Ошибка: данные о времени не найдены.")
    
    # Обработчики для купания за вчера
    elif data.startswith("bath_yesterday_"):
        minutes_ago = int(data.split("_")[-1])
        uid = event.sender_id
        
        if uid in bath_pending and isinstance(bath_pending[uid], dict):
            time_str = bath_pending[uid]["time"]
            add_bath(uid, minutes_ago=minutes_ago)
            yesterday = (get_thai_date() - timedelta(days=1)).strftime('%d.%m')
            await event.edit(f"✅ Купание за вчера ({yesterday}) в {time_str} зафиксировано.")
            del bath_pending[uid]
        else:
            await event.edit("❌ Ошибка: данные о времени не найдены.")
    
    elif data.startswith("feed_"):
        hours = int(data.split("_")[1])
        fid = get_family_id(event.sender_id)
        set_user_interval(fid, feed_interval=hours)
        await event.edit(f"✅ Интервал кормления установлен на {hours} ч.")
    elif data.startswith("diaper_"):
        hours = int(data.split("_")[1])
        fid = get_family_id(event.sender_id)
        set_user_interval(fid, diaper_interval=hours)
        await event.edit(f"✅ Интервал смены подгузника установлен на {hours} ч.")
    elif data == "toggle_tips":
        fid = get_family_id(event.sender_id)
        toggle_tips(fid)
        await settings_menu(event)
    
    elif data == "toggle_bath":
        fid = get_family_id(event.sender_id)
        enabled, hour, minute, period = get_bath_settings(fid)
        new_enabled = 0 if enabled else 1
        set_bath_settings(fid, enabled=new_enabled)
        await event.edit(f"✅ Напоминания о купании {'включены' if new_enabled else 'отключены'}")
        await asyncio.sleep(2)
        await settings_menu(event)
    
    elif data == "my_role":
        uid = event.sender_id
        role, name = get_member_info(uid)
        
        message = (
            f"👤 **Ваша роль в семье:**\n\n"
            f"🎭 Роль: {role}\n"
            f"📝 Имя: {name}\n\n"
            f"💡 Нажмите кнопку ниже, чтобы изменить"
        )
        
        buttons = [
            [Button.inline("✏️ Изменить роль", b"edit_role")],
            [Button.inline("🔙 Назад к настройкам", b"back_to_settings")]
        ]
        
        await event.edit(message, buttons=buttons)
    
    elif data == "edit_role":
        await event.edit("👤 Выберите вашу роль:")
        buttons = [
            [Button.inline("👨‍👩‍👧 Родитель", b"role_parent")],
            [Button.inline("👨‍👩‍👧 Мама", b"role_mom")],
            [Button.inline("👨‍👩‍👧 Папа", b"role_dad")],
            [Button.inline("👨‍👩‍👧 Бабушка", b"role_grandma")],
            [Button.inline("👨‍👩‍👧 Дедушка", b"role_grandpa")],
            [Button.inline("👨‍👩‍👧 Няня", b"role_nanny")],
            [Button.inline("🔙 Назад к настройкам", b"back_to_settings")]
        ]
        await event.edit("👤 Выберите вашу роль:", buttons=buttons )
    
    elif data.startswith("role_"):
        role_map = {
            "role_parent": "Родитель",
            "role_mom": "Мама",
            "role_dad": "Папа",
            "role_grandma": "Бабушка",
            "role_grandpa": "Дедушка",
            "role_nanny": "Няня"
        }
        role = role_map.get(data, "Родитель")
        uid = event.sender_id
        
        # Запрашиваем имя
        await event.edit(f"👤 Роль установлена: {role}\n\n📝 Теперь введите ваше имя:")
        edit_role_pending[uid] = {"role": role, "step": "waiting_name"}
    
    elif data == "back_to_main":
        await start(event)
    
    elif data == "set_tips_time":
        await event.edit("🕐 Выберите время для рассылки советов:")
        # Показываем кнопки для выбора часа
        buttons = []
        for hour in range(0, 24, 2):  # Каждые 2 часа
            buttons.append([Button.inline(f"{hour:02d}:00", f"tips_hour_{hour}".encode())])
        buttons.append([Button.inline("🔙 Назад", b"back_to_settings")])
        await event.edit("🕐 Выберите час для рассылки советов:", buttons=buttons)

    elif data.startswith("tips_hour_"):
        hour = int(data.split("_")[-1])
        # Показываем кнопки для выбора минуты
        buttons = []
        for minute in range(0, 60, 15):  # Каждые 15 минут
            buttons.append([Button.inline(f"{hour:02d}:{minute:02d}", f"tips_time_{hour}_{minute}".encode())])
        buttons.append([Button.inline("🔙 Назад", b"set_tips_time")])
        await event.edit(f"🕐 Выберите минуту для времени {hour:02d}:XX:", buttons=buttons)
    
    elif data.startswith("tips_time_"):
        parts = data.split("_")
        hour = int(parts[-2])
        minute = int(parts[-1])
        fid = get_family_id(event.sender_id)
        set_tips_time(fid, hour, minute)
        await event.edit(f"✅ Время рассылки советов установлено на {hour:02d}:{minute:02d}")
        # Возвращаемся к настройкам через 2 секунды
        await asyncio.sleep(2)
        await settings_menu(event)
    
    elif data.startswith("hist_"):
        print(f"DEBUG: Обработка истории для пользователя {event.sender_id}, data: {data}")
        try:
            index = int(data.split("_")[1])
            target_date = get_thai_date() - timedelta(days=index)
            print(f"DEBUG: Целевая дата: {target_date}")
            
            feedings = get_feedings_by_day(event.sender_id, target_date)
            diapers = get_diapers_by_day(event.sender_id, target_date)
            
            print(f"DEBUG: Найдено кормлений: {len(feedings) if feedings else 0}")
            print(f"DEBUG: Найдено смен подгузников: {len(diapers) if diapers else 0}")
            
            if feedings:
                print(f"DEBUG: Первое кормление: {feedings[0]}")
                print(f"DEBUG: Количество колонок в кормлении: {len(feedings[0])}")
                print(f"DEBUG: Структура кормления: id={feedings[0][0]}, time={feedings[0][1]}, role={feedings[0][2] if len(feedings[0]) > 2 else 'N/A'}, name={feedings[0][3] if len(feedings[0]) > 3 else 'N/A'}")
            if diapers:
                print(f"DEBUG: Первая смена: {diapers[0]}")
                print(f"DEBUG: Количество колонок в смене: {len(diapers[0])}")
                print(f"DEBUG: Структура смены: id={diapers[0][0]}, time={diapers[0][1]}, role={diapers[0][2] if len(diapers[0]) > 2 else 'N/A'}, name={diapers[0][3] if len(diapers[0]) > 3 else 'N/A'}")
        except Exception as e:
            print(f"DEBUG: Ошибка при обработке истории: {e}")
            await event.answer(f"❌ Ошибка: {str(e)}", alert=True)
            return

        text = f"📅 История за {target_date}:\n\n"

        if feedings:
            text += "🍼 Кормления:\n"
            for f in feedings:
                time_str = datetime.fromisoformat(f[1]).strftime("%H:%M")
                # Проверяем, есть ли информация об авторе (индексы 2 и 3)
                if len(f) >= 4 and f[2] and f[3]:  # author_role и author_name
                    author_info = f"{f[2]} {f[3]}"
                else:
                    author_info = "Неизвестно"
                text += f"  • {time_str} - {author_info} [ID {f[0]}]\n"
        else:
            text += "🍼 Кормлений нет\n"

        if diapers:
            text += "\n🧷 Подгузники:\n"
            for d in diapers:
                time_str = datetime.fromisoformat(d[1]).strftime("%H:%M")
                # Проверяем, есть ли информация об авторе (индексы 2 и 3)
                if len(d) >= 4 and d[2] and d[3]:  # author_role и author_name
                    author_info = f"{d[2]} {d[3]}"
                else:
                    author_info = "Неизвестно"
                text += f"  • {time_str} - {author_info} [ID {d[0]}]\n"
        else:
            text += "\n🧷 Смен нет\n"

        # Кнопки удаления и редактирования
        buttons = []
        for f in feedings:
            buttons.append([Button.inline(f"🍼 {f[0]} ✏️", f"edit_feed_{f[0]}".encode()),
                            Button.inline("🗑", f"del_feed_{f[0]}".encode())])
        for d in diapers:
            buttons.append([Button.inline(f"🧷 {d[0]} ✏️", f"edit_diaper_{d[0]}".encode()),
                            Button.inline("🗑", f"del_diaper_{d[0]}".encode())])

        # Проверяем, есть ли кнопки
        if buttons:
            await event.edit(text, buttons=buttons)
        else:
            # Если кнопок нет, просто обновляем текст
            await event.edit(text)
        return

    elif data.startswith("del_feed_"):
        entry_id = int(data.split("_")[-1])
        delete_entry("feedings", entry_id)
        await event.answer("🗑 Удалено", alert=True)

    elif data.startswith("del_diaper_"):
        entry_id = int(data.split("_")[-1])
        delete_entry("diapers", entry_id)
        await event.answer("🗑 Удалено", alert=True)

    elif data.startswith("edit_feed_") or data.startswith("edit_diaper_"):
        entry_id = int(data.split("_")[-1])
        table = "feedings" if "feed" in data else "diapers"
        edit_pending[event.sender_id] = (table, entry_id)
        await event.respond(f"✏️ Введите новое время в формате ЧЧ:ММ для записи ID {entry_id}")
    
    elif data == "settings":
        await settings_menu(event)
    
    elif data == "create_family":
        await event.respond("👨‍👩‍👧 Введите название новой семьи:")
        family_creation_pending[event.sender_id] = True
    
    elif data == "join_family":
        await event.respond("🔗 Введите код приглашения семьи:")
        join_pending[event.sender_id] = True
    
    elif data == "family_management":
        await family_management_cmd(event)
    
    elif data == "set_baby_birth":
        baby_birth_pending[event.sender_id] = True
        await event.edit("👶 Введите дату рождения малыша в формате ГГГГ-ММ-ДД (например: 2024-01-15):")
    
    elif data == "family_members":
        await family_members_cmd(event)
    
    elif data == "back_to_family_management":
        await family_management_cmd(event)
    
    elif data == "back_to_settings":
        await settings_menu(event)
    
    elif data == "feed_cancel":
        uid = event.sender_id
        if uid in manual_feeding_pending:
            del manual_feeding_pending[uid]
        await event.edit("❌ Запись кормления отменена.")
    
    elif data == "diaper_cancel":
        uid = event.sender_id
        if uid in manual_feeding_pending:
            del manual_feeding_pending[uid]
        await event.edit("❌ Запись смены подгузника отменена.")
    
    # Обработчики для купания
    elif data == "bath_now":
        add_bath(event.sender_id)
        await event.edit("🛁 Купание зафиксировано.")
    elif data == "bath_15":
        add_bath(event.sender_id, 15)
        await event.edit("🛁 Купание (15 мин назад) зафиксировано.")
    elif data == "bath_30":
        add_bath(event.sender_id, 30)
        await event.edit("🛁 Купание (30 мин назад) зафиксировано.")
    elif data == "bath_manual":
        bath_pending[event.sender_id] = True
        await event.respond("🕒 Введите время купания в формате ЧЧ:ММ (например, 14:30):")
    elif data == "bath_settings":
        await show_bath_settings(event)
    
    # Обработчики для игр
    elif data == "activity_tummy":
        add_activity(event.sender_id, "tummy_time")
        await event.edit("🦵 Выкладывание на живот зафиксировано.")
    elif data == "activity_play":
        add_activity(event.sender_id, "play")
        await event.edit("🎯 Игра зафиксирована.")
    elif data == "activity_massage":
        add_activity(event.sender_id, "massage")
        await event.edit("💆 Массаж зафиксирован.")
    elif data == "activity_settings":
        await show_activity_settings(event)
    
    # Обработчики для сна
    elif data == "sleep_start":
        start_sleep_session(event.sender_id)
        await event.edit("🌙 Малыш заснул. Отслеживаем сон...")
    elif data == "sleep_end":
        duration = end_sleep_session(event.sender_id)
        if duration:
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            await event.edit(f"🌅 Малыш проснулся! Спал {hours}ч {minutes}м.")
        else:
            await event.edit("🌅 Малыш проснулся!")
    elif data == "sleep_status":
        await show_sleep_status(event)
    elif data == "sleep_history":
        await show_sleep_history(event)
    

    
    # Обработчики для настроек купания
    elif data.startswith("bath_period_"):
        period = int(data.split("_")[-1])
        fid = get_family_id(event.sender_id)
        set_bath_settings(fid, period=period)
        await event.edit(f"✅ Период напоминаний о купании установлен на {period} день(ей)")
        await asyncio.sleep(2)
        await settings_menu(event)
    
    elif data.startswith("bath_time_"):
        time_parts = data.split("_")
        hour = int(time_parts[-2])
        minute = int(time_parts[-1])
        fid = get_family_id(event.sender_id)
        set_bath_settings(fid, hour=hour, minute=minute)
        await event.edit(f"✅ Время напоминаний о купании установлено на {hour:02d}:{minute:02d}")
        await asyncio.sleep(2)
        await settings_menu(event)
    
    # Обработчики для настроек игр
    elif data.startswith("activity_interval_"):
        interval = int(data.split("_")[-1])
        fid = get_family_id(event.sender_id)
        set_activity_settings(fid, interval=interval)
        await event.edit(f"✅ Интервал напоминаний об играх установлен на {interval} ч.")
        await asyncio.sleep(2)
        await settings_menu(event)
    

    
    # Обработчики для кнопок "Назад"
    elif data == "back_to_games":
        await games_menu(event)
    elif data == "back_to_sleep":
        await sleep_menu(event)
    elif data == "bath_cancel":
        uid = event.sender_id
        if uid in bath_pending:
            del bath_pending[uid]
        await event.edit("❌ Запись купания отменена.")
    
    # Обработчики для настроек купания
    elif data == "bath_change_time":
        await event.edit("🕐 Выберите время для напоминаний о купании:")
        buttons = []
        for hour in range(18, 22):  # Вечерние часы для купания
            for minute in [0, 15, 30, 45]:
                buttons.append([Button.inline(f"{hour:02d}:{minute:02d}", f"bath_time_{hour}_{minute}".encode())])
        buttons.append([Button.inline("🔙 Назад", b"bath_settings")])
        await event.edit("🕐 Выберите время для напоминаний о купании:", buttons=buttons)
    
    elif data == "bath_change_period":
        await event.edit("📅 Выберите период напоминаний о купании:")
        buttons = [
            [Button.inline("1 день", b"bath_period_1")],
            [Button.inline("2 дня", b"bath_period_2")],
            [Button.inline("3 дня", b"bath_period_3")],
            [Button.inline("🔙 Назад", b"bath_settings")]
        ]
        await event.edit("📅 Выберите период напоминаний о купании:", buttons=buttons)
    
    elif data == "bath_toggle":
        fid = get_family_id(event.sender_id)
        enabled, hour, minute, period = get_bath_settings(fid)
        new_enabled = 0 if enabled else 1
        set_bath_settings(fid, enabled=new_enabled)
        await event.edit(f"✅ Напоминания о купании {'включены' if new_enabled else 'отключены'}")
        await asyncio.sleep(2)
        await show_bath_settings(event)
    
    # Обработчики для настроек игр
    elif data == "activity_change_interval":
        await event.edit("⏰ Выберите интервал напоминаний об играх:")
        buttons = [
            [Button.inline("1 час", b"activity_interval_1")],
            [Button.inline("2 часа", b"activity_interval_2")],
            [Button.inline("3 часа", b"activity_interval_3")],
            [Button.inline("4 часа", b"activity_interval_4")],
            [Button.inline("🔙 Назад", b"activity_settings")]
        ]
        await event.edit("⏰ Выберите интервал напоминаний об играх:", buttons=buttons)
    

    
    elif data == "activity_toggle":
        fid = get_family_id(event.sender_id)
        enabled, interval, age_months = get_activity_settings(fid)
        new_enabled = 0 if enabled else 1
        set_activity_settings(fid, enabled=new_enabled)
        await event.edit(f"✅ Напоминания об играх {'включены' if new_enabled else 'отключены'}")
        await asyncio.sleep(2)
        await settings_menu(event)

@client.on(events.NewMessage)
async def handle_text(event):
    uid = event.sender_id

    if uid in manual_feeding_pending:
        user_input = event.raw_text.strip()
        action_type = manual_feeding_pending[uid]
        
        # Проверяем, что это за действие
        if action_type == "diaper":
            print(f"DEBUG: Пользователь {uid} ввел время для смены подгузника: '{user_input}'")
            action_name = "смена подгузника"
            add_func = add_diaper_change
            callback_prefix = "diaper_yesterday_"
            cancel_callback = "diaper_cancel"
        else:
            print(f"DEBUG: Пользователь {uid} ввел время для кормления: '{user_input}'")
            action_name = "кормление"
            add_func = add_feeding
            callback_prefix = "feed_yesterday_"
            cancel_callback = "feed_cancel"
        
        try:
            # Парсим введенное время
            t = datetime.strptime(user_input, "%H:%M")
            print(f"DEBUG: Парсинг времени успешен: {t}")
            
            # Создаем datetime объект для сегодняшнего дня с введенным временем (в тайском времени)
            today = get_thai_date()
            # Создаем datetime объект с тайским часовым поясом
            thai_tz = pytz.timezone('Asia/Bangkok')
            dt = thai_tz.localize(datetime.combine(today, t.time()))
            now = get_thai_time()
            
            print(f"DEBUG: Сегодня (Таиланд): {today}")
            print(f"DEBUG: Введенное время: {dt}")
            print(f"DEBUG: Текущее время (Таиланд): {now}")
            print(f"DEBUG: UTC время: {datetime.now(pytz.UTC)}")
            
            # Вычисляем разницу в минутах
            diff = int((now - dt).total_seconds() // 60)
            print(f"DEBUG: Разница в минутах: {diff}")
            
            # Проверяем, что время не в будущем и не слишком далеко в прошлом
            if diff < 0:
                print(f"DEBUG: Время в будущем, разница: {diff}")
                # Предлагаем сделать запись за прошлый день
                yesterday = today - timedelta(days=1)
                yesterday_dt = thai_tz.localize(datetime.combine(yesterday, t.time()))
                yesterday_diff = int((now - yesterday_dt).total_seconds() // 60)
                
                if yesterday_diff >= 0 and yesterday_diff <= 1440:
                    # Создаем кнопки для выбора дня
                    buttons = [
                        [Button.inline("✅ Да, за вчера", f"{callback_prefix}{yesterday_diff}".encode())],
                        [Button.inline("❌ Нет, отменить", cancel_callback.encode())]
                    ]
                    await event.respond(
                        f"🕒 Время {user_input} больше текущего времени.\n"
                        f"Хотите сделать запись {action_name} за вчера ({yesterday.strftime('%d.%m')})?",
                        buttons=buttons)
                    # Сохраняем введенное время для возможного использования
                    manual_feeding_pending[uid] = {"type": action_type, "time": user_input, "minutes_ago": yesterday_diff}
                    print(f"DEBUG: Сохранили данные в manual_feeding_pending[{uid}] = {manual_feeding_pending[uid]}")
                    return
                else:
                    await event.respond("❌ Нельзя указать время в будущем. Введите прошедшее время.")
                    return
            elif diff > 1440:  # больше 24 часов
                print(f"DEBUG: Время слишком далеко в прошлом, разница: {diff}")
                # Проверяем, может ли это быть время за вчера
                yesterday = today - timedelta(days=1)
                yesterday_dt = thai_tz.localize(datetime.combine(yesterday, t.time()))
                yesterday_diff = int((now - yesterday_dt).total_seconds() // 60)
                
                if yesterday_diff >= 0 and yesterday_diff <= 1440:
                    print(f"DEBUG: Время подходит для вчерашнего дня, разница: {yesterday_diff}")
                    # Автоматически предлагаем записать за вчера
                    buttons = [
                        [Button.inline("✅ Да, за вчера", f"{callback_prefix}{yesterday_diff}".encode())],
                        [Button.inline("❌ Нет, отменить", cancel_callback.encode())]
                    ]
                    await event.respond(
                        f"🕒 Время {user_input} слишком далеко в прошлом для сегодняшнего дня.\n"
                        f"Хотите сделать запись {action_name} за вчера ({yesterday.strftime('%d.%m')})?",
                        buttons=buttons)
                    manual_feeding_pending[uid] = {"type": action_type, "time": user_input, "minutes_ago": yesterday_diff}
                    print(f"DEBUG: Сохранили данные в manual_feeding_pending[{uid}] = {manual_feeding_pending[uid]}")
                    return
                else:
                    await event.respond("❌ Время слишком далеко в прошлом. Максимум 24 часа назад.")
                    return
            
            # Если время в прошлом, но не слишком далеко
            if diff >= 0:
                print(f"DEBUG: Добавляем {action_name}, minutes_ago: {diff}")
                add_func(uid, minutes_ago=diff)
                await event.respond(f"✅ {action_name.capitalize()} в {user_input} зафиксировано.")
            else:
                await event.respond("❌ Ошибка: неожиданное значение времени.")
            
            # Удаляем данные только после успешного добавления
            if uid in manual_feeding_pending:
                del manual_feeding_pending[uid]
        except ValueError as e:
            print(f"DEBUG: Ошибка парсинга времени: {e}")
            await event.respond("❌ Неверный формат. Введите время в формате ЧЧ:ММ (например: 14:30)")
            # Удаляем данные при ошибке парсинга
            if uid in manual_feeding_pending:
                del manual_feeding_pending[uid]
        except Exception as e:
            print(f"DEBUG: Неожиданная ошибка: {e}")
            await event.respond(f"❌ Ошибка: {str(e)}")
            # Удаляем данные при неожиданной ошибке
            if uid in manual_feeding_pending:
                del manual_feeding_pending[uid]
        return

    if uid in family_creation_pending:
        name = event.raw_text.strip()
        fid = create_family(name, uid)
        del family_creation_pending[uid]
        code = invite_code_for(fid)
        await event.respond(f"✅ Семья создана. Код приглашения: `{code}`")
        return
    
    if uid in join_pending:
        code = event.raw_text.strip()
        family_id, family_name = join_family_by_code(code, uid)
        del join_pending[uid]
        
        if family_id:
            await event.respond(f"✅ Вы успешно присоединились к семье '{family_name}'!")
        else:
            await event.respond(f"❌ Не удалось присоединиться к семье: {family_name}")
        return
    
    if uid in edit_role_pending:
        user_input = event.raw_text.strip()
        role_data = edit_role_pending[uid]
        
        if role_data["step"] == "waiting_name":
            # Устанавливаем роль и имя
            set_member_role(uid, role_data["role"], user_input)
            del edit_role_pending[uid]
            
            await event.respond(
                f"✅ Роль обновлена!\n\n"
                f"🎭 Роль: {role_data['role']}\n"
                f"📝 Имя: {user_input}\n\n"
                f"💡 Теперь в истории будет отображаться, кто именно ухаживает за малышом!"
            )
        return
    
    # Обработка ввода даты рождения малыша
    if uid in baby_birth_pending:
        user_input = event.raw_text.strip()
        
        try:
            # Парсим введенную дату
            birth_date = datetime.strptime(user_input, "%Y-%m-%d")
            current_date = get_thai_date()
            
            # Проверяем, что дата не в будущем
            if birth_date.date() > current_date:
                await event.respond("❌ Дата рождения не может быть в будущем. Введите корректную дату.")
                return
            
            # Проверяем, что дата не слишком старая (больше 5 лет назад)
            if (current_date - birth_date.date()).days > 1825:  # 5 лет
                await event.respond("❌ Дата рождения не может быть больше 5 лет назад. Введите корректную дату.")
                return
            
            # Устанавливаем дату рождения
            fid = get_family_id(uid)
            set_baby_birth_date(fid, user_input)
            
            # Автоматически вычисляем и устанавливаем возраст
            age_months = calculate_baby_age_months(user_input)
            set_activity_settings(fid, age_months=age_months)
            
            await event.respond(
                f"✅ Дата рождения малыша установлена!\n\n"
                f"👶 Дата: {birth_date.strftime('%d.%m.%Y')}\n"
                f"👶 Возраст: {age_months} мес.\n\n"
                f"💡 Теперь бот будет автоматически обновлять возраст и давать персонализированные рекомендации!"
            )
            
            # Удаляем состояние
            del baby_birth_pending[uid]
        except ValueError:
            await event.respond("❌ Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД (например: 2024-01-15)")
        except Exception as e:
            await event.respond(f"❌ Ошибка: {str(e)}")
            del baby_birth_pending[uid]
        return
    
    # Обработка ввода для купания
    if uid in bath_pending:
        user_input = event.raw_text.strip()
        
        try:
            # Парсим введенное время
            t = datetime.strptime(user_input, "%H:%M")
            
            # Создаем datetime объект для сегодняшнего дня с введенным временем
            today = get_thai_date()
            thai_tz = pytz.timezone('Asia/Bangkok')
            dt = thai_tz.localize(datetime.combine(today, t.time()))
            now = get_thai_time()
            
            # Вычисляем разницу в минутах
            diff = int((now - dt).total_seconds() // 60)
            
            # Проверяем, что время не в будущем и не слишком далеко в прошлом
            if diff < 0:
                # Предлагаем сделать запись за прошлый день
                yesterday = today - timedelta(days=1)
                yesterday_dt = thai_tz.localize(datetime.combine(yesterday, t.time()))
                yesterday_diff = int((now - yesterday_dt).total_seconds() // 60)
                
                if yesterday_diff >= 0 and yesterday_diff <= 1440:
                    buttons = [
                        [Button.inline("✅ Да, за вчера", f"bath_yesterday_{yesterday_diff}".encode())],
                        [Button.inline("❌ Нет, отменить", b"bath_cancel")]
                    ]
                    await event.respond(
                        f"🕒 Время {user_input} больше текущего времени.\n"
                        f"Хотите сделать запись купания за вчера ({yesterday.strftime('%d.%m')})?",
                        buttons=buttons)
                    bath_pending[uid] = {"time": user_input, "minutes_ago": yesterday_diff}
                    return
                else:
                    await event.respond("❌ Нельзя указать время в будущем. Введите прошедшее время.")
                    del bath_pending[uid]
                    return
            elif diff > 1440:  # больше 24 часов
                # Проверяем, может ли это быть время за вчера
                yesterday = today - timedelta(days=1)
                yesterday_dt = thai_tz.localize(datetime.combine(yesterday, t.time()))
                yesterday_diff = int((now - yesterday_dt).total_seconds() // 60)
                
                if yesterday_diff >= 0 and yesterday_diff <= 1440:
                    buttons = [
                        [Button.inline("✅ Да, за вчера", f"bath_yesterday_{yesterday_diff}".encode())],
                        [Button.inline("❌ Нет, отменить", b"bath_cancel")]
                    ]
                    await event.respond(
                        f"🕒 Время {user_input} слишком далеко в прошлом для сегодняшнего дня.\n"
                        f"Хотите сделать запись купания за вчера ({yesterday.strftime('%d.%m')})?",
                        buttons=buttons)
                    bath_pending[uid] = {"time": user_input, "minutes_ago": yesterday_diff}
                    return
                else:
                    await event.respond("❌ Время слишком далеко в прошлом. Максимум 24 часа назад.")
                    del bath_pending[uid]
                    return
            
            # Если время в прошлом, но не слишком далеко
            if diff >= 0:
                add_bath(uid, minutes_ago=diff)
                await event.respond(f"✅ Купание в {user_input} зафиксировано.")
            else:
                await event.respond("❌ Ошибка: неожиданное значение времени.")
            
            # Удаляем данные только после успешного добавления
            if uid in bath_pending:
                del bath_pending[uid]
        except ValueError:
            await event.respond("❌ Неверный формат. Введите время в формате ЧЧ:ММ (например: 14:30)")
            del bath_pending[uid]
        except Exception as e:
            await event.respond(f"❌ Ошибка: {str(e)}")
            del bath_pending[uid]
        return
    
    # Обработка ввода для активностей
    if uid in activity_pending:
        user_input = event.raw_text.strip()
        activity_data = activity_pending[uid]
        
        try:
            # Парсим введенное время
            t = datetime.strptime(user_input, "%H:%M")
            
            # Создаем datetime объект для сегодняшнего дня с введенным временем
            today = get_thai_date()
            thai_tz = pytz.timezone('Asia/Bangkok')
            dt = thai_tz.localize(datetime.combine(today, t.time()))
            now = get_thai_time()
            
            # Вычисляем разницу в минутах
            diff = int((now - dt).total_seconds() // 60)
            
            # Проверяем, что время не в будущем и не слишком далеко в прошлом
            if diff < 0 or diff > 1440:
                await event.respond("❌ Время должно быть в прошлом, но не более 24 часов назад.")
                del activity_pending[uid]
                return
            
            # Добавляем активность
            add_activity(uid, activity_data["type"], minutes_ago=diff)
            await event.respond(f"✅ {activity_data['name']} в {user_input} зафиксировано.")
            
            # Удаляем данные
            del activity_pending[uid]
        except ValueError:
            await event.respond("❌ Неверный формат. Введите время в формате ЧЧ:ММ (например: 14:30)")
            del activity_pending[uid]
        except Exception as e:
            await event.respond(f"❌ Ошибка: {str(e)}")
            del activity_pending[uid]
        return



def get_last_feeding_time_for_family(family_id):
    """Получить время последнего кормления для семьи"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Получаем всех членов семьи
    cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
    members = cur.fetchall()
    
    if not members:
        conn.close()
        return None
    
    # Получаем последнее кормление среди всех членов семьи
    member_ids = [str(member[0]) for member in members]
    placeholders = ','.join(['?' for _ in member_ids])
    
    cur.execute(f"""
        SELECT timestamp FROM feedings 
        WHERE family_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (family_id,))
    
    result = cur.fetchone()
    conn.close()
    
    if result:
        return datetime.fromisoformat(result[0])
    return None

def should_send_feeding_reminder(family_id):
    """Проверить, нужно ли отправить напоминание о кормлении"""
    conn = sqlite3.connect("babybot.db")
    cur = conn.cursor()
    
    # Получаем интервал кормления для семьи
    cur.execute("SELECT feed_interval FROM settings WHERE family_id = ?", (family_id,))
    result = cur.fetchone()
    
    if not result:
        conn.close()
        return False
    
    feed_interval = result[0]  # в часах
    last_feeding = get_last_feeding_time_for_family(family_id)
    
    if not last_feeding:
        # Если кормлений еще не было, напоминаем через 2 часа после создания семьи
        return True
    
    # Вычисляем, сколько времени прошло с последнего кормления
    time_since_last = datetime.now() - last_feeding
    hours_since_last = time_since_last.total_seconds() / 3600
    
    # Если прошло больше интервала + 30 минут (буфер), отправляем напоминание
    return hours_since_last >= (feed_interval + 0.5)
    
    conn.close()

@scheduler.scheduled_job('interval', minutes=30)
async def check_feeding_reminders():
    """Проверять каждые 30 минут, нужно ли отправить напоминания о кормлении"""
    try:
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        
        # Получаем все семьи с включенными уведомлениями
        cur.execute("SELECT family_id FROM settings WHERE tips_enabled = 1")
        families = cur.fetchall()
        
        for (family_id,) in families:
            if should_send_feeding_reminder(family_id):
                # Получаем всех членов семьи
                cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                members = cur.fetchall()
                
                # Получаем интервал кормления
                cur.execute("SELECT feed_interval FROM settings WHERE family_id = ?", (family_id,))
                interval_result = cur.fetchone()
                feed_interval = interval_result[0] if interval_result else 3
                
                # Получаем время последнего кормления
                last_feeding = get_last_feeding_time_for_family(family_id)
                
                if last_feeding:
                    time_since_last = datetime.now() - last_feeding
                    hours_since_last = time_since_last.total_seconds() / 3600
                    message = (
                        f"🍼 **Напоминание о кормлении!**\n\n"
                        f"⏰ Прошло: {hours_since_last:.1f} ч. с последнего кормления\n"
                        f"📅 Последнее кормление: {last_feeding.strftime('%H:%M')}\n"
                        f"🔄 Рекомендуемый интервал: {feed_interval} ч.\n\n"
                        f"💡 Не забудьте покормить малыша!"
                    )
                else:
                    message = (
                        f"🍼 **Первое кормление!**\n\n"
                        f"👶 Пора начать отслеживать кормления\n"
                        f"🔄 Рекомендуемый интервал: {feed_interval} ч.\n\n"
                        f"💡 Запишите первое кормление!"
                    )
                
                # Отправляем уведомление всем членам семьи
                for (user_id,) in members:
                    try:
                        await client.send_message(user_id, message)
                        print(f"✅ Отправлено напоминание о кормлении пользователю {user_id}")
                    except Exception as e:
                        print(f"❌ Ошибка отправки напоминания пользователю {user_id}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка в check_feeding_reminders: {e}")

@scheduler.scheduled_job('interval', minutes=1)
async def send_scheduled_tips():
    """Отправлять советы по расписанию для каждой семьи"""
    try:
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        
        # Получаем все семьи с включенными советами
        cur.execute("SELECT family_id, tips_time_hour, tips_time_minute FROM settings WHERE tips_enabled = 1")
        families = cur.fetchall()
        
        for (family_id, tips_hour, tips_minute) in families:
            # Проверяем, пора ли отправлять советы для этой семьи
            if current_hour == tips_hour and current_minute == tips_minute:
                tip = get_random_tip()
                
                # Получаем всех членов семьи
                cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                members = cur.fetchall()
                
                # Отправляем совет всем членам семьи
                for (user_id,) in members:
                    try:
                        await client.send_message(user_id, tip)
                        print(f"✅ Отправлен совет пользователю {user_id} в {current_hour:02d}:{current_minute:02d}")
                    except Exception as e:
                        print(f"❌ Ошибка отправки совета пользователю {user_id}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка в send_scheduled_tips: {e}")

@scheduler.scheduled_job('interval', minutes=15)
async def send_scheduled_feeding_reminders():
    """Отправлять регулярные напоминания о кормлении по расписанию"""
    try:
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        
        # Получаем все семьи с включенными уведомлениями
        cur.execute("SELECT family_id FROM settings WHERE tips_enabled = 1")
        families = cur.fetchall()
        
        for (family_id,) in families:
            # Получаем интервал кормления
            cur.execute("SELECT feed_interval FROM settings WHERE family_id = ?", (family_id,))
            interval_result = cur.fetchone()
            feed_interval = interval_result[0] if interval_result else 3
            
            # Получаем время последнего кормления
            last_feeding = get_last_feeding_time_for_family(family_id)
            
            if last_feeding:
                # Используем тайское время для точности
                current_time = get_thai_time()
                time_since_last = current_time - last_feeding
                hours_since_last = time_since_last.total_seconds() / 3600
                minutes_since_last = time_since_last.total_seconds() / 60
                
                # Определяем статус и отправляем уведомления
                if hours_since_last >= feed_interval:
                    # Пора кормить!
                    if hours_since_last < (feed_interval + 0.5):  # В пределах 30 минут после интервала
                        # Получаем всех членов семьи
                        cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                        members = cur.fetchall()
                        
                        # Создаем сообщение с кнопками для быстрых действий
                        message = (
                            f"🍼 **Время кормления!**\n\n"
                            f"⏰ Прошло: {hours_since_last:.1f} ч. ({minutes_since_last:.0f} мин.) с последнего кормления\n"
                            f"📅 Последнее кормление: {last_feeding.strftime('%H:%M')}\n"
                            f"🔄 Интервал: {feed_interval} ч.\n\n"
                            f"💡 Пора покормить малыша!\n\n"
                            f"🔄 Нажмите кнопку ниже, чтобы зафиксировать кормление:"
                        )
                        
                        # Создаем кнопки для быстрых действий
                        buttons = [
                            [Button.inline("🍼 Кормить сейчас", b"feed_now")],
                            [Button.inline("15 мин назад", b"feed_15")],
                            [Button.inline("30 мин назад", b"feed_30")]
                        ]
                        
                        # Отправляем уведомление всем членам семьи
                        for (user_id,) in members:
                            try:
                                await client.send_message(user_id, message, buttons=buttons)
                                print(f"✅ Отправлено уведомление о кормлении пользователю {user_id}")
                            except Exception as e:
                                print(f"❌ Ошибка отправки уведомления о кормлении пользователю {user_id}: {e}")
                    
                    elif hours_since_last >= (feed_interval + 1):  # Через час после интервала - срочное уведомление
                        # Получаем всех членов семьи
                        cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                        members = cur.fetchall()
                        
                        # Срочное уведомление
                        urgent_message = (
                            f"🚨 **СРОЧНО! Долго не кормили!**\n\n"
                            f"⏰ Прошло: {hours_since_last:.1f} ч. ({minutes_since_last:.0f} мин.) с последнего кормления\n"
                            f"📅 Последнее кормление: {last_feeding.strftime('%H:%M')}\n"
                            f"🔄 Интервал: {feed_interval} ч.\n\n"
                            f"⚠️ Малыш может быть голоден! Немедленно покормите!"
                        )
                        
                        # Отправляем срочное уведомление всем членам семьи
                        for (user_id,) in members:
                            try:
                                await client.send_message(user_id, urgent_message)
                                print(f"🚨 Отправлено срочное уведомление о кормлении пользователю {user_id}")
                            except Exception as e:
                                print(f"❌ Ошибка отправки срочного уведомления пользователю {user_id}: {e}")
                
                elif hours_since_last >= (feed_interval - 0.25):  # За 15 минут до интервала - предварительное уведомление
                    # Получаем всех членов семьи
                    cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                    members = cur.fetchall()
                    
                    # Предварительное уведомление
                    pre_message = (
                        f"⏰ **Скоро время кормления**\n\n"
                        f"⏰ Прошло: {hours_since_last:.1f} ч. ({minutes_since_last:.0f} мин.) с последнего кормления\n"
                        f"📅 Последнее кормление: {last_feeding.strftime('%H:%M')}\n"
                        f"🔄 Интервал: {feed_interval} ч.\n\n"
                        f"💡 Через {feed_interval - hours_since_last:.1f} ч. пора будет кормить малыша"
                    )
                    
                    # Отправляем предварительное уведомление всем членам семьи
                    for (user_id,) in members:
                        try:
                            await client.send_message(user_id, pre_message)
                            print(f"⏰ Отправлено предварительное уведомление о кормлении пользователю {user_id}")
                        except Exception as e:
                            print(f"❌ Ошибка отправки предварительного уведомления пользователю {user_id}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка в send_scheduled_feeding_reminders: {e}")

@scheduler.scheduled_job('interval', minutes=15)
async def send_scheduled_diaper_reminders():
    """Отправлять регулярные напоминания о смене подгузника по расписанию"""
    try:
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        
        # Получаем все семьи с включенными уведомлениями
        cur.execute("SELECT family_id FROM settings WHERE tips_enabled = 1")
        families = cur.fetchall()
        
        for (family_id,) in families:
            # Получаем интервал смены подгузника
            cur.execute("SELECT diaper_interval FROM settings WHERE family_id = ?", (family_id,))
            interval_result = cur.fetchone()
            diaper_interval = interval_result[0] if interval_result else 2
            
            # Получаем время последней смены подгузника
            last_diaper = get_last_diaper_change_for_family(family_id)
            
            if last_diaper:
                # Используем тайское время для точности
                current_time = get_thai_time()
                time_since_last = current_time - last_diaper
                hours_since_last = time_since_last.total_seconds() / 3600
                minutes_since_last = time_since_last.total_seconds() / 60
                
                # Определяем статус и отправляем уведомления
                if hours_since_last >= diaper_interval:
                    # Пора менять подгузник!
                    if hours_since_last < (diaper_interval + 0.5):  # В пределах 30 минут после интервала
                        # Получаем всех членов семьи
                        cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                        members = cur.fetchall()
                        
                        # Создаем сообщение с кнопками для быстрых действий
                        message = (
                            f"🧷 **Время сменить подгузник!**\n\n"
                            f"⏰ Прошло: {hours_since_last:.1f} ч. ({minutes_since_last:.0f} мин.) с последней смены\n"
                            f"📅 Последняя смена: {last_diaper.strftime('%H:%M')}\n"
                            f"🔄 Интервал: {diaper_interval} ч.\n\n"
                            f"💡 Пора сменить подгузник малышу!\n\n"
                            f"🔄 Нажмите кнопку ниже, чтобы зафиксировать смену:"
                        )
                        
                        # Создаем кнопки для быстрых действий
                        buttons = [
                            [Button.inline("🧷 Сменить сейчас", b"diaper_now")],
                            [Button.inline("15 мин назад", b"diaper_15")],
                            [Button.inline("30 мин назад", b"diaper_30")]
                        ]
                        
                        # Отправляем уведомление всем членам семьи
                        for (user_id,) in members:
                            try:
                                await client.send_message(user_id, message, buttons=buttons)
                                print(f"✅ Отправлено уведомление о смене подгузника пользователю {user_id}")
                            except Exception as e:
                                print(f"❌ Ошибка отправки уведомления о смене подгузника пользователю {user_id}: {e}")
                    
                    elif hours_since_last >= (diaper_interval + 1):  # Через час после интервала - срочное уведомление
                        # Получаем всех членов семьи
                        cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                        members = cur.fetchall()
                        
                        # Срочное уведомление
                        urgent_message = (
                            f"🚨 **СРОЧНО! Долго не меняли подгузник!**\n\n"
                            f"⏰ Прошло: {hours_since_last:.1f} ч. ({minutes_since_last:.0f} мин.) с последней смены\n"
                            f"📅 Последняя смена: {last_diaper.strftime('%H:%M')}\n"
                            f"🔄 Интервал: {diaper_interval} ч.\n\n"
                            f"⚠️ Малыш может испытывать дискомфорт! Немедленно смените подгузник!"
                        )
                        
                        # Отправляем срочное уведомление всем членам семьи
                        for (user_id,) in members:
                            try:
                                await client.send_message(user_id, urgent_message)
                                print(f"🚨 Отправлено срочное уведомление о смене подгузника пользователю {user_id}")
                            except Exception as e:
                                print(f"❌ Ошибка отправки срочного уведомления о смене подгузника пользователю {user_id}: {e}")
                
                elif hours_since_last >= (diaper_interval - 0.25):  # За 15 минут до интервала - предварительное уведомление
                    # Получаем всех членов семьи
                    cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                    members = cur.fetchall()
                    
                    # Предварительное уведомление
                    pre_message = (
                        f"⏰ **Скоро время сменить подгузник**\n\n"
                        f"⏰ Прошло: {hours_since_last:.1f} ч. ({minutes_since_last:.0f} мин.) с последней смены\n"
                        f"📅 Последняя смена: {last_diaper.strftime('%H:%M')}\n"
                        f"🔄 Интервал: {diaper_interval} ч.\n\n"
                        f"💡 Через {diaper_interval - hours_since_last:.1f} ч. пора будет менять подгузник"
                    )
                    
                    # Отправляем предварительное уведомление всем членам семьи
                    for (user_id,) in members:
                        try:
                            await client.send_message(user_id, pre_message)
                            print(f"⏰ Отправлено предварительное уведомление о смене подгузника пользователю {user_id}")
                        except Exception as e:
                            print(f"❌ Ошибка отправки предварительного уведомления о смене подгузника пользователю {user_id}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка в send_scheduled_diaper_reminders: {e}")

# Новые планировщики для купания, игр и сна
@scheduler.scheduled_job('interval', minutes=30)
async def send_bath_reminders():
    """Отправлять напоминания о купании по расписанию"""
    try:
        current_time = get_thai_time()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        
        # Получаем все семьи с включенными напоминаниями о купании
        cur.execute("SELECT family_id, bath_reminder_hour, bath_reminder_minute, bath_reminder_period FROM settings WHERE bath_reminder_enabled = 1")
        families = cur.fetchall()
        
        for (family_id, reminder_hour, reminder_minute, period) in families:
            # Проверяем, пора ли отправлять напоминание о купании
            if current_hour == reminder_hour and current_minute == reminder_minute:
                # Получаем время последнего купания
                last_bath = get_last_bath_time_for_family(family_id)
                
                if last_bath:
                    # Проверяем, прошло ли достаточно времени
                    days_since_last = (current_time - last_bath).days
                    
                    if days_since_last >= period:
                        # Получаем всех членов семьи
                        cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                        members = cur.fetchall()
                        
                        # Создаем сообщение с кнопкой переноса
                        message = (
                            f"🛁 **Время купания!**\n\n"
                            f"⏰ Прошло: {days_since_last} дней с последнего купания\n"
                            f"📅 Последнее купание: {last_bath.strftime('%d.%m в %H:%M')}\n"
                            f"🔄 Период: {period} день(ей)\n\n"
                            f"💡 Пора искупать малыша!\n\n"
                            f"🔄 Нажмите кнопку ниже, чтобы зафиксировать купание:"
                        )
                        
                        # Создаем кнопки
                        buttons = [
                            [Button.inline("🛁 Купать сейчас", b"bath_now")],
                            [Button.inline("15 мин назад", b"bath_15")],
                            [Button.inline("30 мин назад", b"bath_30")]
                        ]
                        
                        # Отправляем уведомление всем членам семьи
                        for (user_id,) in members:
                            try:
                                await client.send_message(user_id, message, buttons=buttons)
                                print(f"✅ Отправлено напоминание о купании пользователю {user_id}")
                            except Exception as e:
                                print(f"❌ Ошибка отправки напоминания о купании пользователю {user_id}: {e}")
                else:
                    # Первое купание
                    cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                    members = cur.fetchall()
                    
                    message = (
                        f"🛁 **Первое купание!**\n\n"
                        f"👶 Пора начать купать малыша\n"
                        f"🔄 Период: {period} день(ей)\n\n"
                        f"💡 Запишите первое купание!"
                    )
                    
                    buttons = [
                        [Button.inline("🛁 Купать сейчас", b"bath_now")]
                    ]
                    
                    for (user_id,) in members:
                        try:
                            await client.send_message(user_id, message, buttons=buttons)
                            print(f"✅ Отправлено напоминание о первом купании пользователю {user_id}")
                        except Exception as e:
                            print(f"❌ Ошибка отправки напоминания о первом купании пользователю {user_id}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка в send_bath_reminders: {e}")

@scheduler.scheduled_job('interval', minutes=15)
async def send_smart_activity_reminders():
    """Отправлять умные напоминания об играх - не раньше чем за 20 минут до еды"""
    try:
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        
        # Получаем все семьи с включенными напоминаниями об играх
        cur.execute("SELECT family_id, activity_reminder_interval, baby_age_months FROM settings WHERE activity_reminder_enabled = 1")
        families = cur.fetchall()
        
        for (family_id, interval, age_months) in families:
            # Получаем время последней активности
            last_activity = get_last_activity_time_for_family(family_id, "tummy_time")
            
            # Получаем интервал кормления для этой семьи
            cur.execute("SELECT feed_interval FROM settings WHERE family_id = ?", (family_id,))
            feed_interval_result = cur.fetchone()
            feed_interval = feed_interval_result[0] if feed_interval_result else 3
            
            # Получаем время последнего кормления
            last_feeding = get_last_feeding_time_for_family(family_id)
            
            if last_activity and last_feeding:
                # Используем тайское время для точности
                current_time = get_thai_time()
                time_since_last_activity = current_time - last_activity
                time_since_last_feeding = current_time - last_feeding
                
                hours_since_last_activity = time_since_last_activity.total_seconds() / 3600
                hours_since_last_feeding = time_since_last_feeding.total_seconds() / 3600
                
                # Проверяем, пора ли играть (по интервалу активности)
                if hours_since_last_activity >= interval:
                    # Проверяем, не слишком ли близко к кормлению (не раньше чем за 20 минут)
                    minutes_until_feeding = (feed_interval - hours_since_last_feeding) * 60
                    
                    if minutes_until_feeding >= 20:  # Не раньше чем за 20 минут до еды
                        # Получаем всех членов семьи
                        cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                        members = cur.fetchall()
                        
                        # Получаем рекомендации по возрасту
                        activities = get_age_appropriate_activities(age_months)
                        
                        # Создаем сообщение с рекомендациями
                        message = (
                            f"🎮 **Время игр и активностей!**\n\n"
                            f"⏰ Прошло: {hours_since_last_activity:.1f} ч. с последней активности\n"
                            f"📅 Последняя активность: {last_activity.strftime('%H:%M')}\n"
                            f"🔄 Интервал: {interval} ч.\n"
                            f"👶 Возраст: {age_months} мес.\n"
                            f"🍼 До следующего кормления: {minutes_until_feeding:.0f} мин.\n\n"
                            f"💡 **Рекомендации для вашего возраста:**\n"
                            f"🦵 Выкладывание на живот: {activities['tummy_time']}\n"
                            f"🎯 Игры: {activities['play']}\n"
                            f"💆 Массаж: {activities['massage']}\n\n"
                            f"🔄 Нажмите кнопку ниже, чтобы зафиксировать активность:"
                        )
                        
                        # Создаем кнопки для быстрых действий
                        buttons = [
                            [Button.inline("🦵 Выкладывание на живот", b"activity_tummy")],
                            [Button.inline("🎯 Играть сейчас", b"activity_play")],
                            [Button.inline("💆 Массаж", b"activity_massage")]
                        ]
                        
                        # Отправляем уведомление всем членам семьи
                        for (user_id,) in members:
                            try:
                                await client.send_message(user_id, message, buttons=buttons)
                                print(f"✅ Отправлено умное напоминание об играх пользователю {user_id}")
                            except Exception as e:
                                print(f"❌ Ошибка отправки умного напоминания об играх пользователю {user_id}: {e}")
            elif not last_activity and last_feeding:
                # Первая активность - проверяем время до кормления
                current_time = get_thai_time()
                time_since_last_feeding = current_time - last_feeding
                hours_since_last_feeding = time_since_last_feeding.total_seconds() / 3600
                minutes_until_feeding = (feed_interval - hours_since_last_feeding) * 60
                
                if minutes_until_feeding >= 20:  # Не раньше чем за 20 минут до еды
                    cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                    members = cur.fetchall()
                    
                    activities = get_age_appropriate_activities(age_months)
                    
                    message = (
                        f"🎮 **Первая активность!**\n\n"
                        f"👶 Пора начать играть с малышом\n"
                        f"🔄 Рекомендуемый интервал: {interval} ч.\n"
                        f"👶 Возраст: {age_months} мес.\n"
                        f"🍼 До следующего кормления: {minutes_until_feeding:.0f} мин.\n\n"
                        f"💡 **Рекомендации для вашего возраста:**\n"
                        f"🦵 Выкладывание на живот: {activities['tummy_time']}\n"
                        f"🎯 Игры: {activities['play']}\n"
                        f"💆 Массаж: {activities['massage']}\n\n"
                        f"🔄 Начните с выкладывания на живот!"
                    )
                    
                    buttons = [
                        [Button.inline("🦵 Выкладывание на живот", b"activity_tummy")],
                        [Button.inline("🎯 Играть сейчас", b"activity_play")],
                        [Button.inline("💆 Массаж", b"activity_massage")]
                    ]
                    
                    for (user_id,) in members:
                        try:
                            await client.send_message(user_id, message, buttons=buttons)
                            print(f"✅ Отправлено умное напоминание о первой активности пользователю {user_id}")
                        except Exception as e:
                            print(f"❌ Ошибка отправки умного напоминания о первой активности пользователю {user_id}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка в send_smart_activity_reminders: {e}")

@scheduler.scheduled_job('interval', minutes=15)
async def monitor_sleep_and_feeding():
    """Мониторить сон и предупреждать о кормлении"""
    try:
        conn = sqlite3.connect("babybot.db")
        cur = conn.cursor()
        
        # Получаем все семьи с включенным мониторингом сна
        cur.execute("SELECT family_id FROM settings WHERE sleep_monitoring_enabled = 1")
        families = cur.fetchall()
        
        for (family_id,) in families:
            # Получаем активную сессию сна
            active_sleep = get_active_sleep_session(family_id)
            
            if active_sleep:
                # Получаем интервал кормления
                cur.execute("SELECT feed_interval FROM settings WHERE family_id = ?", (family_id,))
                interval_result = cur.fetchone()
                feed_interval = interval_result[0] if interval_result else 3
                
                # Проверяем, нужно ли разбудить для кормления
                should_wake = should_wake_for_feeding(active_sleep["start_time"], feed_interval)
                
                if should_wake:
                    # Получаем всех членов семьи
                    cur.execute("SELECT user_id FROM family_members WHERE family_id = ?", (family_id,))
                    members = cur.fetchall()
                    
                    sleep_duration = get_thai_time() - active_sleep["start_time"]
                    hours = int(sleep_duration.total_seconds() // 3600)
                    minutes = int((sleep_duration.total_seconds() % 3600) // 60)
                    
                    # Предупреждение о кормлении
                    warning_message = (
                        f"⚠️ **ВНИМАНИЕ! Малыш спит дольше интервала кормления!**\n\n"
                        f"😴 Малыш спит уже: {hours}ч {minutes}м\n"
                        f"⏰ Начало сна: {active_sleep['start_time'].strftime('%H:%M')}\n"
                        f"🔄 Интервал кормления: {feed_interval} ч.\n\n"
                        f"🍼 **Рекомендуется разбудить для кормления!**\n\n"
                        f"💡 Малыш может проснуться голодным, если сон выпадает на кормление"
                    )
                    
                    # Отправляем предупреждение всем членам семьи
                    for (user_id,) in members:
                        try:
                            await client.send_message(user_id, warning_message)
                            print(f"⚠️ Отправлено предупреждение о сне и кормлении пользователю {user_id}")
                        except Exception as e:
                            print(f"❌ Ошибка отправки предупреждения о сне и кормлении пользователю {user_id}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка в monitor_sleep_and_feeding: {e}")

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = f"""
            <html>
            <head><title>BabyCareBot Health Check</title></head>
            <body>
                <h1>🍼 BabyCareBot</h1>
                <p>Status: ✅ Running</p>
                <p>Time: {current_time}</p>
                <p>Bot is working in background</p>
                <p>Last Activity: {current_time}</p>
                <p>Uptime: Active</p>
                <p>Render Keep-Alive: Active</p>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = f'{{"status": "healthy", "service": "babycare-bot", "timestamp": "{current_time}", "uptime": "active", "render_keepalive": "active"}}'
            self.wfile.write(response.encode())
        elif self.path == '/ping':
            # Простой ping для постоянной активности
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"pong {current_time}".encode())
        elif self.path == '/status':
            # Расширенный статус
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = f'{{"status": "healthy", "bot": "running", "timestamp": "{current_time}", "health": "ok", "render_keepalive": "active"}}'
            self.wfile.write(response.encode())
        elif self.path == '/render-ping':
            # Специальный endpoint для Render
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = f'{{"status": "ok", "service": "babycare-bot", "timestamp": "{current_time}", "render": "active"}}'
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server(port=8000):
    """Запуск HTTP сервера для health checks"""
    try:
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            print(f"🌐 Health check server started on port {port}")
            print(f"🔗 Health check URLs:")
            print(f"   • Main: http://localhost:{port}/")
            print(f"   • Health: http://localhost:{port}/health")
            print(f"   • Ping: http://localhost:{port}/ping")
            print(f"   • Status: http://localhost:{port}/status")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ Health check server error: {e}")

async def start_bot():
    """Запуск бота"""
    print("🔍 Проверяем подключение к Telegram...")
    
    try:
        # Проверяем, что бот подключился
        me = await client.get_me()
        print(f"✅ Бот подключен: @{me.username}")
        print(f"🆔 ID бота: {me.id}")
        print(f"📝 Имя бота: {me.first_name}")
        
        # Запускаем health сервер в отдельном потоке
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        print("🌐 Health check server started")
        
        scheduler.start()
        print("✅ Бот запущен!")
        
        # Запускаем бота
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        print("🔍 Проверьте переменные окружения и токен бота")
        raise e

# Запуск бота
if __name__ == "__main__":
    try:
        print("🚀 Запуск BabyCareBot...")
        print(f"🔑 API_ID: {API_ID}")
        print(f"🔑 API_HASH: {API_HASH[:10]}...")  # Показываем только первые 10 символов
        print(f"🔑 BOT_TOKEN: {BOT_TOKEN[:10]}...")  # Показываем только первые 10 символов
        
        with client:
            client.loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔍 Проверьте логи для диагностики")
        import traceback
        traceback.print_exc()
