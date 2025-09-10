from telethon import TelegramClient, events, Button
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import random
import threading
import time
import http.server
import socketserver
import pytz
import subprocess
import requests
import json

# Конфигурация (загружается из переменных окружения)
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем данные из переменных окружения
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Проверяем наличие всех необходимых переменных
if not all([API_ID, API_HASH, BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ ОШИБКА: Не все необходимые переменные окружения установлены!")
    print("📝 Убедитесь, что в .env файле или переменных окружения установлены:")
    print("   • API_ID")
    print("   • API_HASH") 
    print("   • BOT_TOKEN")
    print("   • SUPABASE_URL")
    print("   • SUPABASE_KEY")
    print("🔧 Создайте .env файл на основе env_example.txt")
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

# Класс для работы с Supabase
class SupabaseClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, data=None):
        """Выполняет HTTP запрос к Supabase"""
        url = f"{self.url}/rest/v1/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка Supabase запроса: {e}")
            return None
    
    def get_family_by_user(self, user_id):
        """Получить семью пользователя"""
        # Сначала ищем пользователя в family_members
        members = self._make_request('GET', 'family_members', {'user_id': f'eq.{user_id}'})
        if members and len(members) > 0:
            family_id = members[0]['family_id']
            # Получаем информацию о семье
            family = self._make_request('GET', 'families', {'id': f'eq.{family_id}'})
            return family[0] if family else None
        return None
    
    def create_family(self, name):
        """Создать новую семью"""
        data = {'name': name}
        result = self._make_request('POST', 'families', data)
        return result[0] if result else None
    
    def add_family_member(self, family_id, user_id, role, name):
        """Добавить члена семьи"""
        data = {
            'family_id': family_id,
            'user_id': user_id,
            'role': role,
            'name': name
        }
        return self._make_request('POST', 'family_members', data)
    
    def add_feeding(self, family_id, author_id, author_role, author_name):
        """Добавить кормление"""
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'timestamp': get_thai_time().isoformat(),
            'author_role': author_role,
            'author_name': author_name
        }
        return self._make_request('POST', 'feedings', data)
    
    def add_diaper(self, family_id, author_id, author_role, author_name):
        """Добавить смену подгузника"""
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'timestamp': get_thai_time().isoformat(),
            'author_role': author_role,
            'author_name': author_name
        }
        return self._make_request('POST', 'diapers', data)
    
    def add_bath(self, family_id, author_id, author_role, author_name):
        """Добавить купание"""
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'timestamp': get_thai_time().isoformat(),
            'author_role': author_role,
            'author_name': author_name
        }
        return self._make_request('POST', 'baths', data)
    
    def add_activity(self, family_id, author_id, activity_type, author_role, author_name):
        """Добавить активность"""
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'timestamp': get_thai_time().isoformat(),
            'activity_type': activity_type,
            'author_role': author_role,
            'author_name': author_name
        }
        return self._make_request('POST', 'activities', data)
    
    def start_sleep(self, family_id, author_id, author_role, author_name):
        """Начать сессию сна"""
        # Сначала завершаем все активные сессии сна
        self._make_request('PATCH', 'sleep_sessions', 
                          {'is_active': False}, 
                          {'family_id': f'eq.{family_id}', 'is_active': 'eq.true'})
        
        # Создаем новую активную сессию
        data = {
            'family_id': family_id,
            'author_id': author_id,
            'start_time': get_thai_time().isoformat(),
            'is_active': True,
            'author_role': author_role,
            'author_name': author_name
        }
        return self._make_request('POST', 'sleep_sessions', data)
    
    def end_sleep(self, family_id, author_id, author_role, author_name):
        """Завершить сессию сна"""
        data = {
            'end_time': get_thai_time().isoformat(),
            'is_active': False
        }
        return self._make_request('PATCH', 'sleep_sessions', data, 
                                 {'family_id': f'eq.{family_id}', 'is_active': f'eq.true'})
    
    def get_last_events(self, family_id):
        """Получить последние события"""
        # Получаем последние события из всех таблиц
        feedings = self._make_request('GET', 'feedings', 
                                    {'family_id': f'eq.{family_id}', 
                                     'order': 'timestamp.desc', 
                                     'limit': '1'})
        diapers = self._make_request('GET', 'diapers', 
                                   {'family_id': f'eq.{family_id}', 
                                    'order': 'timestamp.desc', 
                                    'limit': '1'})
        baths = self._make_request('GET', 'baths', 
                                 {'family_id': f'eq.{family_id}', 
                                  'order': 'timestamp.desc', 
                                  'limit': '1'})
        activities = self._make_request('GET', 'activities', 
                                      {'family_id': f'eq.{family_id}', 
                                       'order': 'timestamp.desc', 
                                       'limit': '1'})
        sleep = self._make_request('GET', 'sleep_sessions', 
                                 {'family_id': f'eq.{family_id}', 
                                  'is_active': 'eq.true', 
                                  'order': 'start_time.desc', 
                                  'limit': '1'})
        
        return {
            'feeding': feedings[0] if feedings else None,
            'diaper': diapers[0] if diapers else None,
            'bath': baths[0] if baths else None,
            'activity': activities[0] if activities else None,
            'sleep': sleep[0] if sleep else None
        }

