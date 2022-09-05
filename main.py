import schedule
import time
import telebot
from telebot import types
import datetime
import requests
import sys
from threading import Thread

from format_data import formatData

today = datetime.datetime.today() + datetime.timedelta(hours=5)
weekday_ = (datetime.datetime.today() + datetime.timedelta(hours=5)).weekday() + 1
tommorowDate = datetime.datetime.today() + datetime.timedelta(days=1, hours=5)
defaultrequesturl = "https://lyceum.urfu.ru/?type=11&scheduleType=group&group=22"

joinedUsers = set()
if (not "testing" in sys.argv):
    joinedFile = open("./ids.txt", "r")
    for line in joinedFile:
        joinedUsers.add(int(line.strip()))
    joinedFile.close()

admins = [926132680, 1145867325, 5027348167]

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
        messageforlogineduser = "Друг, ты уже есть в моих списках, не переживай, я тебя оповещу!"
        if (msg.chat.id < 0):
            messageforlogineduser = "Эта группа уже добавлена! Если ты хочешь добавить себя это нужно сделать в личных сообщениях"
        bot.send_message(msg.chat.id, messageforlogineduser)

@bot.message_handler(commands=['menu'])
def open_menu(msg):
    bot.send_message(msg.chat.id, f"Привет, {msg.from_user.first_name}! Ты в самой невероятной менюшке этого города", reply_markup=defaultButtons)

@bot.message_handler(commands=['admin'])
def open_admin(msg):
    ids_list = f"Сейчас в боте {len(joinedUsers)} аккаунтов:\n"
    ids_list += "```\n"
    for i in joinedUsers:
        ids_list += "\n"
        ids_list += str(i)
    ids_list += "```"

    if (msg.chat.id in admins):
        bot.send_message(msg.chat.id, ids_list, parse_mode="Markdown")
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
        responsetoday = requests.get(defaultrequesturl + f"&weekday={weekday_}")
        
        bot.send_message(call.message.chat.id, formatData(response = responsetoday, date = today.date(), mailing = False))
    if call.data == "openTomorrow":
        responsetomorrow = requests.get(defaultrequesturl + f"&weekday={(weekday_ + 1) % 7}")

        bot.send_message(call.message.chat.id, formatData(response = responsetomorrow, date = tommorowDate.date(), mailing = False))

@bot.message_handler(commands=['today'])
def send_today(msg):
    responsetoday = requests.get(defaultrequesturl + f"&weekday={weekday_}")

    bot.send_message(msg.chat.id, formatData(response = responsetoday, date = today.date(), mailing=False))

@bot.message_handler(commands=['tomorrow'])
def send_tomorrow(msg):
    responsetomorrow = requests.get(defaultrequesturl + f"&weekday={(weekday_ + 1) % 7}")

    bot.send_message(msg.chat.id, formatData(response = responsetomorrow, date = tommorowDate.date(), mailing=False))

# Функия, отправляющая всем пользователям расписание на указаную дату 
def send_messages (date, data_weekday):
    response = requests.get(defaultrequesturl + f"&weekday={data_weekday}")

    for i in joinedUsers: 
        bot.send_message(i, formatData(response = response, date = date, mailing=True))


def send_today_mail():
    send_messages(date = today.date(), data_weekday=weekday_)

def send_tommorow_mail():
    send_messages(date = tommorowDate.date(), data_weekday=(weekday_+1)%7)

# Backup
def backup ():
    ids_list = f"Сейчас в боте {len(joinedUsers)} аккаунтов:\n"
    ids_list += "```\n"
    for i in joinedUsers:
        ids_list += "\n"
        ids_list += str(i)
    ids_list += "```"

    bot.send_message(926132680, ids_list, parse_mode="Markdown")

# Обновляем все переменные связаные со временем (иначе у бота всегда будет та дата, которая была при запуске)
def update_dates ():
    global today 
    global weekday_ 
    global tommorowDate 

    today = datetime.datetime.today() + datetime.timedelta(hours=5)
    weekday_ = (datetime.datetime.today() + datetime.timedelta(hours=5)).weekday() + 1
    tommorowDate = datetime.datetime.now() + datetime.timedelta(days=1)

# Здесь устанавливаем всякие таймера на апдейт переменных раз в день, время рассылок и т.д.
def do_schedule ():
    schedule.every().hour.do(backup)
    schedule.every().days.at("19:00").do(update_dates)

    if weekday_ != 6:
        schedule.every().days.at("13:00").do(send_tommorow_mail)
    if weekday_ != 7:
        schedule.every().days.at("02:00").do(send_today_mail)
    while True:
        schedule.run_pending()
        time.sleep(1)
    

thread = Thread(target=do_schedule)
thread.start()
bot.polling(non_stop=True)