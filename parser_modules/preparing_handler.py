# parser_modules/preparing_handler.py
from bs4 import BeautifulSoup
from parser_modules.async_request import requester
from parser_modules.time_handlers import get_full_today_date
from typing import Optional, Dict, List, Tuple, Any
import asyncio
import logging

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_groups_dict(url: str, headers: Optional[Dict] = None) -> Dict[str, str]:
    logger.info("🔍 Начался процесс загрузки данных о группах...")
    logger.info(f"🌐 URL: {url}")

    html = await requester.get(url)

    if html is None:
        logger.error("❌ Не удалось загрузить главную страницу расписания")
        return {}

    main_page_html = BeautifulSoup(html, "html.parser")

    content_div = main_page_html.find(
        "div", class_=lambda c: c and "content" in c)

    if not content_div:
        logger.error("❌ Не найден блок class='content' на странице")
        return {}

    content = content_div.find_all("li")
    if not content:
        logger.warning("⚠️ Не найдены элементы <li> на странице институтов")

    institute_dict = {}
    logger.info(f"📚 Загружаем институты... (найдено {len(content)} элементов)")

    for item in content:
        link_tag = item.find("a")
        if link_tag and link_tag.get("href"):
            institute_name = link_tag.text.strip()
            institute_href = link_tag.get("href").strip()

            if institute_href.startswith("http"):
                full_url = institute_href
            elif institute_href.startswith("?"):
                full_url = "https://www.istu.edu/schedule/" + institute_href
            else:
                full_url = "https://www.istu.edu/schedule/" + institute_href

            institute_dict[institute_name] = full_url
            logger.info(f"  🏛️ {institute_name} → {full_url}")

    groups_dict = {}
    logger.info(f"👥 Загружаем группы из {len(institute_dict)} институтов...")

    for idx, (name, institute_link) in enumerate(institute_dict.items(), 1):
        logger.info(
            f"  [{idx}/{len(institute_dict)}] Обработка института: {name}")
        try:
            html = await requester.get(institute_link)
            if html is None:
                logger.warning(
                    f"  ⚠️ Не удалось загрузить страницу института: {name}")
                continue

            groups_list_page = BeautifulSoup(html, "html.parser")
            content_div = groups_list_page.find(
                "div", class_=lambda c: c and "content" in c)
            if not content_div:
                logger.warning(
                    f"  ⚠️ Нет блока 'content' на странице института {name}")
                continue

            kurs_list = content_div.find(
                "ul", class_=lambda c: c and "kurs-list" in c)

            if not kurs_list:
                kurs_list = content_div.find("ul")

            if not kurs_list:
                logger.warning(
                    f"  ⚠️ Нет списка групп на странице института {name}")
                continue

            groups = kurs_list.find_all("ul")
            for item in groups:
                links = item.find_all("li")
                for a in links:
                    link_tag = a.find("a")
                    if link_tag and link_tag.get("href"):
                        group_name = link_tag.text.strip()
                        group_href = link_tag.get("href").strip()

                        if group_href.startswith("http"):
                            full_url = group_href
                        elif group_href.startswith("?"):
                            full_url = "https://www.istu.edu/schedule/" + group_href
                        else:
                            full_url = "https://www.istu.edu/schedule/" + group_href

                        groups_dict[group_name] = full_url

        except Exception as e:
            logger.error(
                f"  ❌ Ошибка при обработке института {name}: {type(e).__name__} — {e}")
            continue

    logger.info(f"✅ Загрузка завершена! Всего групп: {len(groups_dict)}")

    return groups_dict


