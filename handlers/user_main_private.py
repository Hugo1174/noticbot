import asyncio
from aiogram import Bot, Router
from aiogram.types import Message

import datetime

from kbds import reply

from db.users_db import Database


#обработчик
user_private_router = Router()


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
    group_id = await db.get_user(str(user_id))
    group_id = group_id[4]
    group_name = await db.return_group(int(group_id))
    group_name = group_name[2]
    events = await db.get_asignment(int(group_id))
    if not events:
        await message.answer(f"В группе '{group_name}' событий пока нет.", reply_markup=USER_KB)
    else:
        response = "События:\n"
        for event in events:
            response += ( f"Название: {event['title']},\n"
                          f"Срок: {event['due_date']},\n"
                          f"Описание: {event['description']}\n")
        await message.answer(response, reply_markup=USER_KB)

# Обработчик ближайшей даты
@user_private_router.message(lambda message: message.text == "⏳ Ближайшая дата")
async def nearest_date(message: Message):
    user_id = message.from_user.id
    group_id = await db.get_user(str(user_id))
    group_id = group_id[4]
    group_name = await db.return_group(int(group_id))
    group_name = group_name[2]
    events = await db.get_asignment(int(group_id))

    if not events:
        await message.answer(f"В группе '{group_name}' событий пока нет.", reply_markup=USER_KB)
    else:
        today = datetime.today().date()  # Получаем текущую дату
        # Находим ближайшую дату
        nearest_event = min(
            (event for event in events if event['due_date'].date() >= today),
            default=None,
            key=lambda e: (e['due_date'].date() - today).days
        )

        if nearest_event:
            await message.answer(
                f"Ближайшая дата в группе: {nearest_event['due_date'].strftime('%Y-%m-%d')}\n"
                f"Событие: {nearest_event['title']}\n"
                f"Описание: {nearest_event['description']}",
                reply_markup=USER_KB
            )
        else:
            await message.answer(f"Ближайших дат в группе '{group_name}' нет.", reply_markup=USER_KB)


# Функция для отправки уведомлений
async def send_notifications(bot: Bot):
    while True:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        events = await db.get_events_by_date(tomorrow)
        for event in events:
            if event['due_time'].date() == tomorrow: 
                users = await db.search_user_by_group(int(event['group_id']))
                for user in users:
                    try:
                        await bot.send_message(
                            user[0], \
                                f"{user[2]} напоминание: Завтра ({event['due_time']}) событие: {event['title']}'"
                        )
                    except Exception as e:
                        print(f"Ошибка отправки уведомления: {e}")
        await asyncio.sleep(3600)