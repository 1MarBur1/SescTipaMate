from dataclasses import replace
import schedule
import time
import json
import telebot
from telebot import types
import datetime
import requests
from threading import Thread

now = datetime.datetime.now()
weekday_ = datetime.datetime.today().weekday() + 1
tommorowDate = datetime.datetime.today() + datetime.timedelta(days=1)

joinedFile = open("./ids.txt", "r")
joinedUsers = set()

for line in joinedFile:
    joinedUsers.add(line.strip())
joinedFile.close()

lessonsTime = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")

bot = telebot.TeleBot("5435533576:AAERV3w9cDsGraZ8DiTCjG2AMjva8vD9Wo8")

@bot.message_handler(commands=['start'])
def send_welcome(msg):
    if not (msg.chat.id in joinedUsers):
        joinedFile = open("./ids.txt", "a")
        joinedFile.write(str(msg.chat.id) + "\n")
        joinedUsers.add(msg.chat.id)
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Посмотреть расписание на сегодня", callback_data="openToday")
        button2 = types.InlineKeyboardButton("Посмотреть расписание на завтра", callback_data="openTomorrow")
        markup.add(button1)
        markup.add(button2)
        bot.send_message(msg.chat.id, f"Привет, {msg.from_user.first_name}! Ты являешься учеником СУНЦ УрФУ! Нужно всегда быть в курсе расписания, теперь я буду помогать с этим =)", reply_markup=markup)
    else: 
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Посмотреть расписание на сегодня", callback_data="openToday")
        button2 = types.InlineKeyboardButton("Посмотреть расписание на завтра", callback_data="openTomorrow")
        markup.add(button1)
        markup.add(button2)
        bot.send_message(msg.chat.id, "Воу-воу, друг, ты уже есть в моих списках, не переживай, я тебя оповещу!", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def open_adming(msg):
    if (msg.chat.id == 926132680):
        bot.send_message(msg.chat.id, str(joinedUsers))
    else:
        bot.send_message(msg.chat.id, "У тебя нет админки =/")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "openToday":
        responsetoday = requests.get("https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday=" + str(weekday_) + "&group=22")
        todaydata = json.loads(responsetoday.text)
        messageforuser = "Сегодня, " + str(now.date())+ ", у тебя такое расписание: \n"
        n = 0
        if (not len(todaydata["lessons"])):
            messageforuser = "Сегодня не запланироавно никаких уроков =("

        for i in range(len(todaydata["lessons"])):
            if (i+1<len(todaydata["lessons"])):
                if (todaydata["lessons"][i-1]["number"] == todaydata["lessons"][i]["number"]):
                    n += 1
                elif (todaydata["lessons"][i+1]["number"] == todaydata["lessons"][i]["number"]):
                    messageforuser += "\n"
                    messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | " + todaydata["lessons"][i]["subject"] + " | " + "2 группы: " +  todaydata["lessons"][i+1]["auditory"] + ", " + todaydata["lessons"][i]["auditory"] + "каб."
                else:
                    messageforuser += "\n"
                    messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | "  + todaydata["lessons"][i]["subject"] + " | " + todaydata["lessons"][i]["auditory"] + "каб."
            else:
                messageforuser += "\n"
                messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | "  + todaydata["lessons"][i]["subject"] + " | " + todaydata["lessons"][i]["auditory"] + "каб."

        bot.send_message(call.message.chat.id, messageforuser)
    if call.data == "openTomorrow":
        responsetomorrow = requests.get("https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday=" + str(weekday_ + 1) + "&group=22")
        todaydata = json.loads(responsetomorrow.text)
        messageforuser = "Завтра, " + str(now.date())+ ", у тебя будет такое расписание: \n"
        n = 0
        if (not len(todaydata["lessons"])):
            messageforuser = "Завтра не запланироавно никаких уроков =("

        for i in range(len(todaydata["lessons"])):
            if (i+1<len(todaydata["lessons"])):
                if (todaydata["lessons"][i-1]["number"] == todaydata["lessons"][i]["number"]):
                    n += 1
                elif (todaydata["lessons"][i+1]["number"] == todaydata["lessons"][i]["number"]):
                    messageforuser += "\n"
                    messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | " + todaydata["lessons"][i]["subject"] + " | " + "2 группы: " +  todaydata["lessons"][i+1]["auditory"] + ", " + todaydata["lessons"][i]["auditory"] + "каб."
                else:
                    messageforuser += "\n"
                    messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | "  + todaydata["lessons"][i]["subject"] + " | " + todaydata["lessons"][i]["auditory"] + "каб."
            else:
                messageforuser += "\n"
                messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | "  + todaydata["lessons"][i]["subject"] + " | " + todaydata["lessons"][i]["auditory"] + "каб."

        bot.send_message(call.message.chat.id, messageforuser)

@bot.message_handler(commands=['today'])
def send_today(msg):
    responsetoday = requests.get("https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday=" + str(weekday_) + "&group=22")
    todaydata = json.loads(responsetoday.text)
    messageforuser = "Привет! Сегодня у тебя будет такое расписание: \n"
    n = 0
    if (not len(todaydata["lessons"])):
        messageforuser = "Привет! Сегондя не запланироавно никаких уроков =("

    for i in range(len(todaydata["lessons"])):
        if (i+1<len(todaydata["lessons"])):
            if (todaydata["lessons"][i-1]["number"] == todaydata["lessons"][i]["number"]):
                n += 1
            elif (todaydata["lessons"][i+1]["number"] == todaydata["lessons"][i]["number"]):
                messageforuser += "\n"
                messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | " + todaydata["lessons"][i]["subject"] + " | " + "2 группы: " +  todaydata["lessons"][i+1]["auditory"] + ", " + todaydata["lessons"][i]["auditory"] + "каб."
            else:
                messageforuser += "\n"
                messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | "  + todaydata["lessons"][i]["subject"] + " | " + todaydata["lessons"][i]["auditory"] + "каб."
        else:
            messageforuser += "\n"
            messageforuser += lessonsTime[todaydata["lessons"][i]["number"]-1] + " | "  + todaydata["lessons"][i]["subject"] + " | " + todaydata["lessons"][i]["auditory"] + "каб."

    bot.send_message(msg.chat.id, messageforuser)

# Функия, отправляющая всем пользователям расписание на завтра 
def send_messages ():
    response = requests.get("https://lyceum.urfu.ru/?type=11&scheduleType=group&weekday=" + str(weekday_ + 1) + "&group=22")
    data = json.loads(response.text)

    messageforuser = "Привет! " + str(tommorowDate.date())+ " у тебя будет такое расписание: \n"
    n = 0
    if (not len(data["lessons"])):
        messageforuser = "Привет! " + str(tommorowDate.date())+ " не запланироавно никаких уроков =("

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



    for i in joinedUsers: 
        bot.send_message(i, messageforuser)

# Backup
def backup ():
    bot.send_message(926132680, str(joinedUsers))
def printe ():
    print("hello")

# Используем функцию send_messages раз в день, в установленное время, так же отправляем backup мне в тг
def do_schedule ():
    schedule.every().hour.do(backup)
    if (True):
        schedule.every().days.at("07:16").do(printe)
    while True:
        schedule.run_pending()
        time.sleep(1)
    

thread = Thread(target=do_schedule)
thread.start()
bot.polling(non_stop=True)