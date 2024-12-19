import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types.input_file import FSInputFile
from aiogram.filters import Command
from aiogram import Router

# Хранилище состояний пользователе
user_states = {}

@router.message(Command("start"))
async def send_welcome(message: Message):
    user_states[message.from_user.id] = "start"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Староста", callback_data="role_starosta")],
        [InlineKeyboardButton(text="Студент", callback_data="role_student")]
    ])

    photo = FSInputFile(PICTURE_START)
    await message.answer_photo(photo, reply_markup=keyboard)

@router.callback_query()
async def handle_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    if callback.data == "role_starosta":
        user_states[user_id] = "awaiting_institute"
        photo = FSInputFile(PICTURE_STAROSTA)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_start")]
        ])
        await callback.message.answer_photo(photo, caption="Токен доступа можно получить у админа @scrooge79", reply_markup=keyboard)

    elif callback.data == "role_student":
        photo = FSInputFile(PICTURE_STUDENT)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_start")]
        ])
        await callback.message.answer_photo(photo, caption="Выбрать доступную Учреждение -> Школу -> Группа", reply_markup=keyboard)

    elif callback.data == "back_to_start":
        user_states[user_id] = "start"
        await send_welcome(callback.message)

    elif callback.data == "back_to_institute":
        user_states[user_id] = "awaiting_institute"
        photo = FSInputFile(PICTURE_INSTITUTE)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_start")]
        ])
        await callback.message.answer_photo(photo, caption="Создать учреждение, например ТПУ", reply_markup=keyboard)

    elif callback.data == "back_to_faculty":
        user_states[user_id] = "awaiting_faculty"
        photo = FSInputFile(PICTURE_FACULTY)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_institute")]
        ])
        await callback.message.answer_photo(photo, caption="Создать факультет, например ИШИТР", reply_markup=keyboard)

@router.message()
async def handle_messages(message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id, "start")

    if state == "awaiting_institute":
        user_states[user_id] = "awaiting_faculty"
        photo = FSInputFile(PICTURE_FACULTY)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_start")]
        ])
        await message.answer_photo(photo, caption="Создать факультет, например ИШИТР", reply_markup=keyboard)

    elif state == "awaiting_faculty":
        user_states[user_id] = "awaiting_group"
        photo = FSInputFile(PICTURE_GROUP)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_faculty")]
        ])
        await message.answer_photo(photo, caption="Создать группу, например 8В32", reply_markup=keyboard)

    elif state == "awaiting_group":
        user_states[user_id] = "completed"
        await message.answer("Спасибо! Все этапы завершены.")

async def main():
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
