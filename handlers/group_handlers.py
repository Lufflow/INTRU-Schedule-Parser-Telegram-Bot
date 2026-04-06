# handlers/group_handlers.py

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.menu_keyboard import menu_keyboard, format_keyboard, confirmation_keyboard
from parser_modules import preparing_handler as ph
from parser_modules import time_handlers as th
from parser_modules.auto_update import groups_dict
from handlers import schedule_handlers as sh
import logging
import re

logger = logging.getLogger(__name__)

router = Router()


class GroupStates(StatesGroup):
    waiting_for_group = State()
    waiting_for_message = State()


def get_groups_dict_safe():
    if not groups_dict:
        return {
            "ИБб-24-1": 'https://www.istu.edu/schedule/?group=474032',
            "ЭВМб-24-1": 'https://www.istu.edu/schedule/?group=474421',
            "РДб-24-1": 'https://www.istu.edu/schedule/?group=474256'
        }
    return groups_dict


@router.message(Command("get_schedule"))
@router.message(F.text == "📅 Получить расписание")
async def get_schedule(message: types.Message, state: FSMContext, db=None):
    user_id = message.from_user.id
    db = message.bot.db
    group = db.get_user_group(user_id)

    if group:
        await show_format_choice(message, group)
    else:
        text = (
            "📝 У вас еще не установлена группа.\n"
            "Введите <b>точное</b> название учебной группы:"
        )
        await state.set_state(GroupStates.waiting_for_group)
        await message.answer(text, parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())


