from aiogram.filters import Filter
from aiogram import Bot, types

from db.users_db import Database

class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types
    

class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        return str(message.from_user.id) in bot.admin_list
    
class IsHeadman(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message) -> bool:
        db = Database()
        headman = await db.get_user(str(message.from_user.id))
        headman = headman[3]
        return headman == 'headman'