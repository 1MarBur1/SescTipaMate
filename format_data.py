import requests
from requests.utils import default_headers
import json
import logging
from collections import defaultdict

lessons_time = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")
groups = {
    "8А": 1, "8В": 2, "9В": 3, "9A": 4, "9Б": 5, "11А": 6, "11Б": 7, "11В": 8, "9Е": 9, "9Г": 11, "10А": 12, "10Б": 13,
    "10В": 14, "10Г": 15, "10Д": 16, "10Е": 17, "10З": 18, "10К": 19, "10Л": 20, "10М": 21, "10Н": 22, "10С": 23,
    "11Г": 24, "11Д": 25, "11Е": 26, "11З": 27, "11К": 28, "11Л": 29, "11М": 30, "11С": 31, "11Н": 32
}


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

        for group in groups.items():
            try:
                response = requests.get(
                    f"https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday={day}&group={group[1]}",
                    headers=default_headers()
                )
            except requests.exceptions.RequestException:
                logging.exception(f"During fetching schedule for {group[0]} group request exception has been thrown")
                continue
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

    formatted = [""] * 7
    if not schedule:
        return dialog.message("mail_no_schedule", date=date)
    for lesson in schedule:
        entry = f'    {lesson["subject"]}'
        if lesson["audience"]:
            entry += f' *[{lesson["audience"]}]*'
        if lesson["teacher"]:
            entry += f' - _{lesson["teacher"]}_'
        formatted[lesson["number"] - 1] += entry + "\n"
    result = dialog.message("mail_schedule_header", date=date) + "\n"
    for i in range(7):
        if not formatted[i]:
            formatted[i] = "    \[_нет_]\n"
        result += f"*{i+1}. {lessons_time[i]}*\n"
        result += f"{formatted[i]}"
    return result