async def show_format_choice(message: types.Message, group: str):
    text = (
        f"Ваша группа📝: <code>{group}</code>\n"
        "Выберите <b>формат</b> вывода расписания:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=format_keyboard)


@router.message(GroupStates.waiting_for_group)
async def save_group(message: types.Message, state: FSMContext, db=None):
    user_id = message.from_user.id
    group_name = message.text.strip()

    logger.info(f"👨‍🎓 Сохранение группы {group_name} пользователя {user_id}")

    db = message.bot.db
    current_dict = get_groups_dict_safe()

    if group_name in current_dict:
        success = db.save_user_group(user_id, group_name)

        if success:
            await state.clear()
            await message.answer(
                f"✅ Группа <code>{group_name}</code> сохранена!",
                reply_markup=menu_keyboard, parse_mode='HTML'
            )
            await show_format_choice(message, group_name)
        else:
            await message.answer("❌ Ошибка сохранения. Попробуйте позже.")
    else:
        await message.answer("❌ Учебной группы с таким названием не существует. \nПроверьте правильность написания и попробуйте снова:")


@router.message(Command("mygroup"))
@router.message(F.text == "ℹ️ Моя группа")
async def show_my_group(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    db = message.bot.db
    group = db.get_user_group(user_id)

    if group:
        await message.answer(f"📚 Ваша текущая группа: <code>{group}</code>", parse_mode="HTML")
    else:
        await message.answer("❌ Группа не установлена. Используйте кнопку <code>📅 Получить расписание</code>")


@router.message(Command("setgroup"))
@router.message(F.text == "🔄 Сменить группу")
async def change_group_confirmation(message: types.Message, state: FSMContext):
    db = message.bot.db
    current_group = db.get_user_group(message.from_user.id)

    if current_group and current_group is not None:
        await message.answer(
            f"Ваша текущая группа: <code>{current_group}</code>\n\n"
            "Вы точно хотите сменить группу?",
            parse_mode="HTML",
            reply_markup=confirmation_keyboard
        )
    else:
        await state.set_state(GroupStates.waiting_for_group)
        await message.answer(
            "Введите <b>точное</b> название учебной группы:",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )


@router.callback_query(F.data == 'yes_change')
async def change_group(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    await state.set_state(GroupStates.waiting_for_group)

    await call.message.answer(
        "Введите <b>точное</b> название учебной группы:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )


@router.callback_query(F.data == 'no_change')
async def no_change_group(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    db = call.bot.db
    group = db.get_user_group(user_id)

    await call.answer()
    await state.clear()
    await call.message.delete()
    text = (
        f"Ваша группа📝: <code>{group}</code>\n"
        "Выберите <b>формат</b> вывода расписания:"
    )
    await call.message.answer(
        text=text,
        reply_markup=format_keyboard, parse_mode='HTML'
    )


@router.message(F.text == "🍎 На неделю")
@router.message(F.text == "🍏 На следующую неделю")
async def show_week_schedule(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    db = message.bot.db
    group = db.get_user_group(user_id)

    if not group:
        text = (
            "📝 У вас еще не установлена группа.\n"
            "Введите <b>точное</b> название учебной группы:"
        )
        await state.set_state(GroupStates.waiting_for_group)
        await message.answer(text, parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        return

    loading_message = await message.answer("⏳ Загружаю расписание...")

    try:
        if message.text == "🍎 На неделю":
            next_week = False
        elif message.text == "🍏 На следующую неделю":
            next_week = True

        current_dict = get_groups_dict_safe()
        result = await ph.get_group_week_schedule(group, current_dict, next_week)

        if result is None:
            text = (
                "🤷‍♂️ Расписание отсутствует\n"
                "Проверьте актуальную информацию на официальном сайте."
            )
            await safe_delete_message(loading_message)
            await message.answer(text)
            return

        alert_info, week_schedule_data = result

        if not week_schedule_data:
            await safe_delete_message(loading_message)
            await message.answer(f"🤔 Для указанной группы расписание не найдено: <code>{group}</code>", parse_mode="HTML")
            return

        await safe_delete_message(loading_message)

        if alert_info:
            formatted_alert_info = sh.collect_alert_info(alert_info, group)
            if formatted_alert_info:
                await message.answer(formatted_alert_info, parse_mode="HTML")

        for elem in week_schedule_data:
            formatted_data = sh.collect_day_data(elem)
            if formatted_data and formatted_data != "Расписание не найдено":
                await message.answer(formatted_data, parse_mode="HTML")

    except Exception as e:
        await safe_delete_message(loading_message)
        await message.answer(f"❌ Ошибка при загрузке расписания: {str(e)}")


@router.message(F.text == "👇 На сегодня")
@router.message(F.text == "👉 На завтра")
async def show_day_schedule(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    db = message.bot.db
    group = db.get_user_group(user_id)

    if not group:
        text = (
            "📝 У вас еще не установлена группа.\n"
            "Введите <b>точное</b> название учебной группы:"
        )
        await state.set_state(GroupStates.waiting_for_group)
        await message.answer(text, parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        return

    loading_message = await message.answer("⏳ Загружаю расписание...")

    try:
        if message.text == "👇 На сегодня":
            day_number = th.get_today_date()
        elif message.text == "👉 На завтра":
            day_number = th.get_tomorrow_date()

        next_week = None
        if th.get_today_day() == 'Sunday':
            next_week = True

        current_dict = get_groups_dict_safe()
        result = await ph.get_group_week_schedule(group, current_dict, next_week)

        if result is None:
            text = (
                "🤷‍♂️ Расписание отсутствует\n"
                "Проверьте актуальную информацию на официальном сайте."
            )
            await safe_delete_message(loading_message)
            await message.answer(text)
            return

        alert_info, week_schedule_data = result

        if not week_schedule_data:
            await safe_delete_message(loading_message)
            await message.answer(f"В этот день занятий нет!🎉", parse_mode="HTML")
            return

        logger.info(f"🔍 Ищем день: {day_number}")

        found = False
        day_data = None
        for day_object in week_schedule_data:
            day_date = day_object['day']
            pattern = r'\b' + day_number + r'\b'

            if re.search(pattern, day_date):
                day_data = day_object
                found = True
                logger.info(f"✅ Найдено по числу: {day_number}")
                break

        if not found:
            await safe_delete_message(loading_message)
            await message.answer(f"В этот день занятий нет!🎉")
            return

        await safe_delete_message(loading_message)

        if alert_info:
            formatted_alert_info = sh.collect_alert_info(alert_info, group)
            if formatted_alert_info:
                await message.answer(formatted_alert_info, parse_mode="HTML")

        formatted_data = sh.collect_day_data(day_data)
        if formatted_data and formatted_data != "Расписание не найдено":
            await message.answer(formatted_data, parse_mode="HTML")
        else:
            await message.answer(f"❌ Для указанной группы расписание не найдено: <code>{group}</code>")

    except Exception as e:
        await safe_delete_message(loading_message)
        await message.answer(f"❌ Ошибка при загрузке расписания: {str(e)}")


async def safe_delete_message(message):
    try:
        await message.delete()
    except Exception:
        pass


@router.message(F.text == "◀️ Назад")
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=menu_keyboard)
