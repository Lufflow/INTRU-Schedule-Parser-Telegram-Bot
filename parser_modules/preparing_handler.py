from bs4 import BeautifulSoup
from parser_modules.async_request import requester
from parser_modules.time_handlers import get_full_today_date
from typing import Optional, Dict, List, Tuple, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


async def get_groups_dict(url: str, headers: Optional[Dict] = None) -> Dict[str, str]:
    logger.info("Начался процесс загрузки данных о группах.")
    logger.info(f"URL: {url}")

    html = await requester.get(url)

    if html is None:
        logger.error("Не удалось загрузить главную страницу расписания")
        return {}

    main_page_html = BeautifulSoup(html, "html.parser")

    content_div = main_page_html.find("ul", class_="list-sublist")

    if not content_div:
        logger.error("Не найден блок class='list-sublist' на странице")
        return {}

    content = content_div.find_all("li", class_="multilist-item")
    if not content:
        logger.warning("Не найдены элементы <li> на странице институтов")

    institute_dict = {}
    logger.info(f"Загрузка институтов... (найдено {len(content)} элементов)")

    for item in content:
        link_tag = item.find("a")
        if link_tag and link_tag.get("href"):
            institute_name = link_tag.text.strip()
            institute_href = link_tag.get("href").strip()

            if institute_href.startswith("http"):
                full_url = institute_href
            else:
                full_url = "https://www.istu.edu" + institute_href

            institute_dict[institute_name] = full_url
            logger.info(f"{institute_name} → {full_url}")

    groups_dict = {}
    logger.info(f"Загрузка групп из {len(institute_dict)} институтов.")

    for idx, (name, institute_link) in enumerate(institute_dict.items(), 1):
        logger.info(
            f"  [{idx}/{len(institute_dict)}] Обработка института: {name}")
        try:
            html = await requester.get(institute_link)
            if html is None:
                logger.warning(
                    f"Не удалось загрузить страницу института: {name}")
                continue

            groups_list_page = BeautifulSoup(html, "html.parser")

            schd_grp_list = groups_list_page.find(
                "div", class_="schd-grp-list")
            if not schd_grp_list:
                logger.warning(
                    f"Нет блока 'schd-grp-list' на странице института {name}")
                continue

            group_items = schd_grp_list.find_all("div", class_="schd-grp-item")

            for item in group_items:
                link_tag = item.find("a")
                if link_tag and link_tag.get("href"):
                    group_name = link_tag.text.strip()
                    group_href = link_tag.get("href").strip()

                    if group_href.startswith("http"):
                        full_url = group_href
                    else:
                        full_url = "https://www.istu.edu" + group_href

                    groups_dict[group_name] = full_url

        except Exception as e:
            logger.error(
                f"Ошибка при обработке института {name}: {type(e).__name__} — {e}")
            continue

    logger.info(f"Загрузка завершена. Всего групп: {len(groups_dict)}")

    return groups_dict


