#!/usr/bin/env python3
"""
Скрипт для синхронизации локальной базы данных с Render
"""
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime

def sync_database():
    """Синхронизирует локальную базу данных с Render"""
    try:
        print(f"🔄 Синхронизация базы данных - {datetime.now().strftime('%H:%M:%S')}")
        
        # Проверяем, что локальная база существует
        if not os.path.exists("babybot.db"):
            print("❌ Локальная база данных babybot.db не найдена!")
            return False
        
        # Создаем копию для Render
        shutil.copy2("babybot.db", "babybot_render.db")
        print("✅ База данных скопирована для Render")
        
        # Проверяем изменения
        conn = sqlite3.connect("babybot_render.db")
        cursor = conn.cursor()
        
        # Проверяем статистику
        cursor.execute("SELECT COUNT(*) FROM feedings")
        feedings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM diapers")
        diapers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM activities")
        activities = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM baths")
        baths = cursor.fetchone()[0]
        
        print(f"📊 Текущая статистика:")
        print(f"   • Кормления: {feedings}")
        print(f"   • Подгузники: {diapers}")
        print(f"   • Активности: {activities}")
        print(f"   • Купания: {baths}")
        
        conn.close()
        
        # Добавляем в Git
        print("📤 Отправка на GitHub...")
        subprocess.run(["git", "add", "babybot_render.db"], check=True)
        subprocess.run(["git", "commit", "-m", f"Обновление данных - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print("✅ Данные успешно синхронизированы с Render!")
        print("⏰ Render обновит API через 2-3 минуты")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при синхронизации: {e}")
        return False

if __name__ == "__main__":
    sync_database()
