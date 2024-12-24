import asyncio
import shutil
import os

from aiogram import Bot, Router
from aiogram.types import Message

import datetime

from kbds import reply

from db.users_db import Database


#обработчик
user_private_router = Router()

# Меню для добавления события
HEADMAN_KB = reply.get_keyboard(
        '➕ Добавить дату',
        '📅 Просмотр всех дат',
        '⏳ Ближайшая дата',
        placeholder='выберите действие',
        sizes=(1,3),
)

# Меню для добавления события
USER_KB = reply.get_keyboard(
        '📅 Просмотр всех дат',
        '⏳ Ближайшая дата',
        placeholder='выберите действие',
        sizes=(1,2),
)

db = Database()

# Обработчик просмотра всех дат
@user_private_router.message(lambda message: message.text == "📅 Просмотр всех дат")
async def view_all_dates(message: Message):
    user_id = message.from_user.id
    user_data = await db.get_user(str(user_id))
    role = user_data[3]
    group_id = user_data[4]
    group_name = await db.return_group(int(group_id))
    group_name = group_name[2]
    events = await db.get_asignment(int(group_id))
    print(group_id, group_name, events)
    response = ''
    if not events:
        response = f"В группе '{group_name}' событий пока нет."
    else:
        response = "События:\n"
        for event in events:
            response += ( f"Название: {event['title']},\n"
                          f"Срок: {event['due_date']},\n"
                          f"Описание: {event['description']}\n")
    if role == 'student':
        await message.answer(response, reply_markup=USER_KB)
    else:
        await message.answer(response, reply_markup=HEADMAN_KB)    

# Обработчик ближайшей даты
@user_private_router.message(lambda message: message.text == "⏳ Ближайшая дата")
async def nearest_date(message: Message):
    user_id = message.from_user.id
    user_data = await db.get_user(str(user_id))
    role = user_data[3]
    group_id = user_data[4]
    group_name = await db.return_group(int(group_id))
    group_name = group_name[2]

    # Получаем события из базы данных
    events = await db.get_asignment(int(group_id))

    print(group_id, group_name, events)
    
    response = ''
    if not events:
        response = f"В группе '{group_name}' событий пока нет."
    else:
        today = datetime.datetime.today().date()  # Получаем текущую дату
        print(today)

        # Находим ближайшую дату
        nearest_event = None
        min_days_diff = float('inf')  # Инициализируем с большим значением

        for event in events:
            due_date_str = event['due_date']  # Get due date as a string
            due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d %H:%M:%S').date()
            
            if due_date >= today:
                days_diff = (due_date - today).days
                if days_diff < min_days_diff:
                    min_days_diff = days_diff
                    nearest_event = event

        if nearest_event:
            response = f"Ближайшая дата в группе: {nearest_event['due_date']}\n"\
                       f"Событие: {nearest_event['title']}\n"\
                       f"Описание: {nearest_event['description']}"
        else:
            response = f"Ближайших дат в группе '{group_name}' нет."

    if role == 'student':
        await message.answer(response, reply_markup=USER_KB)
    else:
        await message.answer(response, reply_markup=HEADMAN_KB)

source_file = '../db/bot_db.db'  # Путь к исходному файлу
destination_directory = '~noticbot/logs/'
if not os.path.exists(destination_directory):
    os.makedirs(destination_directory)

# Функция для отправки уведомлений
async def send_notifications(bot: Bot):
    i = 1
    message_time = datetime.time(12, 0)  # 12:00
    while True:
        # Получаем текущее время
        now = datetime.datetime.now().time()
        if now.hour == message_time.hour and now.minute == message_time.minute:
            print(f"Сообщение отправлено в {now}")
            # Проверка существования исходного файла перед копированием
            if os.path.exists(source_file):
                try:
                    # Копирование файла
                    shutil.copy(source_file, os.path.join(destination_directory, f'bot_db{i}.db'))
                    print(f'Файл {source_file} успешно скопирован в {destination_directory}')
                except Exception as e:
                    print(f'Ошибка при копировании файла: {e}')
            else:
                print(f'Исходный файл не найден: {source_file}')

            # Обновление счетчика
            i += 1 if i < 11 else -10  # Сброс счетчика после 10
        else:
            await asyncio.sleep(1)
            continue

        print(now)

        today = datetime.datetime.today().date()
        tomorrow = today + datetime.timedelta(days=1)

        # Получаем события, запланированные на завтра
        events = await db.get_events_by_date(tomorrow)

        for event in events:
            # Предполагается, что due_time хранится как строка в формате 'YYYY-MM-DD HH:MM:SS'
            due_time = datetime.datetime.strptime(event['due_date'], '%Y-%m-%d %H:%M:%S').date()

            if due_time == tomorrow: 
                # Получаем пользователей, связанных с группой события
                users = await db.search_user_by_group(int(event['group_id']))
                
                for user in users:
                    try:
                        await bot.send_message(
                            user['telegram_id'], 
                            f"Напоминание: Завтра ({event['due_date']}) событие: {event['title']}"
                        )
                    except Exception as e:
                        print(f"Ошибка отправки уведомления пользователю {user['telegram_id']}: {e}")
        
        await asyncio.sleep(86000)