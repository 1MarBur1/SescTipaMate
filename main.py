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
defaultrequesturl = "https://lyceum.urfu.ru/?type=11&scheduleType=group"

classes = ["8А", "8В", "9В", "9A", "9Б", "11А", "11Б", "11В", "9Е", "", "9Г", "10А", "10Б", "10В", "10Г", "10Д", "10Е", "10З", "10К", "10Л", "10М", "10Н", "10С", "11Г", "11Д", "11Е", "11З", "11К", "11Л", "11М", "11С", "11Н"]

# user = [user_id, group_id, mailing] - модель пользователя
groups = []
joinedUsers = []

def getGroups ():
    global groups

    for i in joinedUsers:
        if i[1] and not i[1] in groups:
            groups.append(i[1])


if (not "testing" in sys.argv):
    joinedFile = open("./ids.txt", "r")
    for line in joinedFile:
        user_id, group, mailing = line.strip().split(",")
        joinedUsers.append([int(user_id), int(group), bool(mailing)])
    joinedFile.close()
    getGroups()

admins = [926132680]

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

def usersHaveUser (user):
    have = False
    for i in joinedUsers:
        if (i[0] == user):
            have = True
            break
    return have

def getUserId (user):
    id = -1

    for i in range(len(joinedUsers)):
        if (joinedUsers[i][0] == user):
            id = i
            break

    return id

@bot.message_handler(commands=['help'])
def help(msg):
    bot.send_message(msg.chat.id, "/start - регистрирует тебя в боте\n/menu - открывает меню, оттуда можно посмотреть расписание на сегодня, завтра, открыть полезные ресуры и т.д.\n/today - отправляет расписание на сегодня\n/tomorrow - отправляет расписание на завтра\n/admin - только для администраторов\n/deactivate - удаляет тебя из рассылки\n/activate - добавляет тебя в рассылку\n/class - выбрать свой класс\n/audiences - список, где находятся аудитории")

@bot.message_handler(commands=['start'])
def send_welcome(msg):
    if not usersHaveUser(msg.chat.id):
        joinedUsers.append([msg.chat.id, 0, True])
       
        bot.send_message(msg.chat.id, f"Привет, {msg.from_user.first_name}! Ты являешься учеником СУНЦ УрФУ! Нужно всегда быть в курсе расписания, теперь я буду помогать с этим =) Но сначала напиши свой класс с помощью /class")
        getGroups()
    else: 
        messageforlogineduser = "Друг, ты уже зарегестрирован и можешь пользоваться ботом!"
        if (msg.chat.id < 0):
            messageforlogineduser = "Эта группа уже зарегестрирована! Если ты хочешь добавить себя это нужно сделать в личных сообщениях"
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
        ids_list += str(i).replace("[", "").replace("]", "").replace(" ", "")
    ids_list += "```"

    if (msg.chat.id in admins):
        bot.send_message(msg.chat.id, ids_list, parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, "У тебя нет админки =/\nЗа ней обращайся к @xmarburx")

@bot.message_handler(commands=['audiences'])
def send_auditories(msg):
    img = open('assets/images/audiences.png', 'rb')
    bot.send_photo(msg.chat.id, img)

@bot.message_handler(commands=['class'])
def send_settings(msg):
    if usersHaveUser(msg.chat.id):
        bot.send_message(msg.chat.id, "Чтобы настроить свой класс просто введи его ниже в фромате '12Я' (если у вас уже был установлен класс он изменится на новый)")

        def get_settings(msg):
            if msg.text.upper() in classes:
                bot.send_message(msg.chat.id, f"Окей, твой класс {msg.text.upper()}, я присвоил его тебе! Теперь ты можешь смотреть расписание")

                joinedUsers[getUserId(msg.chat.id)][1] = classes.index(msg.text.upper()) + 1
                getGroups()
            else:
                bot.send_message(msg.chat.id, "Я не знаю такого класса, попробуй еще раз /class")
        bot.register_next_step_handler(msg, get_settings)
    else:
        bot.send_message(msg.chat.id, "Для настройки тебе нужно зарегистрироваться с помощью /start")

