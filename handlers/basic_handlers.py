from aiogram import Router, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from keyboards.menu_keyboard import menu_keyboard, cancel_keyboard
from handlers.group_handlers import GroupStates
from dotenv import load_dotenv
import os
import asyncio
import logging

load_dotenv()

logger = logging.getLogger(__name__)
router = Router()
ADMIN_ID = os.getenv("ADMIN_ID")

broadcast_status = {
    'in_progress': False,
    'total': 0,
    'sent': 0,
    'failed': 0
}


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


@router.message(Command("number_of_users"))
async def get_number_of_users(message: types.Message, db=None):
    db = message.bot.db

    if message.from_user.id != ADMIN_ID:
        await message.answer(
            "❌ У вас нет прав для этой команды",
            reply_markup=menu_keyboard
        )
        return

    user_id_list = db.get_user_id_list()

    if user_id_list is None:
        await message.answer(
            "⚠️ Не удалось получить данные о пользователях",
            reply_markup=menu_keyboard
        )
        return

    total_users = len(user_id_list)

    await message.answer(
        f"📊 <b>Статистика пользователей</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"📅 Данные актуальны на момент запроса",
        parse_mode="HTML",
        reply_markup=menu_keyboard
    )

    logger.info(
        f"Администратор {message.from_user.id} запросил статистику: {total_users} пользователей")


@router.message(Command("send_message"))
async def start_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer(
            "❌ У вас нет прав для этой команды",
            reply_markup=menu_keyboard
        )
        return

    await state.set_state(GroupStates.waiting_for_message)
    await message.answer(
        "📨 Введите сообщение для <b>массовой рассылки</b>:\n\n"
        "<i>Отправьте текст или перешлите сообщение</i>\n"
        "Для отмены нажмите ❌ Отмена",
        parse_mode="HTML",
        reply_markup=cancel_keyboard
    )


@router.message(GroupStates.waiting_for_message, F.text == "❌ Отмена")
async def cancel_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Рассылка отменена",
        reply_markup=menu_keyboard
    )


@router.message(GroupStates.waiting_for_message)
async def process_broadcast(message: types.Message, state: FSMContext):
    db = message.bot.db
    user_id_list = db.get_user_id_list()

    if not user_id_list:
        await message.answer("❌ Нет пользователей для рассылки")
        await state.clear()
        return

    if broadcast_status['in_progress']:
        await message.answer("⚠️ Рассылка уже выполняется!")
        return

    await state.clear()

    await message.answer(
        f"✅ <b>Рассылка запущена!</b>\n\n"
        f"👥 Получателей: {len(user_id_list)}\n"
        f"Вы получите отчёт по завершении.",
        parse_mode="HTML"
    )

    asyncio.create_task(
        run_background_broadcast(message, user_id_list, db)
    )


async def run_background_broadcast(original_message, user_id_list, db):
    """
    Фоновая задача: отправляет сообщение всем пользователям
    """
    global broadcast_status

    broadcast_status = {
        'in_progress': True,
        'total': len(user_id_list) - 1,  # Без учёта админа
        'sent': 0,
        'failed': 0
    }

    logger.info(
        f"Запуск рассылки: {broadcast_status['total']} пользователей")

    for uid in user_id_list:
        if uid == ADMIN_ID:
            continue

        try:
            await original_message.copy_to(chat_id=uid)
            broadcast_status['sent'] += 1

        except TelegramForbiddenError:
            logger.warning(
                f"Пользователь {uid} заблокировал бота. Удаляю из базы данных...")
            try:
                db.delete_user(uid)
                logger.info(f"Пользователь {uid} удалён из базы данных")
            except Exception as db_err:
                logger.error(
                    f"Ошибка при удалении пользователя {uid} из БД: {db_err}")
            broadcast_status['failed'] += 1

        except TelegramAPIError as e:
            logger.warning(
                f"Ошибка API для пользователя {uid}: {type(e).__name__}: {e}")
            broadcast_status['failed'] += 1

        except Exception as e:
            logger.warning(f"Не удалось отправить пользователю {uid}: {e}")
            broadcast_status['failed'] += 1

        await asyncio.sleep(0.1)

    broadcast_status['in_progress'] = False

    await original_message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📬 Успешно: {broadcast_status['sent']}\n"
        f"❌ Ошибок: {broadcast_status['failed']}\n"
        f"👥 Всего: {broadcast_status['total']}",
        parse_mode="HTML",
        reply_markup=menu_keyboard
    )

    logger.info(
        f"Рассылка завершена: "
        f"{broadcast_status['sent']}/{broadcast_status['total']} успешно"
    )


@router.message(Command("broadcast_status"))
async def check_broadcast_status(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if broadcast_status['in_progress']:
        percent = round(
            broadcast_status['sent'] / broadcast_status['total'] * 100)
        await message.answer(
            f"🔄 <b>Рассылка в процессе...</b>\n\n"
            f"📬 Отправлено: {broadcast_status['sent']}/{broadcast_status['total']} ({percent}%)\n"
            f"❌ Ошибок: {broadcast_status['failed']}",
            parse_mode="HTML"
        )
    else:
        await message.answer("✅ Нет активной рассылки", parse_mode='HTML')


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("Используйте кнопки меню!", reply_markup=menu_keyboard)
