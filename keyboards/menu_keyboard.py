from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)


menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📅 Получить расписание')],
        [KeyboardButton(text='🔄 Сменить группу'),
         KeyboardButton(text='ℹ️ Моя группа')],
        [KeyboardButton(text='🤖 Информация о боте')],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню"
)


format_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🍎 На неделю')],
        [KeyboardButton(text='👇 На сегодня'),
         KeyboardButton(text='👉 На завтра')],
        [KeyboardButton(text='🍏 На следующую неделю')],
        [KeyboardButton(text='🔄 Сменить группу')],
        [KeyboardButton(text='◀️ Назад')],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите формат расписания"
)

confirmation_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='✅ Да, хочу', callback_data='yes_change')],
        [InlineKeyboardButton(text='❌ Нет, не хочу',
                              callback_data='no_change')],
    ]
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='❌ Отмена')]],
    resize_keyboard=True,
    input_field_placeholder="Отмените, если передумали"
)
