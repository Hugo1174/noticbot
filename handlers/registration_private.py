from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

#from db.users_db import cursor, connection
#from test_notice_bot import bot

from kbds import reply

from db.users_db import Database

database = Database()

#обработчик
registration_private_router = Router()

ADMIN_KB = reply.get_keyboard(
        'группы',
        'аннигиляция',
        'активность',
        'токен',
        placeholder='выберите действие',
        sizes=(2,2),
)
# Меню для добавления события
HEADMAN_KB = reply.get_keyboard(
        '➕ Добавить дату',
        '📅 Просмотр всех дат',
        '⏳ Ближайшая дата',
        placeholder='выберите действие',
        sizes=(1,3),
)
USER_KB = reply.get_keyboard\
                (
                    '📅 Просмотр всех дат',
                    '⏳ Ближайшая дата',
                    placeholder="список",
                    sizes=(1,2)
                )

class Registration(StatesGroup):
    role = State()
    faculty = State()
    group = State()
    token = State()

@registration_private_router.message(StateFilter(None), lambda msg: msg.text == '/start')
async def process_start_cmd(message : Message, bot : Bot, state : FSMContext):
    user_id =  message.from_user.id
    username = message.from_user.first_name
    print(user_id, username)
    # ищем юзера и запоминаем
    # подключаем базу данных
    db_user = await database.get_user(user_id)
    print(db_user)
    # если юзера нет
    if db_user == None:
        # проверяем на админа
        if str(user_id) in bot.admin_list:
            # добавляем нового админа
            await database.add_user(user_id, username, 'admin')
            await message.answer\
            (
                f'Привет!\nРады приветствовать нового админа.\n'
                f'Доступные команды можешь посмотреть ниже.',
                reply_markup=ADMIN_KB
            )
        else: # обычный юзер переходит на следующий этап
            await message.answer\
            (
                f'Привет {username}!. Рады приветствовать в боте.\n'
                'Чтобы продолжить регистрацию, укажи введи свою роль:\n'
                '\t/student\n\t/headman',
                reply_markup=None
            )
            await state.set_state(Registration.role)
    else:
        # проверяем, админ ли это и говорим больше не писать
        if db_user[3] != 'admin':
            # не админ
            await message.answer\
            (
                f'{username}, ты уже общаещься с ботом.\n'
                'Постарайся больше не вводить эту команду.\n'
                'Если что-то непонятно, вводи /help',
                reply_markup=USER_KB
            )
        elif (db_user[3] == 'admin') and (str(user_id) not in bot.admin_list):
            await message.answer('Звиняй, ты был админом, но больше ты не нужен',
                                 reply_markup=None)
            await database.delete_user(db_user[1])
        else:
            # админ
            await message.answer\
            (
                f'{username}, ты админ.\n'
                'Не испытывай терпение бота.\n'
                'Можешь лишиться своих возможностей!!!',
                reply_markup=ADMIN_KB  
            )
        

    ''' для студента '''
# выбор группы для студента
@registration_private_router.message(Registration.role, Command("student"))
async def process_student_role(message : Message, state : FSMContext):
    await state.update_data(role="student")
    await message.answer\
        (
            'Введите свой факультет'
        )
    await state.set_state(Registration.faculty)

@registration_private_router.message(Registration.faculty, F.text)
async def process_student_role(message : Message, state : FSMContext):
    await state.update_data(faculty=message.text.casefold())
    await message.answer\
        (
            'Введите свою группу'
        )
    await state.set_state(Registration.group)
    
# поиск группы студента
@registration_private_router.message(Registration.group, F.text)
async def process_add_group(message : Message, state : FSMContext):
    # ищем группу в бд
    user_group = message.text.casefold()

    await state.update_data(group=user_group)

    state_data = await state.get_data()
    faculty = state_data.get('faculty')
    group = await database.search_group(faculty, user_group)
    role = state_data.get('role')
    print(user_group,faculty, group, role)
    if not group:
        # если нашли уведомляем пользователя и добавляем в FSM
        if role == 'headman':
            await message.answer\
                (
                    f'Отлично!\n{message.from_user.username}, я создал группу!'
                )
            # добавляем юзера
            await database.add_user(str(message.from_user.id), message.from_user.username, role)
            headman_id = await database.get_user(str(message.from_user.id))
            headman_id = headman_id[0]
            await database.add_group(faculty, user_group, headman_id)
            group_id = await database.search_group(faculty, user_group)
            group_id = group_id[0]
            await database.add_group_id_to_headman(headman_id, group_id)
            await message.answer\
                (
                    'Теперь тебе доступны возможности бота.\n'
                    'С помощью кнопок ниже можешь творить',
                    reply_markup=HEADMAN_KB
                )
        else: 
            await message.answer\
            (
                'Звиняй, что-то не так.\n'
                'Возможно староста ещё не создал группу. Напиши ему!'
            )
        await state.clear()
    
    # проверка на старосту
    if group:
        group_id = group[0]
        # если нашли уведомляем пользователя и добавляем в FSM
        if role == 'student':
            await message.answer\
                (
                    f'Отлично!\n{message.from_user.username}, я нашёл твою группу!'
                )
            # добавляем юзера
            await database.add_user(str(message.from_user.id), message.from_user.username, role, group_id)

            await message.answer\
                (
                    'Теперь тебе доступны возможности бота.\n'
                    'С помощью кнопок ниже можешь посмотреть, к чему надо готовиться',
                    reply_markup=USER_KB
                )
        else: 
            await message.answer\
            (
                'Звиняй, что-то не так.\n'
                'Возможно где-то ошибка!\n'
                'Начать заново - /start'
            )
        await state.clear()


    ''' для старосты '''
