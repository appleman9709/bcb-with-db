#!/usr/bin/env python3
"""
Скрипт для проверки данных в Supabase
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

def check_data():
    print("🔍 Проверяем данные в Supabase...")
    
    # Проверяем семьи
    response = requests.get(f'{SUPABASE_URL}/rest/v1/families', headers=headers)
    if response.status_code == 200:
        families = response.json()
        print(f"📊 Семей в Supabase: {len(families)}")
        for family in families:
            print(f"   • ID: {family['id']}, Название: {family['name']}")
    else:
        print(f"❌ Ошибка получения семей: {response.text}")
    
    # Проверяем членов семьи
    response = requests.get(f'{SUPABASE_URL}/rest/v1/family_members', headers=headers)
    if response.status_code == 200:
        members = response.json()
        print(f"👥 Членов семьи в Supabase: {len(members)}")
        for member in members:
            print(f"   • Семья: {member['family_id']}, Пользователь: {member['user_id']}, Имя: {member['name']}")
    else:
        print(f"❌ Ошибка получения членов семьи: {response.text}")
    
    # Проверяем кормления
    response = requests.get(f'{SUPABASE_URL}/rest/v1/feedings', headers=headers)
    if response.status_code == 200:
        feedings = response.json()
        print(f"🍼 Кормлений в Supabase: {len(feedings)}")
    else:
        print(f"❌ Ошибка получения кормлений: {response.text}")

if __name__ == "__main__":
    check_data()
