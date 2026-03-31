import asyncio
import logging
from typing import Dict
from parser_modules import preparing_handler as ph

logger = logging.getLogger(__name__)

groups_dict: Dict[str, str] = {}

update_event = asyncio.Event()


async def update_groups_dict():
    logger.info("🔄 Начинаю обновление groups_dict...")

    url = "https://www.istu.edu/schedule/?special=vikl"
    new_dict = await ph.get_groups_dict(url)

    if new_dict:
        groups_dict.clear()
        groups_dict.update(new_dict)
        logger.info(f"✅ groups_dict обновлён! Всего групп: {len(groups_dict)}")
        update_event.set()
    else:
        logger.error(
            "❌ Не удалось обновить groups_dict — используем старые данные")


async def auto_update_task(interval_hours: int = 24):
    interval_seconds = interval_hours * 60 * 60

    await update_groups_dict()

    while True:
        logger.info(f"⏳ Следующее обновление через {interval_hours} часов...")
        await asyncio.sleep(interval_seconds)
        await update_groups_dict()