# Создаем клиент Supabase
supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)

client = TelegramClient('babybot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Словарь для хранения состояний пользователей
user_states = {}

# Функция для получения роли пользователя
def get_user_role(user_id, family_id):
    """Получить роль пользователя в семье"""
    members = supabase._make_request('GET', 'family_members', 
                                   {'family_id': f'eq.{family_id}', 'user_id': f'eq.{user_id}'})
    if members and len(members) > 0:
        return members[0]['role']
    return 'Родитель'

# Функция для получения имени пользователя
def get_user_name(user_id, family_id):
    """Получить имя пользователя в семье"""
    members = supabase._make_request('GET', 'family_members', 
                                   {'family_id': f'eq.{family_id}', 'user_id': f'eq.{user_id}'})
    if members and len(members) > 0:
        return members[0]['name']
    return 'Неизвестно'

# Функция для форматирования времени
def format_time_ago(timestamp):
    """Форматировать время с последнего события"""
    if not timestamp:
        return "Неизвестно"
    
    try:
        event_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        current_time = get_thai_time()
        diff = current_time - event_time
        
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}ч {minutes}м назад"
        else:
            return f"{minutes}м назад"
    except:
        return "Неизвестно"

# Обработчик команды /start
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    user_info = await client.get_entity(user_id)
    user_name = user_info.first_name or "Пользователь"
    
    # Проверяем, есть ли у пользователя семья
    family = supabase.get_family_by_user(user_id)
    
    if family:
        # Пользователь уже в семье
        family_name = family['name']
        role = get_user_role(user_id, family['id'])
        name = get_user_name(user_id, family['id'])
        
        message = f"👋 Привет, {name}!\n\n"
        message += f"🏠 Вы в семье: {family_name}\n"
        message += f"👤 Ваша роль: {role}\n\n"
        message += "📱 Выберите действие:"
        
        buttons = [
            [Button.inline("🍼 Кормление", b"feeding")],
            [Button.inline("👶 Смена подгузника", b"diaper")],
            [Button.inline("🛁 Купание", b"bath")],
            [Button.inline("🎮 Активность", b"activity")],
            [Button.inline("😴 Сон", b"sleep")],
            [Button.inline("📊 Дашборд", b"dashboard")],
            [Button.inline("ℹ️ Информация", b"info")]
        ]
        
        await event.respond(message, buttons=buttons)
    else:
        # Пользователь не в семье - предлагаем создать или присоединиться
        message = f"👋 Привет, {user_name}!\n\n"
        message += "🏠 Добро пожаловать в BabyCareBot!\n\n"
        message += "📝 Выберите действие:"
        
        buttons = [
            [Button.inline("🏠 Создать семью", b"create_family")],
            [Button.inline("🔗 Присоединиться к семье", b"join_family")],
            [Button.inline("ℹ️ Информация", b"info")]
        ]
        
        await event.respond(message, buttons=buttons)

