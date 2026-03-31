from aiogram import Router, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from keyboards.menu_keyboard import menu_keyboard

router = Router()


@router.message(Command("start"))
async def start_message(message: types.Message):

    text = (
        f"<b>Добро пожаловать🎉,</b> {message.from_user.username}<b>!</b>\n\n"
        "С помощью этого бота вы можете смотреть учебное расписание ИрНИТУ📚\n"
        "Введите точное название группы и смотрите расписание!📱\n"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=menu_keyboard)


@router.message(Command("bot_info"))
@router.message(F.text == "🤖 Информация о боте")
async def get_bot_info(message: types.Message):
    text = (
        "Этот Бот🤖 предоставляет расписание согласно введённой учебной группе🤓\n\n"
        "<b>Внимание!</b> В функционал бота не входит:\n"
        "- Просмотр расписания преподавателей👨‍🏫\n"
        "- Просмотр расписания занятий в кабинетах#️⃣\n\n"
        "Если у Вас возникают сомнения🤔, то вы всегда можете посмотреть расписание на <b>официальном сайте</b>:\n"
        "https://www.istu.edu/schedule/"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=menu_keyboard)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("Используйте кнопки меню!", reply_markup=menu_keyboard)
