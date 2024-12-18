
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import datetime

from kbds import reply

from db.users_db import Database

from filters.chat_types import ChatTypeFilter, IsHeadman

#обработчик
headman_private_router = Router()
headman_private_router.message.filter(ChatTypeFilter(['private']), IsHeadman())
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

db = Database()

# Состояния
class AddEvent(StatesGroup):
    event = State()
    date = State()
    time = State()
    

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
    await state.set_state(AddEvent.date)

# Обработчик добавления времени
@headman_private_router.message(AddEvent.date, F.text)
async def add_event(message: Message, state : FSMContext):
    await state.update_data(date=message.text)
    await message.answer("Введите время в формате: `ЧЧ:ММ`.\nНапример: `16:30.")
    await state.set_state(AddEvent.time)

# Обработчик ввода даты и события
@headman_private_router.message(AddEvent.time, F.text)
async def process_date(message: Message, state : FSMContext):
    await state.update_data(time=message.text)
    state_info = await state.get_data()  # Получаем все данные из состояния
    date = state_info.get('date')
    time = state_info.get('time')+':00'
    due_data = f'{date} {time}'
    try:
        due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
        event = state_info.get('event')
        await message.answer(
            f"Добавлено событие: {event} на дату {due_data}.",
            reply_markup=HEADMAN_KB  # Меню для добавления событий
        )
        '''due_date.strftime('%Y-%m-%d)'''
    except ValueError:
        await message.answer(
            "Неверный формат! Используйте формат: `ГГГГ-ММ-ДД Событие`.",
            parse_mode="Markdown"
        )
    await state.clear()




