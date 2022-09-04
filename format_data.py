import json
lessonsTime = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")

def formatData(response, date, mailing):
    data = json.loads(response.text)
    mailingText = ""
    if mailing:
        mailingText = "Я к тебе с рассылкой, "
    
    messageforuser = "Привет! " + mailingText + str(date)+ " у тебя будет такое расписание: \n"
    n = 0
    if (not len(data["lessons"])):
        messageforuser = "Привет! " + mailingText + str(date)+ " не запланироавно никаких уроков =("

    for i in range(len(data["lessons"])):
        if (i+1<len(data["lessons"])):
            if (data["lessons"][i-1]["number"] == data["lessons"][i]["number"]):
                n += 1
            elif (data["lessons"][i+1]["number"] == data["lessons"][i]["number"]):
                messageforuser += "\n"
                messageforuser += lessonsTime[data["lessons"][i]["number"]-1] + " | " + data["lessons"][i]["subject"] + " | " + "2 группы: " +  data["lessons"][i+1]["auditory"] + ", " + data["lessons"][i]["auditory"] + "каб."
            else:
                messageforuser += "\n"
                messageforuser += lessonsTime[data["lessons"][i]["number"]-1] + " | "  + data["lessons"][i]["subject"] + " | " + data["lessons"][i]["auditory"] + "каб."
        else:
            messageforuser += "\n"
            messageforuser += lessonsTime[data["lessons"][i]["number"]-1] + " | "  + data["lessons"][i]["subject"] + " | " + data["lessons"][i]["auditory"] + "каб."
        
    return messageforuser