# Обработчик создания семьи
@client.on(events.CallbackQuery(data=b'create_family'))
async def create_family_handler(event):
    user_id = event.sender_id
    user_states[user_id] = 'waiting_family_name'
    
    await event.edit("🏠 Создание семьи\n\n📝 Введите название семьи:")

# Обработчик присоединения к семье
@client.on(events.CallbackQuery(data=b'join_family'))
async def join_family_handler(event):
    user_id = event.sender_id
    user_states[user_id] = 'waiting_family_id'
    
    await event.edit("🔗 Присоединение к семье\n\n📝 Введите ID семьи (попросите у администратора семьи):")

# Обработчик текстовых сообщений
@client.on(events.NewMessage)
async def text_handler(event):
    user_id = event.sender_id
    text = event.text
    
    if user_id in user_states:
        if user_states[user_id] == 'waiting_family_name':
            # Создаем семью
            family = supabase.create_family(text)
            if family:
                family_id = family['id']
                # Добавляем создателя как администратора
                supabase.add_family_member(family_id, user_id, "Администратор", 
                                         event.sender.first_name or "Пользователь")
                
                message = f"✅ Семья '{text}' создана успешно!\n\n"
                message += f"🆔 ID семьи: {family_id}\n"
                message += f"👤 Ваша роль: Администратор\n\n"
                message += "📱 Теперь вы можете использовать бота!"
                
                buttons = [
                    [Button.inline("🍼 Кормление", b"feeding")],
                    [Button.inline("👶 Смена подгузника", b"diaper")],
                    [Button.inline("🛁 Купание", b"bath")],
                    [Button.inline("🎮 Активность", b"activity")],
                    [Button.inline("😴 Сон", b"sleep")],
                    [Button.inline("📊 Дашборд", b"dashboard")]
                ]
                
                await event.respond(message, buttons=buttons)
            else:
                await event.respond("❌ Ошибка создания семьи. Попробуйте еще раз.")
            
            del user_states[user_id]
            
        elif user_states[user_id] == 'waiting_family_id':
            # Присоединяемся к семье
            try:
                family_id = int(text)
                # Проверяем существование семьи
                family = supabase._make_request('GET', 'families', {'id': f'eq.{family_id}'})
                if family and len(family) > 0:
                    # Добавляем пользователя в семью
                    result = supabase.add_family_member(family_id, user_id, "Родитель", 
                                                      event.sender.first_name or "Пользователь")
                    if result:
                        message = f"✅ Вы успешно присоединились к семье!\n\n"
                        message += f"🏠 Семья: {family[0]['name']}\n"
                        message += f"👤 Ваша роль: Родитель\n\n"
                        message += "📱 Теперь вы можете использовать бота!"
                        
                        buttons = [
                            [Button.inline("🍼 Кормление", b"feeding")],
                            [Button.inline("👶 Смена подгузника", b"diaper")],
                            [Button.inline("🛁 Купание", b"bath")],
                            [Button.inline("🎮 Активность", b"activity")],
                            [Button.inline("😴 Сон", b"sleep")],
                            [Button.inline("📊 Дашборд", b"dashboard")]
                        ]
                        
                        await event.respond(message, buttons=buttons)
                    else:
                        await event.respond("❌ Ошибка присоединения к семье. Возможно, вы уже в этой семье.")
                else:
                    await event.respond("❌ Семья с таким ID не найдена.")
            except ValueError:
                await event.respond("❌ Неверный формат ID. Введите число.")
            
            del user_states[user_id]

