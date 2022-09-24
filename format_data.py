import requests
import json
from collections import defaultdict

lessons_time = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")
groups = ["8А", "8В", "9В", "9A", "9Б", "11А", "11Б", "11В", "9Е", "", "9Г", "10А", "10Б", "10В", "10Г", "10Д", "10Е",
          "10З", "10К", "10Л", "10М", "10Н", "10С", "11Г", "11Д", "11Е", "11З", "11К", "11Л", "11М", "11С", "11Н"]


class ScheduleProvider:
    def __init__(self):
        self.__schedule = {i: {} for i in range(1, 8)}

    def fetch_schedule(self, day):
        # TODO: check schedule diffs compared to previous version
        self.__schedule[day] = {
            "teachers": defaultdict(lambda: []),
            "audiences": defaultdict(lambda: []),
            "groups": defaultdict(lambda: [])
        }

        for group in range(1, len(groups) + 1):
            response = requests.get(f"https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday={day}&group={group}")
            data = json.loads(response.text)

            for les in data["lessons"] + data["diffs"]:
                del les["uid"], les["weekday"]
                aud = les.pop("auditory")
                lesson = {**les, "audience": aud}

                self.__schedule[day]["teachers"][les["teacher"]].append(lesson)
                self.__schedule[day]["audiences"][aud].append(lesson)
                self.__schedule[day]["groups"][group].append(lesson)

    def for_group(self, day, group):
        return self.__schedule[day]["groups"][group]

    def for_audience(self, day, audience):
        return self.__schedule[day]["audiences"][audience]

    def for_teacher(self, day, teacher):
        return self.__schedule[day]["teachers"][teacher]


def format_schedule(schedule, date):
    from main import dialog

    formatted = [[]] * 7
    if not schedule:
        return dialog.message("mail_no_schedule", date=date)
    for lesson in schedule:
        entry = f'    {lesson["subject"]}'
        if lesson["audience"]:
            entry += f' *[{lesson["audience"]}]*'
        if lesson["teacher"]:
            entry += f' - _{lesson["teacher"]}_'
        formatted[lesson["number"] - 1].append({"string": entry, "subgroup": lesson["subgroup"]})
    result = dialog.message("mail_schedule_header", date=date) + "\n"
    for i in range(7):
        if not formatted[i]:
            formatted[i]["string"] = "    \[_нет_]"
        result += f"*{i+1}. {lessons_time[i]}*\n"
        result += "\n".join(map(lambda d: d["string"], sorted(formatted[i], key=lambda d: d["subgroup"])))
    return result
