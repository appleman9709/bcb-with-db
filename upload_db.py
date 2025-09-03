#!/usr/bin/env python3
"""
Скрипт для загрузки базы данных на Render
"""
import os
import shutil
import sqlite3

def upload_database():
    """Загружает базу данных на Render"""
    try:
        # Проверяем, что база данных существует
        if not os.path.exists("babybot.db"):
            print("❌ База данных babybot.db не найдена!")
            return False
        
        # Создаем копию для Render
        shutil.copy2("babybot.db", "babybot_render.db")
        print("✅ База данных скопирована для Render")
        
        # Проверяем подключение к базе
        conn = sqlite3.connect("babybot_render.db")
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"   • {table[0]}")
        
        # Проверяем семьи
        cursor.execute("SELECT COUNT(*) FROM families")
        family_count = cursor.fetchone()[0]
        print(f"👨‍👩‍👧‍👦 Найдено семей: {family_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке БД: {e}")
        return False

if __name__ == "__main__":
    upload_database()
