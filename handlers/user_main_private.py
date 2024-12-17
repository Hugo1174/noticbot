import asyncio
from aiogram import Bot, F, Router, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

import datetime

from kbds import reply

from db.users_db import Database

#обработчик
main_private_router = Router()

# Словарь для хранения событий по группам
#group_events = {}
# Словарь для хранения ID пользователей
#users = set()
# Словарь для отслеживания выбранной группы для каждого пользователя
#user_selected_group = {}

# Меню для добавления события
USER_KB = reply.get_keyboard(
        '📅 Просмотр всех дат',
        '⏳ Ближайшая дата',
        placeholder='выберите действие',
        sizes=(2,),
)


# Состояния
class GroupStates(StatesGroup):
    choosing_group = State()
    adding_event = State()


# Обработчик добавления события
@main_private_router.message(lambda message: message.text == "➕ Добавить дату")
async def add_event(message: types.Message):
    user_id = message.from_user.id
    group_name = user_selected_group.get(user_id)

    if not group_name:
        await message.answer("Сначала выберите группу через меню '📚 Выбрать группу'.", reply_markup=main_menu)
        return

    await message.answer("Введите дату и событие в формате: `ГГГГ-ММ-ДД Событие`.\nНапример: `2024-12-25 Рождество`.")

# Обработчик ввода даты и события
@main_private_router.message(lambda message: not message.text.startswith("➕") and 
                            not message.text.startswith("📚") and 
                            not message.text.startswith("📅") and 
                            not message.text.startswith("⏳") and 
                            not message.text.startswith("🚪"))
async def process_date(message: types.Message):
    user_id = message.from_user.id
    group_name = user_selected_group.get(user_id)

    if not group_name:
        await message.answer("Сначала выберите группу через меню '📚 Выбрать группу'.", reply_markup=main_menu)
        return

    try:
        date, event = message.text.split(" ", 1)
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        group_events[group_name][date] = event
        await message.answer(
            f"Добавлено событие: {event} на дату {date.strftime('%Y-%m-%d')} в группе '{group_name}'.",
            reply_markup=add_event_menu  # Меню для добавления событий
        )
    except ValueError:
        await message.answer(
            "Неверный формат! Используйте формат: `ГГГГ-ММ-ДД Событие`.",
            parse_mode="Markdown"
        )

# Обработчик просмотра всех дат
@main_private_router.message(lambda message: message.text == "📅 Просмотр всех дат")
async def view_all_dates(message: types.Message):
    user_id = message.from_user.id
    group_name = user_selected_group.get(user_id)
    if not group_name:
        await message.answer("Сначала выберите группу через меню '📚 Выбрать группу'.", reply_markup=main_menu)
        return

    events = group_events.get(group_name, {})
    if not events:
        await message.answer(f"В группе '{group_name}' событий пока нет.", reply_markup=add_event_menu)
    else:
        events_list = "\n".join(
            [f"{date.strftime('%Y-%m-%d')}: {event}" for date, event in sorted(events.items())]
        )
        await message.answer(f"Все события в группе '{group_name}':\n\n{events_list}", reply_markup=add_event_menu)

# Обработчик ближайшей даты
@main_private_router.message(lambda message: message.text == "⏳ Ближайшая дата")
async def nearest_date(message: types.Message):
    user_id = message.from_user.id
    group_name = user_selected_group.get(user_id)
    if not group_name:
        await message.answer("Сначала выберите группу через меню '📚 Выбрать группу'.", reply_markup=main_menu)
        return

    events = group_events.get(group_name, {})
    if not events:
        await message.answer(f"В группе '{group_name}' событий пока нет.", reply_markup=add_event_menu)
    else:
        today = datetime.date.today()
        nearest = min(
            (date for date in events if date >= today),
            default=None,
            key=lambda d: (d - today).days
        )
        if nearest:
            await message.answer(
                f"Ближайшая дата в группе '{group_name}': {nearest.strftime('%Y-%m-%d')}\nСобытие: {events[nearest]}",
                reply_markup=add_event_menu
            )
        else:
            await message.answer(f"Ближайших дат в группе '{group_name}' нет.", reply_markup=add_event_menu)

# Обработчик выхода из группы
@main_private_router.message(lambda message: message.text == "🚪 Выйти из группы")
async def leave_group(message: types.Message):
    user_id = message.from_user.id
    group_name = user_selected_group.get(user_id)
    if not group_name:
        await message.answer("Вы не состоите в какой-либо группе.", reply_markup=main_menu)
        return

    # Удаляем группу из выбранных
    del user_selected_group[user_id]
    await message.answer(
        f"Вы вышли из группы '{group_name}'. Вы можете выбрать другую группу или создать новую.",
        reply_markup=main_menu
    )

# Функция для отправки уведомлений
async def send_notifications():
    while True:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        for group_name, events in group_events.items():
            for date, event in events.items():
                if date == tomorrow:
                    for user_id in users:
                        try:
                            await bot.send_message(
                                user_id, f"Напоминание: Завтра ({date.strftime('%Y-%m-%d')}) событие: {event} в группе '{group_name}'"
                            )
                        except Exception as e:
                            print(f"Ошибка отправки уведомления: {e}")
        await asyncio.sleep(3600)