# Обработчики кнопок
@client.on(events.CallbackQuery(data=b'feeding'))
async def feeding_handler(event):
    user_id = event.sender_id
    family = supabase.get_family_by_user(user_id)
    
    if not family:
        await event.answer("❌ Вы не в семье!")
        return
    
    # Добавляем кормление
    result = supabase.add_feeding(family['id'], user_id, 
                                 get_user_role(user_id, family['id']),
                                 get_user_name(user_id, family['id']))
    
    if result:
        current_time = get_thai_time().strftime("%H:%M")
        await event.answer(f"✅ Кормление записано в {current_time}")
        
        # Показываем последние события
        events = supabase.get_last_events(family['id'])
        message = "🍼 Кормление записано!\n\n"
        message += "📊 Последние события:\n"
        
        if events['feeding']:
            message += f"🍼 Кормление: {format_time_ago(events['feeding']['timestamp'])}\n"
        if events['diaper']:
            message += f"👶 Подгузник: {format_time_ago(events['diaper']['timestamp'])}\n"
        if events['bath']:
            message += f"🛁 Купание: {format_time_ago(events['bath']['timestamp'])}\n"
        if events['activity']:
            message += f"🎮 Активность: {format_time_ago(events['activity']['timestamp'])}\n"
        if events['sleep']:
            message += f"😴 Сон: {format_time_ago(events['sleep']['start_time'])}\n"
        
        buttons = [
            [Button.inline("🍼 Кормление", b"feeding")],
            [Button.inline("👶 Смена подгузника", b"diaper")],
            [Button.inline("🛁 Купание", b"bath")],
            [Button.inline("🎮 Активность", b"activity")],
            [Button.inline("😴 Сон", b"sleep")],
            [Button.inline("📊 Дашборд", b"dashboard")],
            [Button.inline("ℹ️ Информация", b"info")]
        ]
        
        await event.edit(message, buttons=buttons)
    else:
        await event.answer("❌ Ошибка записи кормления!")

@client.on(events.CallbackQuery(data=b'diaper'))
async def diaper_handler(event):
    user_id = event.sender_id
    family = supabase.get_family_by_user(user_id)
    
    if not family:
        await event.answer("❌ Вы не в семье!")
        return
    
    # Добавляем смену подгузника
    result = supabase.add_diaper(family['id'], user_id, 
                                get_user_role(user_id, family['id']),
                                get_user_name(user_id, family['id']))
    
    if result:
        current_time = get_thai_time().strftime("%H:%M")
        await event.answer(f"✅ Смена подгузника записана в {current_time}")
        
        # Показываем последние события
        events = supabase.get_last_events(family['id'])
        message = "👶 Смена подгузника записана!\n\n"
        message += "📊 Последние события:\n"
        
        if events['feeding']:
            message += f"🍼 Кормление: {format_time_ago(events['feeding']['timestamp'])}\n"
        if events['diaper']:
            message += f"👶 Подгузник: {format_time_ago(events['diaper']['timestamp'])}\n"
        if events['bath']:
            message += f"🛁 Купание: {format_time_ago(events['bath']['timestamp'])}\n"
        if events['activity']:
            message += f"🎮 Активность: {format_time_ago(events['activity']['timestamp'])}\n"
        if events['sleep']:
            message += f"😴 Сон: {format_time_ago(events['sleep']['start_time'])}\n"
        
        buttons = [
            [Button.inline("🍼 Кормление", b"feeding")],
            [Button.inline("👶 Смена подгузника", b"diaper")],
            [Button.inline("🛁 Купание", b"bath")],
            [Button.inline("🎮 Активность", b"activity")],
            [Button.inline("😴 Сон", b"sleep")],
            [Button.inline("📊 Дашборд", b"dashboard")],
            [Button.inline("ℹ️ Информация", b"info")]
        ]
        
        await event.edit(message, buttons=buttons)
    else:
        await event.answer("❌ Ошибка записи смены подгузника!")

