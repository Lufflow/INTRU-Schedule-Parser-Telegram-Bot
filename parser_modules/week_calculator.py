# parser_modules/week_calculator.py

import datetime
from functools import lru_cache

# 🔹 🔥 РУЧНАЯ КОРРЕКТИРОВКА: если бот считает неправильно
# 0 = без сдвига (по умолчанию)
# 1 = сдвинуть на 1 неделю вперёд (odd → even, even → odd)
# -1 = сдвинуть на 1 неделю назад
WEEK_OFFSET = 1  # ← 🔹 ИЗМЕНИ ЭТО ЗНАЧЕНИЕ (0 или 1)


@lru_cache(maxsize=1)
def get_semester_start() -> datetime.date:
    today = datetime.date.today()
    current_year = today.year

    september_first = datetime.date(current_year, 9, 1)

    if today < september_first:
        semester_start = datetime.date(current_year - 1, 9, 1)
    else:
        semester_start = september_first

    return semester_start


def clear_semester_cache():
    get_semester_start.cache_clear()


def get_week_number(date: datetime.date = None) -> int:
    if date is None:
        date = datetime.date.today()

    semester_start = get_semester_start()
    delta = date - semester_start

    if delta.days < 0:
        return 0

    week_number = delta.days // 7 + 1

    return week_number


def get_week_type(date: datetime.date = None) -> str:
    """
    Возвращает тип недели: 'odd' (нечётная) или 'even' (чётная)
    """
    week_number = get_week_number(date)

    if week_number <= 0:
        return 'odd'

    # 🔹 🔥 ПРИМЕНЯЕМ СДВИГ
    adjusted_week_number = week_number + WEEK_OFFSET

    if adjusted_week_number % 2 == 1:
        return 'odd'
    else:
        return 'even'


def get_next_week_type() -> str:
    next_week = datetime.date.today() + datetime.timedelta(days=7)
    return get_week_type(next_week)


def is_weekend_switch() -> bool:
    return datetime.date.today().weekday() == 6


def get_target_week_type(days_ahead: int = 0) -> str:
    target_date = datetime.date.today() + datetime.timedelta(days=days_ahead)
    return get_week_type(target_date)


def get_current_week_info() -> dict:
    today = datetime.date.today()
    semester_start = get_semester_start()
    week_number = get_week_number(today)
    week_type = get_week_type(today)

    return {
        'today': today,
        'semester_start': semester_start,
        'week_number': week_number,
        'week_type': week_type,
        'week_offset': WEEK_OFFSET,  # ← Показываем сдвиг
        'days_since_start': (today - semester_start).days,
        'is_before_semester': today < semester_start,
    }
