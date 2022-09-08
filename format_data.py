import json

lessonsTime = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")


def format_data(response, date, mailing, dialog):
    data = json.loads(response.text)
    mailing_text = ""
    lessons = [[] for _ in range(7)]
    x = 0

    if mailing:
        mailing_text = dialog.message("mail_delivered")

    message_for_user = "Привет! " + mailing_text + str(date) + " у тебя будет такое расписание: \n\n"

    if not len(data["lessons"]):
        message_for_user = "Привет! " + mailing_text + str(date) + " не запланироавно никаких уроков =("

    for i in range(len(data["lessons"])):
        lessons_ = data["lessons"]
        lessons[lessons_[i]["number"] - 1].append(lessons_[i])

    for i in range(len(data["diffs"])):
        diffs_ = data["diffs"]
        lessons[diffs_[i]["number"] - 1].append(diffs_[i])

    if len(data["lessons"]):
        for i in lessons:
            message_for_user += lessonsTime[x] + " | "
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