@client.on(events.CallbackQuery(data=b'bath'))
async def bath_handler(event):
    user_id = event.sender_id
    family = supabase.get_family_by_user(user_id)
    
    if not family:
        await event.answer("❌ Вы не в семье!")
        return
    
    # Добавляем купание
    result = supabase.add_bath(family['id'], user_id, 
                              get_user_role(user_id, family['id']),
                              get_user_name(user_id, family['id']))
    
    if result:
        current_time = get_thai_time().strftime("%H:%M")
        await event.answer(f"✅ Купание записано в {current_time}")
        
        # Показываем последние события
        events = supabase.get_last_events(family['id'])
        message = "🛁 Купание записано!\n\n"
        message += "📊 Последние события:\n"
        
        if events['feeding']:
            message += f"🍼 Кормление: {format_time_ago(events['feeding']['timestamp'])}\n"
        if events['diaper']:
            message += f"👶 Подгузник: {format_time_ago(events['diaper']['timestamp'])}\n"
        if events['bath']:
            message += f"🛁 Купание: {format_time_ago(events['bath']['timestamp'])}\n"
        if events['activity']:
            message += f"🎮 Активность: {format_time_ago(events['activity']['timestamp'])}\n"
        if events['sleep']:
            message += f"😴 Сон: {format_time_ago(events['sleep']['start_time'])}\n"
        
        buttons = [
            [Button.inline("🍼 Кормление", b"feeding")],
            [Button.inline("👶 Смена подгузника", b"diaper")],
            [Button.inline("🛁 Купание", b"bath")],
            [Button.inline("🎮 Активность", b"activity")],
            [Button.inline("😴 Сон", b"sleep")],
            [Button.inline("📊 Дашборд", b"dashboard")],
            [Button.inline("ℹ️ Информация", b"info")]
        ]
        
        await event.edit(message, buttons=buttons)
    else:
        await event.answer("❌ Ошибка записи купания!")

@client.on(events.CallbackQuery(data=b'activity'))
async def activity_handler(event):
    user_id = event.sender_id
    family = supabase.get_family_by_user(user_id)
    
    if not family:
        await event.answer("❌ Вы не в семье!")
        return
    
    # Добавляем активность
    result = supabase.add_activity(family['id'], user_id, "tummy_time",
                                  get_user_role(user_id, family['id']),
                                  get_user_name(user_id, family['id']))
    
    if result:
        current_time = get_thai_time().strftime("%H:%M")
        await event.answer(f"✅ Активность записана в {current_time}")
        
        # Показываем последние события
        events = supabase.get_last_events(family['id'])
        message = "🎮 Активность записана!\n\n"
        message += "📊 Последние события:\n"
        
        if events['feeding']:
            message += f"🍼 Кормление: {format_time_ago(events['feeding']['timestamp'])}\n"
        if events['diaper']:
            message += f"👶 Подгузник: {format_time_ago(events['diaper']['timestamp'])}\n"
        if events['bath']:
            message += f"🛁 Купание: {format_time_ago(events['bath']['timestamp'])}\n"
        if events['activity']:
            message += f"🎮 Активность: {format_time_ago(events['activity']['timestamp'])}\n"
        if events['sleep']:
            message += f"😴 Сон: {format_time_ago(events['sleep']['start_time'])}\n"
        
        buttons = [
            [Button.inline("🍼 Кормление", b"feeding")],
            [Button.inline("👶 Смена подгузника", b"diaper")],
            [Button.inline("🛁 Купание", b"bath")],
            [Button.inline("🎮 Активность", b"activity")],
            [Button.inline("😴 Сон", b"sleep")],
            [Button.inline("📊 Дашборд", b"dashboard")],
            [Button.inline("ℹ️ Информация", b"info")]
        ]
        
        await event.edit(message, buttons=buttons)
    else:
        await event.answer("❌ Ошибка записи активности!")

