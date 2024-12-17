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
headman_private_router = Router()

# Словарь для хранения событий по группам
#group_events = {}
# Словарь для хранения ID пользователей
#users = set()
# Словарь для отслеживания выбранной группы для каждого пользователя
#user_selected_group = {}

# Меню для добавления события
HEADMAN_KB = reply.get_keyboard(
        '➕ Добавить дату',
        '📅 Просмотр всех дат',
        '⏳ Ближайшая дата',
        placeholder='выберите действие',
        sizes=(2,),
)


# Состояния
class AddEvent(StatesGroup):
    event = State()
    dateTime = State()
    

# Обработчик добавления события
@headman_private_router.message(StateFilter(None), lambda message: message.text == "➕ Добавить дату")
async def add_event(message: Message, state : FSMContext):
    await message.answer("Введите событие.\nК примеру: рт по физике")
    await state.set_state(AddEvent.event)

# Обработчик добавления даты
@headman_private_router.message(AddEvent.event, F.text)
async def add_event(message: Message, state : FSMContext):
    await state.update_data(event=message.text)
    await message.answer("Введите дату в формате: `ГГГГ-ММ-ДД`.\nНапример: `2024-12-25.")
    await state.set_state(AddEvent.dateTime)

# Обработчик ввода даты и события
@headman_private_router.message(AddEvent.dateTime, F.text)
async def process_date(message: Message, state : FSMContext):
    try:
        date = message.text
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        await state.update_data(dateTime=date)
        await message.answer(
            f"Добавлено событие: {state.get_data(AddEvent.event)} на дату {date.strftime('%Y-%m-%d')}'.",
            reply_markup=HEADMAN_KB  # Меню для добавления событий
        )
    except ValueError:
        await message.answer(
            "Неверный формат! Используйте формат: `ГГГГ-ММ-ДД Событие`.",
            parse_mode="Markdown"
        )
    await state.clear()

# Обработчик просмотра всех дат
@headman_private_router.message(lambda message: message.text == "📅 Просмотр всех дат")
async def view_all_dates(message: Message, bot : Bot):
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
@headman_private_router.message(lambda message: message.text == "⏳ Ближайшая дата")
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
@headman_private_router.message(lambda message: message.text == "🚪 Выйти из группы")
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

