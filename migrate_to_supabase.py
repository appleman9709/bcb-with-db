#!/usr/bin/env python3
"""
Скрипт для миграции данных из SQLite в Supabase
"""
import sqlite3
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ОШИБКА: Не установлены переменные SUPABASE_URL и SUPABASE_KEY")
    exit(1)

# Заголовки для запросов к Supabase
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

def make_supabase_request(method, endpoint, data=None):
    """Выполняет HTTP запрос к Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else None
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка Supabase запроса: {e}")
        return None

def migrate_families(sqlite_conn):
    """Мигрирует семьи"""
    print("🏠 Миграция семей...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT id, name FROM families")
    families = cursor.fetchall()
    
    migrated_count = 0
    for family_id, name in families:
        data = {'name': name}
        result = make_supabase_request('POST', 'families', data)
        if result:
            print(f"   ✅ Семья '{name}' (ID: {family_id}) -> Supabase ID: {result['id']}")
            migrated_count += 1
        else:
            print(f"   ❌ Ошибка миграции семьи '{name}'")
    
    print(f"📊 Мигрировано семей: {migrated_count}/{len(families)}")
    return migrated_count

def migrate_family_members(sqlite_conn):
    """Мигрирует членов семьи"""
    print("👥 Миграция членов семьи...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT family_id, user_id, role, name FROM family_members")
    members = cursor.fetchall()
    
    migrated_count = 0
    for family_id, user_id, role, name in members:
        data = {
            'family_id': family_id,
            'user_id': user_id,
            'role': role,
            'name': name
        }
        result = make_supabase_request('POST', 'family_members', data)
        if result:
            print(f"   ✅ Член семьи '{name}' (роль: {role})")
            migrated_count += 1
        else:
            print(f"   ❌ Ошибка миграции члена семьи '{name}'")
    
    print(f"📊 Мигрировано членов семьи: {migrated_count}/{len(members)}")
    return migrated_count

def migrate_feedings(sqlite_conn):
    """Мигрирует кормления"""
    print("🍼 Миграция кормлений...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT family_id, author_id, timestamp, author_role, author_name FROM feedings")
    feedings = cursor.fetchall()
    
    migrated_count = 0
    for family_id, author_id, timestamp, author_role, author_name in feedings:
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'timestamp': timestamp,
            'author_role': author_role,
            'author_name': author_name
        }
        result = make_supabase_request('POST', 'feedings', data)
        if result:
            migrated_count += 1
        else:
            print(f"   ❌ Ошибка миграции кормления от {author_name}")
    
    print(f"📊 Мигрировано кормлений: {migrated_count}/{len(feedings)}")
    return migrated_count

def migrate_diapers(sqlite_conn):
    """Мигрирует смены подгузников"""
    print("👶 Миграция смен подгузников...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT family_id, author_id, timestamp, author_role, author_name FROM diapers")
    diapers = cursor.fetchall()
    
    migrated_count = 0
    for family_id, author_id, timestamp, author_role, author_name in diapers:
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'timestamp': timestamp,
            'author_role': author_role,
            'author_name': author_name
        }
        result = make_supabase_request('POST', 'diapers', data)
        if result:
            migrated_count += 1
        else:
            print(f"   ❌ Ошибка миграции смены подгузника от {author_name}")
    
    print(f"📊 Мигрировано смен подгузников: {migrated_count}/{len(diapers)}")
    return migrated_count

def migrate_baths(sqlite_conn):
    """Мигрирует купания"""
    print("🛁 Миграция купаний...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT family_id, author_id, timestamp, author_role, author_name FROM baths")
    baths = cursor.fetchall()
    
    migrated_count = 0
    for family_id, author_id, timestamp, author_role, author_name in baths:
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'timestamp': timestamp,
            'author_role': author_role,
            'author_name': author_name
        }
        result = make_supabase_request('POST', 'baths', data)
        if result:
            migrated_count += 1
        else:
            print(f"   ❌ Ошибка миграции купания от {author_name}")
    
    print(f"📊 Мигрировано купаний: {migrated_count}/{len(baths)}")
    return migrated_count

def migrate_activities(sqlite_conn):
    """Мигрирует активности"""
    print("🎮 Миграция активностей...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT family_id, author_id, timestamp, activity_type, author_role, author_name FROM activities")
    activities = cursor.fetchall()
    
    migrated_count = 0
    for family_id, author_id, timestamp, activity_type, author_role, author_name in activities:
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'timestamp': timestamp,
            'activity_type': activity_type,
            'author_role': author_role,
            'author_name': author_name
        }
        result = make_supabase_request('POST', 'activities', data)
        if result:
            migrated_count += 1
        else:
            print(f"   ❌ Ошибка миграции активности от {author_name}")
    
    print(f"📊 Мигрировано активностей: {migrated_count}/{len(activities)}")
    return migrated_count

def migrate_sleep_sessions(sqlite_conn):
    """Мигрирует сессии сна"""
    print("😴 Миграция сессий сна...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT family_id, author_id, start_time, end_time, is_active, author_role, author_name FROM sleep_sessions")
    sessions = cursor.fetchall()
    
    migrated_count = 0
    for family_id, author_id, start_time, end_time, is_active, author_role, author_name in sessions:
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'start_time': start_time,
            'end_time': end_time,
            'is_active': bool(is_active),
            'author_role': author_role,
            'author_name': author_name
        }
        result = make_supabase_request('POST', 'sleep_sessions', data)
        if result:
            migrated_count += 1
        else:
            print(f"   ❌ Ошибка миграции сессии сна от {author_name}")
    
    print(f"📊 Мигрировано сессий сна: {migrated_count}/{len(sessions)}")
    return migrated_count

def migrate_settings(sqlite_conn):
    """Мигрирует настройки"""
    print("⚙️ Миграция настроек...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT family_id, feed_interval, diaper_interval, tips_enabled, 
               tips_time_hour, tips_time_minute, bath_reminder_enabled,
               bath_reminder_hour, bath_reminder_minute, bath_reminder_period,
               activity_reminder_enabled, activity_reminder_interval,
               sleep_monitoring_enabled, baby_age_months, birth_date
        FROM settings
    """)
    settings = cursor.fetchall()
    
    migrated_count = 0
    for (family_id, feed_interval, diaper_interval, tips_enabled, 
         tips_time_hour, tips_time_minute, bath_reminder_enabled,
         bath_reminder_hour, bath_reminder_minute, bath_reminder_period,
         activity_reminder_enabled, activity_reminder_interval,
         sleep_monitoring_enabled, baby_age_months, birth_date) in settings:
        
        data = {
            'family_id': family_id,
            'feed_interval': feed_interval,
            'diaper_interval': diaper_interval,
            'tips_enabled': bool(tips_enabled),
            'tips_time_hour': tips_time_hour,
            'tips_time_minute': tips_time_minute,
            'bath_reminder_enabled': bool(bath_reminder_enabled),
            'bath_reminder_hour': bath_reminder_hour,
            'bath_reminder_minute': bath_reminder_minute,
            'bath_reminder_period': bath_reminder_period,
            'activity_reminder_enabled': bool(activity_reminder_enabled),
            'activity_reminder_interval': activity_reminder_interval,
            'sleep_monitoring_enabled': bool(sleep_monitoring_enabled),
            'baby_age_months': baby_age_months,
            'baby_birth_date': birth_date
        }
        result = make_supabase_request('POST', 'settings', data)
        if result:
            migrated_count += 1
        else:
            print(f"   ❌ Ошибка миграции настроек для семьи {family_id}")
    
    print(f"📊 Мигрировано настроек: {migrated_count}/{len(settings)}")
    return migrated_count