@client.on(events.CallbackQuery(data=b'sleep'))
async def sleep_handler(event):
    user_id = event.sender_id
    family = supabase.get_family_by_user(user_id)
    
    if not family:
        await event.answer("❌ Вы не в семье!")
        return
    
    # Проверяем, есть ли активная сессия сна
    events = supabase.get_last_events(family['id'])
    
    if events['sleep']:
        # Завершаем сон
        result = supabase.end_sleep(family['id'], user_id,
                                   get_user_role(user_id, family['id']),
                                   get_user_name(user_id, family['id']))
        
        if result:
            current_time = get_thai_time().strftime("%H:%M")
            await event.answer(f"✅ Сон завершен в {current_time}")
            message = "😴 Сон завершен!\n\n"
        else:
            await event.answer("❌ Ошибка завершения сна!")
            return
    else:
        # Начинаем сон
        result = supabase.start_sleep(family['id'], user_id,
                                     get_user_role(user_id, family['id']),
                                     get_user_name(user_id, family['id']))
        
        if result:
            current_time = get_thai_time().strftime("%H:%M")
            await event.answer(f"✅ Сон начат в {current_time}")
            message = "😴 Сон начат!\n\n"
        else:
            await event.answer("❌ Ошибка начала сна!")
            return
    
    # Показываем последние события
    events = supabase.get_last_events(family['id'])
    message += "📊 Последние события:\n"
    
    if events['feeding']:
        message += f"🍼 Кормление: {format_time_ago(events['feeding']['timestamp'])}\n"
    if events['diaper']:
        message += f"👶 Подгузник: {format_time_ago(events['diaper']['timestamp'])}\n"
    if events['bath']:
        message += f"🛁 Купание: {format_time_ago(events['bath']['timestamp'])}\n"
    if events['activity']:
        message += f"🎮 Активность: {format_time_ago(events['activity']['timestamp'])}\n"
    if events['sleep']:
        message += f"😴 Сон: {format_time_ago(events['sleep']['start_time'])}\n"
    
    buttons = [
        [Button.inline("🍼 Кормление", b"feeding")],
        [Button.inline("👶 Смена подгузника", b"diaper")],
        [Button.inline("🛁 Купание", b"bath")],
        [Button.inline("🎮 Активность", b"activity")],
        [Button.inline("😴 Сон", b"sleep")],
        [Button.inline("📊 Дашборд", b"dashboard")],
        [Button.inline("ℹ️ Информация", b"info")]
    ]
    
    await event.edit(message, buttons=buttons)

@client.on(events.CallbackQuery(data=b'dashboard'))
async def dashboard_handler(event):
    user_id = event.sender_id
    family = supabase.get_family_by_user(user_id)
    
    if not family:
        await event.answer("❌ Вы не в семье!")
        return
    
    # Получаем URL дашборда из переменных окружения
    dashboard_url = os.getenv('DASHBOARD_URL', 'https://your-dashboard.vercel.app')
    
    message = f"📊 Дашборд семьи '{family['name']}'\n\n"
    message += f"🔗 Откройте дашборд: {dashboard_url}\n\n"
    message += "📱 В дашборде вы можете:\n"
    message += "• 📈 Видеть статистику в реальном времени\n"
    message += "• 📊 Просматривать графики истории\n"
    message += "• 👥 Управлять членами семьи\n"
    message += "• ⚙️ Настраивать напоминания"
    
    buttons = [
        [Button.url("📊 Открыть дашборд", dashboard_url)],
        [Button.inline("🍼 Кормление", b"feeding")],
        [Button.inline("👶 Смена подгузника", b"diaper")],
        [Button.inline("🛁 Купание", b"bath")],
        [Button.inline("🎮 Активность", b"activity")],
        [Button.inline("😴 Сон", b"sleep")],
        [Button.inline("ℹ️ Информация", b"info")]
    ]
    
    await event.edit(message, buttons=buttons)

