from parser_modules.time_handlers import get_lesson_end_time


def collect_alert_info(alert_info, group):
    if not alert_info:
        return "Дополнительной информации не найдено"

    result = ""

    for item in alert_info:
        for name, data in item.items():
            if name.lower() == 'группа:':
                result += f"<b>{name.capitalize()}</b> <code>{group}</code>\n"
            else:
                result += f"<b>{name.capitalize()}</b> <code>{data.capitalize()}</code>\n"

    return result


def collect_day_data(day_data: dict):
    if not day_data:
        return "Расписание не найдено"

    day = day_data['day']
    time_slots = day_data['time_slots']

    result = f"<blockquote>🗓 {day.upper()}</blockquote>\n\n"

    if not time_slots:
        result += "Нет пар\n"

    for time in time_slots:
        lesson_dict = time_slots[time]

        result += f"⏰ <code>{time} - {get_lesson_end_time(time)}</code>\n"
        for lesson_index, lesson in lesson_dict.items():

            if lesson['type'] == 'free':
                result += " Занятия нет🎉\n"
            else:
                if lesson_index > 0:
                    result += '\n'

                result += f"✍️<b>{lesson['name'].upper()}</b>\n"

                if lesson.get('lesson_type'):
                    result += f" Тип занятия: <code>{lesson['lesson_type']}</code>\n"
                elif lesson.get('lesson_type'):
                    result += f" Тип занятия: <code>не указан</code>\n"

                if lesson.get('teacher'):
                    teachers = ', '.join(lesson['teacher'])
                    result += f" Преподаватель: <code>{teachers}</code>\n"
                else:
                    result += " Преподаватель: <code>не указан</code>\n"

                if lesson.get('audience'):
                    result += f" Аудитория: <code>{lesson['audience']}</code>\n"
                else:
                    result += f" Аудитория: <code>не указана</code>\n"

                if lesson.get('subgroup'):
                    result += f" Подгруппа: <code>{lesson['subgroup']}</code>\n"

        result += '\n'

    return result
