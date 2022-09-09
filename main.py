import schedule
import time
import telebot
from telebot import types
import datetime
import requests
import sys
from threading import Thread

from dialog import Dialog
from format_data import format_data

dialog = Dialog("ru")

today = datetime.datetime.today() + datetime.timedelta(hours=5)
weekday_ = (datetime.datetime.today() + datetime.timedelta(hours=5)).weekday() + 1
tomorrowDate = datetime.datetime.today() + datetime.timedelta(days=1, hours=5)
default_request_url = "https://lyceum.urfu.ru/?type=11&scheduleType=group"

classes = ["8А", "8В", "9В", "9A", "9Б", "11А", "11Б", "11В", "9Е", "", "9Г", "10А", "10Б", "10В", "10Г", "10Д", "10Е",
           "10З", "10К", "10Л", "10М", "10Н", "10С", "11Г", "11Д", "11Е", "11З", "11К", "11Л", "11М", "11С", "11Н"]

# user = [user_id, group_id, mailing, pinning] - модель пользователя
groups = []
joinedUsers = []


def get_groups():
    global groups

    for i in joinedUsers:
        if i[1] and not i[1] in groups:
            groups.append(i[1])


# if (not "testing" in sys.argv):
joinedFile = open("./ids.txt", "r")
for line in joinedFile:
    user_id, group, mailing, pinning = line.strip().split(",")
    joinedUsers.append([int(user_id), int(group), mailing == "True", pinning == "True"])
joinedFile.close()
get_groups()

admins = [926132680, 423052299]

if "testing" in sys.argv:
    bot = telebot.TeleBot("5445774855:AAEuTHh7w5Byc1Pi2yxMupXE3xkc1o7e5J0")
else:
    bot = telebot.TeleBot("5435533576:AAERV3w9cDsGraZ8DiTCjG2AMjva8vD9Wo8")

defaultButtons = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton(dialog.message("menu_today"), callback_data="openToday")
button2 = types.InlineKeyboardButton(dialog.message("menu_tomorrow"), callback_data="openTomorrow")
button_dnevnik = types.InlineKeyboardButton(dialog.message("menu_lycreg"), url='https://lycreg.urfu.ru/')
defaultButtons.add(button1)
defaultButtons.add(button2)
defaultButtons.add(button_dnevnik)


def users_have_user(user):
    have = False
    for i in joinedUsers:
        if i[0] == user:
            have = True
            break
    return have


def get_user_id(user):
    id = -1
    for i in range(len(joinedUsers)):
        if joinedUsers[i][0] == user:
            id = i
            break

    return id


@bot.message_handler(commands=['help'])
def help_message(msg):
    bot.send_message(msg.chat.id, dialog.message("help"))


@bot.message_handler(commands=['start'])
def send_welcome(msg):
    if not users_have_user(msg.chat.id):
        joinedUsers.append([msg.chat.id, 0, True, False])

        bot.send_message(msg.chat.id, dialog.message("welcome", name=msg.from_user.first_name))
        get_groups()
    else:
        message_for_registered_user = \
            dialog.message("group_already_registered" if msg.chat.id < 0 else "user_already_registered")
        bot.send_message(msg.chat.id, message_for_registered_user)


@bot.message_handler(commands=['menu'])
def open_menu(msg):
    bot.send_message(msg.chat.id, dialog.message("menu_welcome", name=msg.from_user.first_name),
                     reply_markup=defaultButtons)


def get_ids_list():
    ids_list = dialog.message("accounts_amount", amount=len(joinedUsers))
    ids_list += "```\n"
    for i in joinedUsers:
        ids_list += "\n"
        ids_list += str(i).replace("[", "").replace("]", "").replace(" ", "")
    ids_list += "```"

    return ids_list


@bot.message_handler(commands=['admin'])
def open_admin(msg):
    ids_list = get_ids_list()
    if msg.chat.id in admins:
        bot.send_message(msg.chat.id, ids_list, parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, dialog.message("you_are_not_admin"))


@bot.message_handler(commands=['audiences'])
def send_audiences(msg):
    img = open('assets/images/audiences.png', mode='rb')
    bot.send_photo(msg.chat.id, img)


@bot.message_handler(commands=['class'])
def send_settings(msg):
    if users_have_user(msg.chat.id):
        bot.send_message(msg.chat.id, dialog.message("settings_help"))

        def get_settings(msg):
            if msg.text.upper() in classes:
                bot.send_message(msg.chat.id, dialog.message("group_selected", group=msg.text.upper()))

                joinedUsers[get_user_id(msg.chat.id)][1] = classes.index(msg.text.upper()) + 1
                get_groups()
            else:
                bot.send_message(msg.chat.id, dialog.message("unknown_group"))
        bot.register_next_step_handler(msg, get_settings)
    else:
        bot.send_message(msg.chat.id, dialog.message("unregistered_user"))


@bot.message_handler(commands=['pinning'])
def toggle_pinning (msg):
    joinedUsers[get_user_id(msg.chat.id)][3] = not joinedUsers[get_user_id(msg.chat.id)][3]
    pinned_message = " не"
    if joinedUsers[get_user_id(msg.chat.id)][3]:
        pinned_message = ""

    bot.send_message(msg.chat.id, f"Теперь я{pinned_message} буду закреплять рассылки")


