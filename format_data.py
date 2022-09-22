import logging
import requests
import json
from collections import defaultdict

from stringi18n import i18n

lessons_time = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")
groups = {
    0: "undefined", 1: "8А", 2: "8В", 3: "9В", 4: "9A", 5: "9Б", 6: "11А", 7: "11Б", 8: "11В", 9: "9Е", 11: "9Г",
    12: "10А", 13: "10Б", 14: "10В", 15: "10Г", 16: "10Д", 17: "10Е", 18: "10З", 19: "10К", 20: "10Л", 21: "10М",
    22: "10Н", 23: "10С", 24: "11Г", 25: "11Д", 26: "11Е", 27: "11З", 28: "11К", 29: "11Л", 30: "11М", 31: "11С",
    32: "11Н"
}
groups_inverse = {
    "undefined": 0, "8А": 1, "8В": 2, "9В": 3, "9A": 4, "9Б": 5, "11А": 6, "11Б": 7, "11В": 8, "9Е": 9, "9Г": 11,
    "10А": 12, "10Б": 13, "10В": 14, "10Г": 15, "10Д": 16, "10Е": 17, "10З": 18, "10К": 19, "10Л": 20, "10М": 21,
    "10Н": 22, "10С": 23, "11Г": 24, "11Д": 25, "11Е": 26, "11З": 27, "11К": 28, "11Л": 29, "11М": 30, "11С": 31,
    "11Н": 32
}


class ScheduleProvider:
    def __init__(self):
        self.__schedule = {i: {} for i in range(7)}

    def fetch_schedule(self, day):
        # TODO: check schedule diffs compared to previous version
        self.__schedule[day] = {
            "teachers": defaultdict(lambda: []),
            "audiences": defaultdict(lambda: []),
            "groups": defaultdict(lambda: [])
        }

        for group in groups.items():
            print(day + 1, group[0])
            try:
                response = requests.get(
                    f"https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday={day + 1}&group={group[0]}"
                )
            except requests.exceptions.RequestException:
                logging.exception(f"During fetching schedule for {group[1]} group request exception has been thrown")
                continue
            data = json.loads(response.text)

            for les in data["lessons"] + data["diffs"]:
                del les["uid"], les["weekday"]
                aud = les.pop("auditory")
                lesson = {**les, "audience": aud}

                self.__schedule[day]["teachers"][les["teacher"]].append(lesson)
                self.__schedule[day]["audiences"][aud].append(lesson)
                self.__schedule[day]["groups"][group[0]].append(lesson)

    def for_group(self, day, group):
        return self.__schedule[day]["groups"][group]

    def for_audience(self, day, audience):
        return self.__schedule[day]["audiences"][audience]

    def for_teacher(self, day, teacher):
        return self.__schedule[day]["teachers"][teacher]


def format_schedule(schedule, date):
    formatted = [""] * 7
    if not schedule:
        return i18n.string("mail_no_schedule", date=date)
    for lesson in schedule:
        entry = f'    {lesson["subject"]}'
        if lesson["audience"]:
            entry += f' <i>[{lesson["audience"]}]</i>'
        if lesson["teacher"]:
            entry += f' - <i>{lesson["teacher"]}</i>'
        formatted[lesson["number"] - 1] += entry + "\n"
    result = i18n.string("mail_schedule_header", date=date) + "\n"
    for i in range(7):
        if not formatted[i]:
            formatted[i] = "    [_нет_]\n"
        result += f"<b>{i + 1}. {lessons_time[i]}</b>\n"
        result += f"{formatted[i]}"
    return result


def group_name_by_id(group_id):
    return groups[group_id]


def id_by_group_name(group_name):
    return groups_inverse[group_name]


def group_id_exists(group_id):
    return group_id in groups


def group_name_exists(group_name):
    return group_name in groups_inverse
