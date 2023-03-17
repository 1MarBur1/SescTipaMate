from src.utils.i18n import i18n

lessons_time = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")


class LessonPattern:
    COMMON = "    {}\n"
    DIFF = "    * {}\n"
    ADDED = "    <b>+ {}</b>\n"
    REMOVED = "    − <s>{}</s>\n"


def format_lesson(lesson, pattern=LessonPattern.COMMON):
    result = lesson.subject
    if lesson.auditory:
        result += f" <i>[{lesson.auditory}]</i>"
    if lesson.teacher:
        result += f" - <i>{lesson.teacher}</i>"

    return pattern.format(result)


def format_timetable(lessons):
    result = ""
    for i in range(7):
        if not lessons[i]:
            lessons[i] = "    [<i>нет</i>]\n"
        result += f"<b>{i + 1}. {lessons_time[i]}</b>\n"
        result += lessons[i]
    return result


def format_schedule(schedule, date):
    if not schedule:
        return i18n.string("mail.no_schedule", date=date)

    lessons = [""] * 7
    for lesson in schedule:
        pattern = LessonPattern.DIFF if lesson.is_diff else LessonPattern.COMMON
        lessons[lesson.number - 1] += format_lesson(lesson, pattern)

    return i18n.string("mail.schedule_header", date=date) + "\n" + format_timetable(lessons)


def format_diffs(schedule, added, removed, date):
    lessons = [""] * 7
    for lesson in schedule:
        pattern = LessonPattern.ADDED if lesson in added else LessonPattern.COMMON
        lessons[lesson.number - 1] += format_lesson(lesson, pattern)
    for lesson in removed:
        lessons[lesson.number - 1] += format_lesson(lesson, pattern=LessonPattern.REMOVED)

    return i18n.string("mail.diff_header", date=date) + "\n" + format_timetable(lessons)


def format_backup():
    ...
