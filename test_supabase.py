#!/usr/bin/env python3
"""
Тест создания записи в Supabase
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

def test_create_family():
    """Тестирует создание семьи"""
    print("🧪 Тестируем создание семьи...")
    
    data = {'name': 'Тестовая семья'}
    response = requests.post(f'{SUPABASE_URL}/rest/v1/families', headers=headers, json=data)
    
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.text}")
    
    if response.status_code == 201:
        if response.text:
            family = response.json()
            print(f"✅ Семья создана с ID: {family[0]['id']}")
            return family[0]['id']
        else:
            print("✅ Семья создана (пустой ответ)")
            # Получаем ID созданной семьи
            get_response = requests.get(f'{SUPABASE_URL}/rest/v1/families', headers=headers)
            if get_response.status_code == 200:
                families = get_response.json()
                if families:
                    print(f"✅ Получен ID семьи: {families[-1]['id']}")
                    return families[-1]['id']
            return None
    else:
        print(f"❌ Ошибка создания семьи: {response.text}")
        return None

def test_create_member(family_id):
    """Тестирует создание члена семьи"""
    print(f"🧪 Тестируем создание члена семьи для семьи {family_id}...")
    
    data = {
        'family_id': family_id,
        'user_id': 123456789,
        'role': 'Тестер',
        'name': 'Тестовый пользователь'
    }
    response = requests.post(f'{SUPABASE_URL}/rest/v1/family_members', headers=headers, json=data)
    
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.text}")
    
    if response.status_code == 201:
        print("✅ Член семьи создан")
        return True
    else:
        print(f"❌ Ошибка создания члена семьи: {response.text}")
        return False

if __name__ == "__main__":
    family_id = test_create_family()
    if family_id:
        test_create_member(family_id)