async def get_group_week_schedule(
    found_group: str,
    groups_dict: Dict[str, str],
    next_week: bool = False
) -> Optional[Tuple[Any, List[Dict]]]:
    logger.info(f"🔍 Запрос расписания для группы: {found_group}")

    if not found_group or found_group not in groups_dict:
        logger.error(f"❌ Группа {found_group} не найдена в groups_dict")
        return None

    url = groups_dict[found_group].strip()
    logger.info(
        f"🌐 URL запроса: {url + '&date=' + get_full_today_date(next_week)}")

    try:
        html = await requester.get(url + '&date=' + get_full_today_date(next_week))

        if html is None:
            logger.error("❌ requester.get() вернул None — запрос не удался")
            return None

        logger.info(f"✅ HTML получен, длина: {len(html)} символов")

        schedule_page_html = BeautifulSoup(html, "html.parser")

        content_div = schedule_page_html.find(
            "div", class_=lambda c: c and "content" in c)
        if not content_div:
            logger.error("❌ Не найден блок class='content'")
            return None

        alert_div = content_div.find("div", class_="alert-info")
        alert_content = alert_div.find_all("p") if alert_div else []

        alert_info = []
        for item in alert_content[:-2]:
            name_and_data = item.contents
            name = name_and_data[0].strip()
            data_tag = name_and_data[1]
            data = data_tag.text.capitalize() if hasattr(
                data_tag, 'text') else str(data_tag)
            alert_info.append({name: data})

        odd_week = schedule_page_html.find("div", class_="full-odd-week")
        even_week = schedule_page_html.find("div", class_="full-even-week")

        week = odd_week if odd_week else even_week

        if not week:
            logger.error("❌ Не найден блок с расписанием")
            return None

        # 🔹 Определяем тип недели
        parsed_week_type = 'odd' if 'full-odd-week' in week.get(
            'class', []) else 'even'
        logger.info(f"📅 Спарсена неделя: {parsed_week_type}")

        week_schedule_data = []
        days = week.find_all("h3", class_="day-heading")
        week_schedule = week.find_all("div", class_="class-lines")

        logger.info(f"📚 Найдено дней: {len(week_schedule)}")

        for day_index, day in enumerate(week_schedule):
            day_name = days[day_index].text.strip() if day_index < len(
                days) else f"День {day_index + 1}"
            day_schedule = day.find_all("div", class_="class-line-item")
            day_time_slots = {}

            for lesson in day_schedule:
                content = lesson.find("div", class_="class-tails")
                if not content:
                    continue

                lesson_time_div = content.find("div", class_="class-time")
                lesson_time = lesson_time_div.text if lesson_time_div else "Время не указано"

                lesson_tails = []

                # 🔹 Берём пары для этой недели + все недели
                if parsed_week_type == 'odd':
                    lesson_tails = content.find_all(
                        "div", class_="class-odd-week")
                    lesson_tails.extend(content.find_all(
                        "div", class_="class-all-week"))
                else:
                    lesson_tails = content.find_all(
                        "div", class_="class-even-week")
                    lesson_tails.extend(content.find_all(
                        "div", class_="class-all-week"))

                if not lesson_tails:
                    continue

                if lesson_time not in day_time_slots:
                    day_time_slots[lesson_time] = {}

                lesson_index = len(day_time_slots[lesson_time])

                for lesson_tail in lesson_tails:
                    if "свободно" in lesson_tail.text.lower():
                        day_time_slots[lesson_time][lesson_index] = {
                            'type': 'free'}
                        continue

                    lesson_name_div = lesson_tail.find(
                        "div", class_="class-pred")
                    lesson_name = lesson_name_div.text if lesson_name_div else "Предмет не указан"

                    lesson_info = lesson_tail.find_all(
                        "div", class_="class-info")
                    lesson_type = ""
                    lesson_teachers = []

                    if len(lesson_info) > 0:
                        lesson_type_and_teacher = lesson_info[0].contents
                        if len(lesson_type_and_teacher) > 0:
                            lesson_type = lesson_type_and_teacher[0].strip(
                            ) if lesson_type_and_teacher[0] else ""
                        if len(lesson_type_and_teacher) > 1:
                            for elem in lesson_type_and_teacher[1:]:
                                if hasattr(elem, 'name') and elem.name == 'a':
                                    lesson_teachers.append(elem.text)

                    groups = []
                    subgroup = ""
                    groups_list = lesson_info[1].contents if len(
                        lesson_info) > 1 else []

                    if "подгруппа" in ''.join(str(item) for item in groups_list):
                        for item in groups_list:
                            if hasattr(item, 'name') and item.name == 'a':
                                groups.append(item.text.strip())
                            elif isinstance(item, str) and item.strip():
                                subgroup = item.strip()
                    else:
                        for item in groups_list:
                            if hasattr(item, 'name') and item.name == 'a':
                                groups.append(item.text.strip())

                    if len(groups) > 1:
                        subgroup = ""

                    lesson_aud_div = lesson_tail.find(
                        "div", class_="class-aud")
                    lesson_aud = lesson_aud_div.text if lesson_aud_div else "Аудитория не указана"

                    day_time_slots[lesson_time][lesson_index] = {
                        'type': 'lesson',
                        'name': lesson_name,
                        'lesson_type': lesson_type,
                        'teacher': lesson_teachers,
                        'groups': groups,
                        'subgroup': subgroup,
                        'audience': lesson_aud
                    }
                    lesson_index += 1

            if day_time_slots:
                week_schedule_data.append({
                    'day': day_name,
                    'time_slots': day_time_slots
                })

        logger.info(
            f"✅ Расписание успешно спарсено: {len(week_schedule_data)} дней")
        return alert_info, week_schedule_data

    except asyncio.TimeoutError:
        logger.error(f"⏰ Timeout при загрузке расписания для {found_group}")
        return None

    except Exception as e:
        logger.error(
            f"❌ Ошибка при парсинге расписания для {found_group}: {type(e).__name__} — {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