async def get_group_week_schedule(
    found_group: str,
    groups_dict: Dict[str, str],
    next_week: bool = False
) -> Optional[Tuple[Any, List[Dict]]]:
    logger.info(f"Запрос расписания для группы: {found_group}")

    if not found_group or found_group not in groups_dict:
        logger.error(f"Группа {found_group} не найдена в groups_dict")
        return None

    base_url = groups_dict[found_group].strip().rstrip('/?')
    date_str = get_full_today_date(next_week)
    request_url = f"{base_url}/{date_str}/"

    logger.info(f"Обращение по ссылке {request_url}")
    logger.info(f"URL запроса: {request_url}")

    try:
        html = await requester.get(request_url)

        if html is None:
            logger.warning(f"Первая попытка не удалась, повтор через 3 сек...")
            await asyncio.sleep(3)
            html = await requester.get(request_url)

        if html is None:
            logger.error("requester.get() вернул None после повторной попытки")
            return None

        logger.info(f"HTML получен, длина: {len(html)} символов")

        schedule_page_html = BeautifulSoup(html, "html.parser")

        alert_info = []
        info_blocks = schedule_page_html.find_all(
            "div", class_="schedule-info-block")
        for block in info_blocks:
            items = block.find_all("div", class_="info-block-item")
            for item in items:
                label_div = item.find("div", class_="info-block-item-label")
                value_div = item.find("div", class_="info-block-item-value")
                if label_div and value_div:
                    label = label_div.text.strip().rstrip(":")
                    value = value_div.text.strip()
                    alert_info.append({label: value})

        week_container = schedule_page_html.find(
            "div", class_=lambda c: c and "sch-list-week" in c)
        if not week_container:
            logger.error("Не найден блок class='sch-list-week'")
            return None

        parsed_week_type = 'odd' if 'sch-list-week-odd' in week_container.get(
            'class', []) else 'even'

        week_schedule_data = []
        day_containers = week_container.find_all("div", class_="sch-list-day")

        for day_container in day_containers:
            day_header = day_container.find("h2", class_="sch-list-day-header")
            day_name = day_header.text.strip() if day_header else "День"

            lesson_items = day_container.find_all(
                "div", class_="sch-list-item")
            day_time_slots = {}

            for lesson_item in lesson_items:
                time_div = lesson_item.find(
                    "div", class_="sch-list-item-time-inner")
                lesson_time = time_div.text.strip() if time_div else "Время не указано"

                if parsed_week_type == 'odd':
                    week_block = lesson_item.find("div", class_="week-odd")
                    if not week_block:
                        week_block = lesson_item.find("div", class_="week-all")
                else:
                    week_block = lesson_item.find("div", class_="week-even")
                    if not week_block:
                        week_block = lesson_item.find("div", class_="week-all")

                if not week_block:
                    continue

                lesson_cards = week_block.find_all("div", class_="schcls-item")

                if lesson_time not in day_time_slots:
                    day_time_slots[lesson_time] = {}

                lesson_index = len(day_time_slots[lesson_time])

                for card in lesson_cards:
                    info_div = card.find("div", class_="schcls-item-info")
                    if not info_div:
                        lesson_type = 'free'
                    lesson_type = 'lesson'

                    name_div = info_div.find("div", class_="schcls-item-name")
                    lesson_name = name_div.text.strip() if name_div else "Предмет не указан"

                    type_div = info_div.find(
                        "div", class_="schcls-item-distype")
                    lesson_type = ""
                    if type_div:
                        type_class = type_div.get('class', [])
                        if 'type-1' in type_class:
                            lesson_type = "лекция"
                        elif 'type-2' in type_class:
                            lesson_type = "практика"
                        elif 'type-3' in type_class:
                            lesson_type = "лабораторная работа"
                        else:
                            lesson_type = type_div.text.strip()

                    teachers = []
                    prepod_div = info_div.find(
                        "div", class_="schcls-item-prepod")
                    if prepod_div:
                        for link in prepod_div.find_all("a"):
                            teachers.append(link.text.strip())

                    groups = []
                    subgroup = ""
                    group_div = info_div.find(
                        "div", class_="schcls-item-group")
                    if group_div:
                        for link in group_div.find_all("a"):
                            groups.append(link.text.strip())
                        group_text = group_div.get_text(
                            separator=' ', strip=True)
                        if "подгруппа" in group_text.lower():
                            parts = group_text.split("подгруппа")
                            if len(parts) > 1:
                                subgroup = "подгруппа " + parts[1].strip()

                    aud_div = card.find("div", class_="schcls-item-aud")
                    lesson_aud = ""
                    if aud_div:
                        link = aud_div.find("a")
                        if link:
                            lesson_aud = link.text.strip()
                        else:
                            lesson_aud = aud_div.text.strip()
                    if not lesson_aud or lesson_aud == "-":
                        lesson_aud = "Аудитория не указана"

                    day_time_slots[lesson_time][lesson_index] = {
                        'type': 'lesson',
                        'name': lesson_name,
                        'lesson_type': lesson_type,
                        'teacher': teachers,
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
            f"Расписание успешно спарсено: {len(week_schedule_data)} дней")
        return alert_info, week_schedule_data

    except asyncio.TimeoutError:
        logger.error(
            f"Превышено ожидание при загрузке расписания для {found_group}")
        return None

    except Exception as e:
        logger.error(
            f"Ошибка при парсинге расписания для {found_group}: {type(e).__name__} — {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