@client.on(events.CallbackQuery(data=b'info'))
async def info_handler(event):
    message = "ℹ️ Информация о BabyCareBot\n\n"
    message += "🤖 BabyCareBot - это бот для отслеживания ухода за малышом\n\n"
    message += "📱 Возможности:\n"
    message += "• 🍼 Запись кормлений\n"
    message += "• 👶 Отслеживание смен подгузников\n"
    message += "• 🛁 Фиксация купаний\n"
    message += "• 🎮 Запись активностей\n"
    message += "• 😴 Мониторинг сна\n"
    message += "• 📊 Красивый дашборд\n\n"
    message += "👥 Семейная координация:\n"
    message += "• Несколько членов семьи\n"
    message += "• Разные роли (Мама, Папа, Бабушка и т.д.)\n"
    message += "• Синхронизация данных\n\n"
    message += "🔗 Создано с ❤️ для заботливых родителей"
    
    buttons = [
        [Button.inline("🏠 Главное меню", b"main_menu")]
    ]
    
    await event.edit(message, buttons=buttons)

@client.on(events.CallbackQuery(data=b'main_menu'))
async def main_menu_handler(event):
    user_id = event.sender_id
    family = supabase.get_family_by_user(user_id)
    
    if family:
        family_name = family['name']
        role = get_user_role(user_id, family['id'])
        name = get_user_name(user_id, family['id'])
        
        message = f"👋 Привет, {name}!\n\n"
        message += f"🏠 Вы в семье: {family_name}\n"
        message += f"👤 Ваша роль: {role}\n\n"
        message += "📱 Выберите действие:"
        
        buttons = [
            [Button.inline("🍼 Кормление", b"feeding")],
            [Button.inline("👶 Смена подгузника", b"diaper")],
            [Button.inline("🛁 Купание", b"bath")],
            [Button.inline("🎮 Активность", b"activity")],
            [Button.inline("😴 Сон", b"sleep")],
            [Button.inline("📊 Дашборд", b"dashboard")],
            [Button.inline("ℹ️ Информация", b"info")]
        ]
    else:
        user_info = await client.get_entity(user_id)
        user_name = user_info.first_name or "Пользователь"
        
        message = f"👋 Привет, {user_name}!\n\n"
        message += "🏠 Добро пожаловать в BabyCareBot!\n\n"
        message += "📝 Выберите действие:"
        
        buttons = [
            [Button.inline("🏠 Создать семью", b"create_family")],
            [Button.inline("🔗 Присоединиться к семье", b"join_family")],
            [Button.inline("ℹ️ Информация", b"info")]
        ]
    
    await event.edit(message, buttons=buttons)

# Функция для внешнего keep-alive (для Vercel)
def external_keep_alive():
    """Функция для внешнего keep-alive через Vercel"""
    try:
        import urllib.request
        import urllib.error
        
        # Получаем внешний URL из переменных окружения
        external_url = os.getenv('VERCEL_EXTERNAL_URL')
        if external_url:
            # Убираем trailing slash если есть
            if external_url.endswith('/'):
                external_url = external_url[:-1]
            
            # Пингуем внешний URL
            try:
                response = urllib.request.urlopen(f'{external_url}/api/health', timeout=10)
                if response.getcode() == 200:
                    print(f"✅ External keep-alive successful: {time.strftime('%H:%M:%S')}")
                else:
                    print(f"⚠️ External keep-alive returned status: {response.getcode()}")
            except urllib.error.URLError as e:
                print(f"⚠️ External keep-alive failed: {e}")
        else:
            print("⚠️ VERCEL_EXTERNAL_URL not set, skipping external keep-alive")
    except Exception as e:
        print(f"❌ External keep-alive critical error: {e}")

# Планировщик для keep-alive
scheduler = AsyncIOScheduler()

# Добавляем задачу keep-alive каждые 10 минут
scheduler.add_job(external_keep_alive, 'interval', minutes=10)

# Запускаем планировщик
scheduler.start()

print("🚀 BabyCareBot запущен с поддержкой Supabase!")
print("📊 API будет доступен на Vercel")
print("🔗 Дашборд: настройте DASHBOARD_URL в переменных окружения")

# Запускаем бота
client.run_until_disconnected()
