from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_keyboard(
        *buttons:str,#что должно быть в кнопках,списком str
        placeholder: str = None,# для поля ввода текста
        sizes: tuple[int] = (2,)
):
    keyboard = ReplyKeyboardBuilder()
    for index, text in enumerate(buttons, start=0):
        keyboard.add(KeyboardButton(text=text))
    return keyboard.adjust(*sizes).as_markup(resize_keyboard=True, input_field_placeholder=placeholder)
    