@bot.message_handler(commands=['deactivate'])
def deactivate_mailing(msg):
    if(usersHaveUser(msg.chat.id)):
        joinedUsers[getUserId(msg.chat.id)][2] = False
        bot.send_message(msg.chat.id, "Я удалил тебя, больше не буду присылать тебе сообщения автоматически. Но ты все так же можешь смотреть расписание с помощью /menu")
    else:
        bot.send_message(msg.chat.id, "Ты не подписан на рассылку, поэтому я не могу тебя удалить из нее =)")
@bot.message_handler(commands=['activate'])
def activate_mailing(msg):
    if(usersHaveUser(msg.chat.id) and not joinedUsers[getUserId(msg.chat.id)][2]):
        joinedUsers[getUserId(msg.chat.id)][2] = True
        bot.send_message(msg.chat.id, "Я добавил тебя, теперь буду присылать тебе сообщения автоматически.")
    else:
        bot.send_message(msg.chat.id, "Ты уже подписан на рассылку, поэтому я не могу добавить тебя в нее =)")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if usersHaveUser(call.message.chat.id):
        if joinedUsers[getUserId(call.message.chat.id)][1] != 0:
            if call.data == "openToday":
                responsetoday = requests.get(defaultrequesturl + f"&weekday={weekday_}&group={joinedUsers[getUserId(call.message.chat.id)][1]}")
                
                bot.send_message(call.message.chat.id, formatData(response = responsetoday, date = today.date(), mailing = False))
            if call.data == "openTomorrow":
                responsetomorrow = requests.get(defaultrequesturl + f"&weekday={(weekday_ + 1) % 7}&group={joinedUsers[getUserId(call.message.chat.id)][1]}")

                bot.send_message(call.message.chat.id, formatData(response = responsetomorrow, date = tommorowDate.date(), mailing = False))
        else:
            bot.send_message(call.message.chat.id, "Сначала выбери свой класс, с помощью /class")
    else:
        bot.send_message(call.message.chat.id, "Чтобы получить расписание нужно зарегистрироваться с помощью /start")

@bot.message_handler(commands=['today'])
def send_today(msg):
    if usersHaveUser(msg.chat.id):
        if joinedUsers[getUserId(msg.chat.id)][1] != 0:
            responsetoday = requests.get(defaultrequesturl + f"&weekday={weekday_}&group={joinedUsers[getUserId(msg.chat.id)][1]}")

            bot.send_message(msg.chat.id, formatData(response = responsetoday, date = today.date(), mailing=False))
        else:
            bot.send_message(msg.chat.id, "Сначала выбери свой класс, с помощью /class")
    else:
        bot.send_message(msg.chat.id, "Чтобы получить расписание нужно зарегистрироваться с помощью /start")

@bot.message_handler(commands=['tomorrow'])
def send_tomorrow(msg):
    if usersHaveUser(msg.chat.id):
        if joinedUsers[getUserId(msg.chat.id)][1] != 0:
            responsetomorrow = requests.get(defaultrequesturl + f"&weekday={(weekday_ + 1) % 7}&group={joinedUsers[getUserId(msg.chat.id)][1]}")

            bot.send_message(msg.chat.id, formatData(response = responsetomorrow, date = tommorowDate.date(), mailing=False))
        else:
            bot.send_message(msg.chat.id, "Сначала выбери свой класс, с помощью /class")
    else:
        bot.send_message(msg.chat.id, "Чтобы получить расписание нужно зарегистрироваться с помощью /start")

# Функия, отправляющая всем пользователям расписание на указаную дату 
def send_messages (date, data_weekday):
    responses = [None] * len(classes)
    for group in groups:
        responses[group-1] = requests.get(defaultrequesturl + f"&weekday={data_weekday}&group={group}")
        time.sleep(1)

    for i in joinedUsers: 
        response = responses[i[1]-1]

        if i[1] and i[2]:
            bot.send_message(i[0], formatData(response = response, date = date, mailing=True))


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
        ids_list += str(i).replace("[", "").replace("]", "").replace(" ", "")
    ids_list += "```"

    bot.send_message(926132680, ids_list, parse_mode="Markdown")

# Обновляем все переменные связаные со временем (иначе у бота всегда будет та дата, которая была при запуске)
def update_dates ():
    global today 
    global weekday_ 
    global tommorowDate 

    today = datetime.datetime.today() + datetime.timedelta(hours=5)
    weekday_ = (datetime.datetime.today() + datetime.timedelta(hours=5)).weekday() + 1
    tommorowDate = datetime.datetime.now() + datetime.timedelta(days=1, hours=5)

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