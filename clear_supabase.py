#!/usr/bin/env python3
"""
Скрипт для полной очистки данных в Supabase
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

def clear_all_data():
    """Очищает все данные в Supabase"""
    print("🧹 Очистка всех данных в Supabase...")
    
    # Получаем все ID семей
    response = requests.get(f'{SUPABASE_URL}/rest/v1/families', headers=headers)
    if response.status_code == 200:
        families = response.json()
        family_ids = [str(family['id']) for family in families]
        print(f"📊 Найдено семей: {len(family_ids)}")
        
        if family_ids:
            # Удаляем все данные по family_id
            for family_id in family_ids:
                print(f"🗑️ Удаляем данные для семьи {family_id}...")
                
                # Удаляем события
                for table in ['feedings', 'diapers', 'baths', 'activities', 'sleep_sessions']:
                    response = requests.delete(
                        f'{SUPABASE_URL}/rest/v1/{table}',
                        headers=headers,
                        params={'family_id': f'eq.{family_id}'}
                    )
                    if response.status_code in [200, 204]:
                        print(f"   ✅ Очищена таблица {table}")
                    else:
                        print(f"   ⚠️ Ошибка очистки {table}: {response.text}")
                
                # Удаляем членов семьи и настройки
                for table in ['family_members', 'settings']:
                    response = requests.delete(
                        f'{SUPABASE_URL}/rest/v1/{table}',
                        headers=headers,
                        params={'family_id': f'eq.{family_id}'}
                    )
                    if response.status_code in [200, 204]:
                        print(f"   ✅ Очищена таблица {table}")
                    else:
                        print(f"   ⚠️ Ошибка очистки {table}: {response.text}")
                
                # Удаляем семью
                response = requests.delete(
                    f'{SUPABASE_URL}/rest/v1/families',
                    headers=headers,
                    params={'id': f'eq.{family_id}'}
                )
                if response.status_code in [200, 204]:
                    print(f"   ✅ Удалена семья {family_id}")
                else:
                    print(f"   ⚠️ Ошибка удаления семьи {family_id}: {response.text}")
        
        print("✅ Очистка завершена!")
    else:
        print(f"❌ Ошибка получения семей: {response.text}")

if __name__ == "__main__":
    clear_all_data()
