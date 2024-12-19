import secrets

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from filters.chat_types import ChatTypeFilter, IsAdmin

#from db.users_db import cursor, connection
#from test_notice_bot import bot

from kbds import reply

from db.users_db import Database

database = Database()

#обработчик
admin_private_router = Router()
admin_private_router.message.filter(ChatTypeFilter(['private']), IsAdmin())

ADMIN_KB = reply.get_keyboard(
        'группы',
        'аннигиляция',
        'активность',
        'токен',
        placeholder='выберите действие',
        sizes=(2,2),
)
'''
Разработать функции доступные только для админа
группы
аннигиляция
активность
'''

class Delete(StatesGroup):
    faculty = State()
    group = State()

@admin_private_router.message(StateFilter(None), F.text == 'аннигиляция')
async def process_delete_group(message : Message, state : FSMContext):
    await message.answer('Введите факультет', reply_markup=None)
    await state.set_state(Delete.faculty)

@admin_private_router.message(Delete.faculty, F.text)
async def process_delete_group(message : Message, state : FSMContext):
    await state.update_data(faculty = message.text.casefold())
    await message.answer('Введите группу')
    await state.set_state(Delete.group)

@admin_private_router.message(Delete.group, F.text)
async def process_search_group(message : Message, state : FSMContext):
    await state.update_data(group = message.text.casefold())
    state_data = await state.get_data()
    faculty = state_data.get('faculty')
    group =  state_data.get('group')
    group = await database.search_group(faculty, group)
    if group != None:
        await database.delete_group(faculty, group)
        await message.answer('Группа успешно удалена', reply_markup=ADMIN_KB)
    else:
        await message.answer('Звиняй, не нашёл группу', reply_markup=ADMIN_KB)
    await state.clear()

    
@admin_private_router.message(F.text == 'группы')
async def process_check_group(message : Message):
    groups = await database.return_groups()
    if groups != None:
        line = ''
        for group in groups:
            line += ('/n' + group[1] + group[2])
        await message.answer(
            f'Вот список все групп:{line}', reply_markup=ADMIN_KB
        )
    else:
        await message.answer('Групп нет', reply_markup=ADMIN_KB)   



@admin_private_router.message(F.text == 'активность')
async def process_delete_group(message : Message):
    active = await database.number()
    await message.answer(f'Всего в боте:\n'
                         f'\tПользователей - {active[0]}\n'
                         f'\tГрупп - {active[1]}', reply_markup=ADMIN_KB)


@admin_private_router.message(F.text == 'токен')
async def process_generate_token(message : Message):
    token = secrets.token_urlsafe(16)
    await message.answer('Вот токен для старосты', reply_markup=ADMIN_KB)
    await message.answer(token)
    await database.add_token(token) 