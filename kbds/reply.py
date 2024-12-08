import asyncio

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


'''
# с помощью request_contact и других можно получиль контакт локацию ...

# первый метод
# записываем список списка кнопок
start_kbd = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="О нас :smile:"),
        ],
        [
            KeyboardButton(text="Посмотреть"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder='Что вас интерисует?'
)
del_kbd = ReplyKeyboardRemove()
# второй метод
start_kbd2 = ReplyKeyboardBuilder()
start_kbd2.add(
    KeyboardButton(text="О нас"),
    KeyboardButton(text="Посмотреть"),
)
# указываем размер
start_kbd2.adjust(1, 2)


# добавление новых кнопок для второго метода
start_kbd3 = ReplyKeyboardBuilder()
start_kbd3.attach(start_kbd2)
start_kbd3.row(KeyboardButton(text="оставь отзыв"),)
'''

# универсальная ф-я для формирования кнопок
def get_keyboard(
    *btns: str,
    placeholder: str = None,
    sizes: tuple[int] = (2, ),
):
    kbd = ReplyKeyboardBuilder()
    for index, text in enumerate(btns, start=0):
        kbd.add(KeyboardButton(text=text))
    return kbd.adjust(*sizes).as_markup(resize_keyboard=True, input_field_placeholder=placeholder)