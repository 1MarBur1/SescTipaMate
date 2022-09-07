import json
lessonsTime = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")

def formatData(response, date, mailing):
    data = json.loads(response.text)
    mailingText = ""
    lessons = [[], [], [], [], [], [], []]
    x = 0

    if mailing:
        mailingText = "Я к тебе с рассылкой, "
    
    messageforuser = "Привет! " + mailingText + str(date)+ " у тебя будет такое расписание: \n\n"

    if (not len(data["lessons"])):
        messageforuser = "Привет! " + mailingText + str(date)+ " не запланироавно никаких уроков =("

    for i in range(len(data["lessons"])):
        lessons_ = data["lessons"]
        lessons[lessons_[i]["number"]-1].append(lessons_[i])
    
    if (len(data["lessons"])):
        for i in lessons:
            messageforuser += lessonsTime[x] + " | " 
            if len(i):
                if (i[0]["subject"] == "Русский"):
                    i[0]["subject"] = "РускЯзык"
                messageforuser += i[0]["subject"] + " | "
                for j in i:
                    messageforuser += j["auditory"] 
                    if (j != i[-1]):
                        messageforuser += ","
                if i[0]["auditory"] != "СпЗал":
                    messageforuser += "каб.\n"
            else:
                messageforuser += "<---нет--->\n"
            x+=1


    return messageforuser