def main():
    """Основная функция миграции"""
    print("🚀 Начинаем миграцию данных из SQLite в Supabase")
    print("=" * 50)
    
    # Проверяем наличие базы данных
    db_files = ['babybot.db', 'babybot_render.db']
    db_file = None
    
    for file in db_files:
        if os.path.exists(file):
            db_file = file
            break
    
    if not db_file:
        print("❌ ОШИБКА: Не найдена база данных SQLite!")
        print("📝 Убедитесь, что файл babybot.db или babybot_render.db существует")
        return
    
    print(f"📁 Используем базу данных: {db_file}")
    
    # Подключаемся к SQLite
    try:
        sqlite_conn = sqlite3.connect(db_file)
        print("✅ Подключение к SQLite успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения к SQLite: {e}")
        return
    
    # Проверяем подключение к Supabase
    print("🔍 Проверяем подключение к Supabase...")
    health_check = make_supabase_request('GET', 'families', {'limit': '1'})
    if health_check is None:
        print("❌ Ошибка подключения к Supabase!")
        return
    print("✅ Подключение к Supabase успешно")
    
    # Выполняем миграцию
    total_migrated = 0
    
    try:
        total_migrated += migrate_families(sqlite_conn)
        total_migrated += migrate_family_members(sqlite_conn)
        total_migrated += migrate_feedings(sqlite_conn)
        total_migrated += migrate_diapers(sqlite_conn)
        total_migrated += migrate_baths(sqlite_conn)
        total_migrated += migrate_activities(sqlite_conn)
        total_migrated += migrate_sleep_sessions(sqlite_conn)
        total_migrated += migrate_settings(sqlite_conn)
        
        print("=" * 50)
        print(f"✅ Миграция завершена!")
        print(f"📊 Всего записей мигрировано: {total_migrated}")
        print("🎉 Данные успешно перенесены в Supabase!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка миграции: {e}")
    finally:
        sqlite_conn.close()

if __name__ == "__main__":
    main()
