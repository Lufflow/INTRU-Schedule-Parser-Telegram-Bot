from datetime import datetime, timedelta


def get_today_date():
    return str(datetime.today().day)


def get_today_day():
    return datetime.today().strftime('%A')


def get_full_today_date(next_week: bool = False):
    if next_week:
        target_date = datetime.today() + timedelta(days=7)
    else:
        target_date = datetime.today()

    return f"{target_date.year}-{target_date.month}-{target_date.day}"


def get_tomorrow_date():
    return str((datetime.today() + timedelta(days=1)).day)


def get_lesson_end_time(time):
    hours, minutes = time.split(':')
    hours = int(hours) + 1
    minutes = int(minutes) + 30

    if minutes >= 60:
        hours += 1
        minutes -= 60
    if minutes == 0:
        minutes = '00'
    if hours >= 24:
        hours -= 24
    if hours == 0:
        hours == '00'

    return f"{hours}:{minutes}"
