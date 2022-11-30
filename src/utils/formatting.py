from src.utils.i18n import i18n

lessons_time = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")


def format_schedule(schedule, date):
    formatted = [""] * 7
    if not schedule:
        return i18n.string("mail_no_schedule", date=date)
    for lesson in schedule:
        entry = f'    {lesson.subject}'
        if lesson.auditory:
            entry += f' <i>[{lesson.auditory}]</i>'
        if lesson.teacher:
            entry += f' - <i>{lesson.teacher}</i>'
        formatted[lesson.number - 1] += entry + "\n"
    result = i18n.string("mail_schedule_header", date=date) + "\n"
    for i in range(7):
        if not formatted[i]:
            formatted[i] = "    [<i>нет</i>]\n"
        result += f"<b>{i + 1}. {lessons_time[i]}</b>\n"
        result += f"{formatted[i]}"
    return result


def format_diffs():
    ...


def format_backup():
    ...
