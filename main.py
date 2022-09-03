import schedule
import time
import json
import telebot
from telebot import types
import datetime
import requests
import sys
from threading import Thread

now = datetime.datetime.now()
weekday_ = datetime.datetime.today().weekday() + 1
tommorowDate = datetime.datetime.today() + datetime.timedelta(days=1)

joinedUsers = set()
if (not "testing" in sys.argv):
    joinedFile = open("./ids.txt", "r")
    for line in joinedFile:
        joinedUsers.add(int(line.strip()))
    joinedFile.close()

admins = [926132680]
lessonsTime = ("9:00-9:40", "9:50-10:30", "10:45-11:25", "11:40-12:20", "12:35-13:15", "13:35-14:15", "14:35-15:15")

if ("testing" in sys.argv):
    bot = telebot.TeleBot("5445774855:AAEuTHh7w5Byc1Pi2yxMupXE3xkc1o7e5J0")
else:
    bot = telebot.TeleBot("5435533576:AAERV3w9cDsGraZ8DiTCjG2AMjva8vD9Wo8")

defaultButtons = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton("Посмотреть расписание на сегодня", callback_data="openToday")
button2 = types.InlineKeyboardButton("Посмотреть расписание на завтра", callback_data="openTomorrow")
button_dnevnik = types.InlineKeyboardButton("Открыть эл. дневник", url='https://lycreg.urfu.ru/')
defaultButtons.add(button1)
defaultButtons.add(button2)
defaultButtons.add(button_dnevnik)

@bot.message_handler(commands=['help'])
def help(msg):
    bot.send_message(msg.chat.id, "/start - добавляет тебя в рассылку\n/menu - открывает меню, оттуда можно посмотреть расписание на сегодня, завтра, открыть полезные ресуры и т.д.\n/today - отправляет расписание на сегодня\n/admin - только для администраторов\n/deactivate - удаляет тебя из рассылки")

@bot.message_handler(commands=['start'])
def send_welcome(msg):
    if not (msg.chat.id in joinedUsers):
        joinedUsers.add(msg.chat.id)
       
        bot.send_message(msg.chat.id, f"Привет, {msg.from_user.first_name}! Ты являешься учеником СУНЦ УрФУ! Нужно всегда быть в курсе расписания, теперь я буду помогать с этим =)")
    else: 
        bot.send_message(msg.chat.id, "Друг, ты уже есть в моих списках, не переживай, я тебя оповещу!")

@bot.message_handler(commands=['menu'])
def open_menu(msg):
    bot.send_message(msg.chat.id, f"Привет, {msg.from_user.first_name}! Ты в самой невероятной менюшке этого города", reply_markup=defaultButtons)

@bot.message_handler(commands=['admin'])
def open_adming(msg):
    if (msg.chat.id in admins):
        bot.send_message(msg.chat.id, str(joinedUsers))
    else:
        bot.send_message(msg.chat.id, "У тебя нет админки =/\nЗа ней обращайся к @xmarburx")

@bot.message_handler(commands=['deactivate'])
def deactivate_mailing(msg):
    if(msg.chat.id in joinedUsers):
        joinedUsers.remove(msg.chat.id)
        bot.send_message(msg.chat.id, "Я удалил тебя, больше не буду присылать тебе сообщения автоматически. Но ты все так же можешь смотреть расписание с помощью /menu")
    else:
        bot.send_message(msg.chat.id, "Ты не подписан на рассылку, поэтому я не могу тебя удалить из нее =)")

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

    messageforuser = "Привет! Я к тебе с рассылкой, " + str(tommorowDate.date())+ " у тебя будет такое расписание: \n"
    n = 0
    if (not len(data["lessons"])):
        messageforuser = "Привет! Я к тебе с рассылкой, " + str(tommorowDate.date())+ " не запланироавно никаких уроков =("

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

# Используем функцию send_messages раз в день, в установленное время, так же отправляем backup мне в тг
def do_schedule ():
    schedule.every().hour.do(backup)
    if (weekday_ != 6):
        schedule.every().days.at("13:00").do(send_messages)
    while True:
        schedule.run_pending()
        time.sleep(1)
    

thread = Thread(target=do_schedule)
thread.start()
bot.polling(non_stop=True)