@bot.message_handler(commands=['deactivate'])
def deactivate_mailing(msg):
    if users_have_user(msg.chat.id):
        joinedUsers[get_user_id(msg.chat.id)][2] = False
        bot.send_message(msg.chat.id, dialog.message("mail_deactivated"))
    else:
        bot.send_message(msg.chat.id, dialog.message("mail_already_deactivated"))


@bot.message_handler(commands=['activate'])
def activate_mailing(msg):
    if users_have_user(msg.chat.id) and not joinedUsers[get_user_id(msg.chat.id)][2]:
        joinedUsers[get_user_id(msg.chat.id)][2] = True
        bot.send_message(msg.chat.id, dialog.message("mail_activated"))
    else:
        bot.send_message(msg.chat.id, dialog.message("mail_already_activated"))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if users_have_user(call.message.chat.id):
        if joinedUsers[get_user_id(call.message.chat.id)][1] != 0:
            if call.data == "openToday":
                response_today = requests.get(default_request_url + f"&weekday={weekday_}&group={joinedUsers[get_user_id(call.message.chat.id)][1]}")
                bot.send_message(call.message.chat.id, format_data(response=response_today, date=today.date(), mailing=False, dialog=dialog))
            if call.data == "openTomorrow":
                response_tomorrow = requests.get(default_request_url + f"&weekday={(weekday_ + 1) % 7}&group={joinedUsers[get_user_id(call.message.chat.id)][1]}")
                bot.send_message(call.message.chat.id, format_data(response=response_tomorrow, date=tomorrowDate.date(), mailing=False, dialog=dialog))
        else:
            bot.send_message(call.message.chat.id, dialog.message("unselected_group"))
    else:
        bot.send_message(call.message.chat.id, dialog.message("unregistered_user"))


@bot.message_handler(commands=['today'])
def send_today(msg):
    if users_have_user(msg.chat.id):
        if joinedUsers[get_user_id(msg.chat.id)][1] != 0:
            response_today = requests.get(default_request_url + f"&weekday={weekday_}&group={joinedUsers[get_user_id(msg.chat.id)][1]}")
            bot.send_message(msg.chat.id, format_data(response=response_today, date=today.date(), mailing=False, dialog=dialog))
        else:
            bot.send_message(msg.chat.id, dialog.message("unselected_group"))
    else:
        bot.send_message(msg.chat.id, dialog.message("unregistered_user"))


@bot.message_handler(commands=['tomorrow'])
def send_tomorrow(msg):
    if users_have_user(msg.chat.id):
        if joinedUsers[get_user_id(msg.chat.id)][1] != 0:
            response_tomorrow = requests.get(default_request_url + f"&weekday={(weekday_ + 1) % 7}&group={joinedUsers[get_user_id(msg.chat.id)][1]}")
            bot.send_message(msg.chat.id, format_data(response=response_tomorrow, date=tomorrowDate.date(), mailing=False, dialog=dialog))
        else:
            bot.send_message(msg.chat.id, dialog.message("unselected_group"))
    else:
        bot.send_message(msg.chat.id, dialog.message("unregistered_user"))


# Функия, отправляющая всем пользователям расписание на указаную дату
def send_messages(date, data_weekday):
    responses = [None] * len(classes)
    for group in groups:
        responses[group - 1] = requests.get(default_request_url + f"&weekday={data_weekday}&group={group}")
    for i in joinedUsers:
        response = responses[i[1] - 1]
        if i[1] and i[2]:
            message_ = bot.send_message(i[0], format_data(response=response, date=date, mailing=True, dialog=dialog))
            if i[3]:
                bot.pin_chat_message(i[0], message_.message_id)


def send_today_mail():
    if weekday_ != 7:
        send_messages(date=today.date(), data_weekday=weekday_)


def send_tomorrow_mail():
    if weekday_ != 6:
        send_messages(date=tomorrowDate.date(), data_weekday=(weekday_ + 1) % 7)


# Backup
def backup():
    bot.send_message(926132680, get_ids_list(), parse_mode="Markdown")


# Обновляем все переменные связаные со временем (иначе у бота всегда будет та дата, которая была при запуске)
def update_dates():
    global today, weekday_, tomorrowDate

    today = datetime.datetime.today() + datetime.timedelta(hours=5)
    weekday_ = (datetime.datetime.today() + datetime.timedelta(hours=5)).weekday() + 1
    tomorrowDate = datetime.datetime.now() + datetime.timedelta(days=1, hours=5)


# Здесь устанавливаем всякие таймера на апдейт переменных раз в день, время рассылок и т.д.
def do_schedule():
    schedule.every().hour.do(backup)
    schedule.every().days.at("19:00").do(update_dates)
    schedule.every().days.at("14:15").do(send_tomorrow_mail)
    schedule.every().days.at("02:00").do(send_today_mail)
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    thread = Thread(target=do_schedule)
    thread.start()
    bot.polling(non_stop=True)


if __name__ == "__main__":
    main()
