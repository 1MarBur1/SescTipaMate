import requests
import json

lessons_time = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")
groups = ["8А", "8В", "9В", "9A", "9Б", "11А", "11Б", "11В", "9Е", "", "9Г", "10А", "10Б", "10В", "10Г", "10Д", "10Е",
          "10З", "10К", "10Л", "10М", "10Н", "10С", "11Г", "11Д", "11Е", "11З", "11К", "11Л", "11М", "11С", "11Н"]


class ScheduleProvider:
    def __init__(self):
        self.__schedule = {"teachers": {}, "audiences": {}, "groups": {}}

    def fetch_schedule(self, day):
        # TODO: check schedule diffs
        self.__schedule = {"teachers": {}, "audiences": {}, "groups": {}}

        for group in range(1, len(groups) + 1):
            response = requests.get(f"https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday={day}&group={group}")
            data = json.loads(response.text)

            for les in data["lessons"] + data["diffs"]:
                del les["uid"], les["weekday"]
                aud = les.pop("auditory")
                lesson = {**les, "audience": aud}

                teacher = lesson["teacher"]
                if teacher not in self.__schedule["teachers"]:
                    self.__schedule["teachers"][teacher] = []
                self.__schedule["teachers"][teacher].append(lesson)

                if aud not in self.__schedule["audiences"]:
                    self.__schedule["audiences"][aud] = []
                self.__schedule["audiences"][aud].append(lesson)

                if group not in self.__schedule["groups"]:
                    self.__schedule["groups"][group] = []
                self.__schedule["groups"][group].append(lesson)

    def for_group(self, group):
        return self.__schedule["groups"].get(group, [])

    def for_audience(self, audience):
        return self.__schedule["audiences"].get(audience, [])

    def for_teacher(self, teacher):
        return self.__schedule["teachers"].get(teacher, [])


def format_schedule(schedule):
    formatted = [""] * 7
    for lesson in schedule:
        entry = f'    {lesson["subject"]}'
        if lesson["audience"]:
            entry += f' *[{lesson["audience"]}]*'
        if lesson["teacher"]:
            entry += f' - _{lesson["teacher"]}_'
        formatted[lesson["number"] - 1] += entry + "\n"
    result = ""
    for i in range(7):
        if not formatted[i]:
            formatted[i] = "    \[_нет_]\n"
        result += f"*{lessons_time[i]}*\n"
        result += f"{formatted[i]}"
    return result


def format_data(response, date, mailing, dialog):
    data = json.loads(response.text)
    mailing_text = ""
    lessons = [[] for _ in range(7)]
    x = 0

    if mailing:
        mailing_text = dialog.message("mail_delivered") + " "

    message_for_user = "Привет! " + mailing_text + str(date) + " у тебя будет такое расписание: \n\n"

    if not len(data["lessons"]):
        message_for_user = "Привет! " + mailing_text + str(date) + " не запланироавно никаких уроков =("

    for i in range(len(data["lessons"])):
        lessons_ = data["lessons"]
        lessons[lessons_[i]["number"] - 1].append(lessons_[i])

    for i in range(len(data["diffs"])):
        diffs_ = data["diffs"]
        if diffs_[i]["subject"] != "Нет":
            lessons[diffs_[i]["number"] - 1].append(diffs_[i])

    if len(data["lessons"]):
        for i in lessons:
            message_for_user += lessons_time[x] + " | "
            if len(i):
                if i[0]["subject"] == "Русский":
                    i[0]["subject"] = "РускЯзык"
                message_for_user += i[0]["subject"] + " | "
                for j in i:
                    message_for_user += j["auditory"]
                    if j != i[-1]:
                        message_for_user += ","
                if i[0]["auditory"] != "СпЗал":
                    message_for_user += "каб.\n"
                else:
                    message_for_user += "\n"
            else:
                message_for_user += "<---нет--->\n"
            x += 1

    return message_for_user