#перекидываем на админа, чтобы тот выдал токен
@registration_private_router.message(Registration.role, Command('headman'))
async def process_get_token(message : Message, state : FSMContext):
    await state.update_data(role = 'headman')
    await message.answer\
    (
        f'{message.from_user.username}, для продолжения регистрации обратись к админу @scrooge79\n'
        'Попроси у него токен и введи его сюда.'
    )
    await state.set_state(Registration.token)


@registration_private_router.message(Registration.token, F.text)
async def process_headman_faculty(message : Message, state : FSMContext):
    await state.update_data(token=message.text)
    # ищем токен
    token = await database.search_token(message.text)
    print(token)
    # если есть записываем старосту
    if token:
        if not token[2]:
            await database.use_token(token[1])
            await message.answer\
            (
                'Введите свой факультет.'
            )
            await state.set_state(Registration.faculty)
            return
        else:
            await message.answer('Этот токен используется, введите новый')
    else:
        await message.answer('Этого токена нет, введите новый')
    await state.set_state(Registration.token)

@registration_private_router.message(Registration.group, F.text)
async def process_group_registration(message : Message, state : FSMContext):    
    # ищем группу в бд
    user_group = message.text.casefold()

    await state.set_state(group=user_group)

    state_data = await state.get_data()
    faculty = state_data.get('faculty')
    group = await database.search_group(faculty, user_group)
    role = state_data.get('role')
    print(faculty, user_group, group, role)
    # проверка на старосту
    if role == 'headman':
        # если нашли уведомляем пользователя и добавляем в FSM
        if not group:
            await message.answer\
                (
                    f'Отлично!\n{message.from_user.username}, я создал группу!'
                )
            # добавляем юзера
            await database.add_user(str(message.from_user.id), message.from_user.username, role, user_group)
            headman_id = await database.get_user(str(message.from_user.id))['id']
            await database.add_group(faculty, user_group, headman_id)
            await message.answer\
                (
                    'Теперь тебе доступны возможности бота.\n'
                    'С помощью кнопок ниже можешь творить',
                    reply_markup=HEADMAN_KB
                )
            
        else: 
            await message.answer\
            (
                'Звиняй, что-то не так.\n'
                'Возможно где-то ошибка!'
            )
    else:
        if group:
            await message.answer\
            (
                'Звиняй, но такая группа уже есть.\n'
            )
            return
            

    await state.clear()








'''
# хэндлер команды /start
@registration_private_router.message(lambda msg: msg.text == '/start')
async def process_start_cmd(message : Message, bot : Bot):
    user_id = message.from_user.id
    username = message.from_user.first_name
    # ищем юзера и запоминаем
    # подключаем базу данных
    db_user = await database.get_user(user_id)
    # если юзер нет
    if not db_user:
        if str(user_id) not in bot.admin_list:
            await message.answer\
            (
                f'Привет!\nРады приветствовать в нашем боте.\n'
                f'Чтобы узнать, как пользовиться ботом, '
                f'вводи команду /help',
                reply_markup=reply.get_keyboard\
                (
                    "Задачи",
                    "задача",
                    placeholder="список",
                    sizes=(1, 2)
                )   
            )
            # добавляем нового юзера
            await database.add_user(user_id, username, 'student')
            print(db_user)
            
        else:
            # добавляем нового админа
            await database.add_user(user_id, username, 'admin')
            await message.answer\
            (
                f'Привет!\nРады приветствовать нового админа.\n'
                f'Доступные команды можешь посмотреть в кнопках',
                reply_markup=reply.get_keyboard\
                (
                    "анигиляция",
                    "группы",
                    "активность",
                    placeholder="команды",
                    sizes=(2, )
                )   
            ) 
    else: # добавили новую кнопку в меню
        if str(user_id) not in bot.admin_list:
            await message.answer\
            (
                f'{username}, ты уже общаещься с ботом.\n'
                'Постарайся больше не вводить эту команду',
                reply_markup=reply.get_keyboard\
                (
                    "Задачи",
                    "задача",
                    placeholder="список",
                    sizes=(2,)
                ) 
            )
        else:
            await message.answer\
            (
                f'{username}, ты админ.\n'
                'Ныsе испытывай терпение бота.\n'
                'Можешь лишиться своих возможностей!!!',
                reply_markup=reply.get_keyboard\
                (
                    "анигиляция",
                    "группы",
                    "активность",
                    placeholder="команды",
                    sizes=(2, )
                )  
            )

'''