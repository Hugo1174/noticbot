import asyncio
import os # для работы с операционкой


from aiogram import Bot, Dispatcher
from aiogram.types import BotCommandScopeAllPrivateChats

# для работы с окружением
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from handlers.registration_private import registration_private_router
from handlers.admin_private import admin_private_router
from handlers.headman_main_private import headman_private_router
from handlers.user_main_private import user_private_router, send_notifications
from common.bot_cmds_list import private

from db.users_db import Database




BOT_TOKEN = os.getenv('TOKEN')# токен бота

# создаём бота и диспетчера
bot = Bot(token = BOT_TOKEN)
#bot.admin_list = ['0']
bot.admin_list = os.getenv('ADMIN_LIST').split(',')

dp = Dispatcher()

database = Database()

dp.include_router(registration_private_router)
dp.include_router(admin_private_router)
dp.include_router(headman_private_router)
dp.include_router(user_private_router)

# Основная функция для запуска бота
async def main():
    try:
        await database.create_database()
        asyncio.create_task(send_notifications(bot))
        # удалить меню
        #await bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
        # создать меню
        await bot.set_my_commands(commands=private, scope=BotCommandScopeAllPrivateChats())
        # Запуск бота с использованием нового метода
        await dp.start_polling(bot)
    finally:
        # Закрытие соединения при завершении работы бота
        #connection.close()
        print("Соединение с базой данных закрыто.")

if __name__ == '__main__':
    asyncio.run(main())