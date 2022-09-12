import schedule
import time
import datetime
import sys
from threading import Thread
from telebot import types, TeleBot
from dotenv import load_dotenv
import os

if "testing" not in sys.argv:
    load_dotenv()
    auth_token = os.getenv('token')

from dialog import Dialog
from format_data import ScheduleProvider, format_schedule

dialog = Dialog("ru")
sp = ScheduleProvider()

today = datetime.datetime.today() + datetime.timedelta(hours=5)
weekday_ = (datetime.datetime.today() + datetime.timedelta(hours=5)).weekday() + 1
tomorrowDate = datetime.datetime.today() + datetime.timedelta(days=1, hours=5)

classes = ["8А", "8В", "9В", "9A", "9Б", "11А", "11Б", "11В", "9Е", "", "9Г", "10А", "10Б", "10В", "10Г", "10Д", "10Е",
           "10З", "10К", "10Л", "10М", "10Н", "10С", "11Г", "11Д", "11Е", "11З", "11К", "11Л", "11М", "11С", "11Н"]

# user = [user_id, group_id, mailing, pinning, pinned_message, get_news] - модель пользователя
groups = []
joinedUsers = []
votingTrue = []
votingFalse = []

def extract_arg(arg):
    return arg[arg.find(" ")::]


def get_groups():
    global groups

    for i in joinedUsers:
        if i[1] and not i[1] in groups:
            groups.append(i[1])


if "testing" not in sys.argv:
    joinedFile = open("./ids.txt", "r")
    for line in joinedFile:
        user_id, group, mailing, pinning, pinned_message, get_news = line.strip().split(",")
        joinedUsers.append([int(user_id), int(group), mailing == "True", pinning == "True", int(pinned_message), get_news == "True"])
    joinedFile.close()
    get_groups()

admins = [926132680, 423052299]

if "testing" in sys.argv:
    bot = TeleBot("5445774855:AAEuTHh7w5Byc1Pi2yxMupXE3xkc1o7e5J0")
else:
    bot = TeleBot(auth_token)

defaultButtons = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton(dialog.message("menu_today"), callback_data="openToday")
button2 = types.InlineKeyboardButton(dialog.message("menu_tomorrow"), callback_data="openTomorrow")
button_dnevnik = types.InlineKeyboardButton(dialog.message("menu_lycreg"), url='https://lycreg.urfu.ru/')
defaultButtons.add(button1)
defaultButtons.add(button2)
defaultButtons.add(button_dnevnik)

votingButtons = types.InlineKeyboardMarkup()
buttontrue = types.InlineKeyboardButton("Сейчас лучше!", callback_data="votingTrue")
buttonfalse = types.InlineKeyboardButton("Раньше было лучше!",  callback_data="votingFalse")
votingButtons.add(buttontrue)
votingButtons.add(buttonfalse)


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
        joinedUsers.append([msg.chat.id, 0, True, False, -1, True])

        bot.send_message(msg.chat.id, dialog.message("welcome", name=msg.from_user.first_name))
        get_groups()
    else:
        message_for_registered_user = dialog.message("group_already_registered" if msg.chat.id < 0 else "user_already_registered")
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
        bot.send_message(msg.chat.id, ids_list, parse_mode="markdown")
    else:
        bot.send_message(msg.chat.id, dialog.message("you_are_not_admin"))


@bot.message_handler(commands=['announcement'])
def announcement(msg):
    if msg.chat.id in admins:
        for i in joinedUsers:
            if i[5]:
                # FIXME: Handle users who blocked bot
                try:
                    bot.send_message(i[0], extract_arg(msg.text))
                except Exception:
                    continue
    else:
        bot.send_message(msg.chat.id, dialog.message("you_are_not_admin"), parse_mode="Markdown")


for i in joinedUsers:
    try:
        bot.send_message(i[0], "Привет! Как ты мог(ла) заметить, дизайн слегка изменился. Мнения разошлись. Кому-то нравится, кто-то говорит, что очень неудобно =( Что думаешь? Нажми кнопку ниже, чтобы проголосовать. А если у тебя есть какое-то предложение, то напиши @xmarburx", reply_markup=votingButtons)
    except Exception:
        continue


@bot.message_handler(commands=['audiences'])
def send_audiences(msg):
    img = open('assets/images/audiences.png', mode='rb')
    bot.send_photo(msg.chat.id, img)


@bot.message_handler(commands=['settings'])
def return_settings(msg):
    if users_have_user(msg.chat.id):
        settings = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(dialog.message("settings_class"), callback_data="settingClass")
        button2 = types.InlineKeyboardButton(dialog.message("settings_mailing"), callback_data="settingMailing")
        button3 = types.InlineKeyboardButton(dialog.message("settings_pinning"), callback_data="settingPinning")
        button4 = types.InlineKeyboardButton(dialog.message("settings_news"), callback_data="settingNews")
        settings.add(button1)
        settings.add(button2)
        settings.add(button3)
        settings.add(button4)
        bot.send_message(msg.chat.id, dialog.message("settings_welcome"), reply_markup=settings)
    else:
        bot.send_message(msg.chat.id, dialog.message("unregistered_user"))


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if users_have_user(call.message.chat.id):
        if call.data == "settingClass":
            bot.send_message(call.message.chat.id, dialog.message("settings_help"))

            def get_settings(msg):
                if msg.text.upper() in classes:
                    bot.send_message(msg.chat.id, dialog.message("group_selected", group=msg.text.upper()))

                    joinedUsers[get_user_id(msg.chat.id)][1] = classes.index(msg.text.upper()) + 1
                    get_groups()
                else:
                    bot.send_message(msg.chat.id, dialog.message("unknown_group"))
            bot.register_next_step_handler(call.message, get_settings)

        elif call.data == "settingMailing":
            joinedUsers[get_user_id(call.message.chat.id)][2] = not joinedUsers[get_user_id(call.message.chat.id)][2]

            if joinedUsers[get_user_id(call.message.chat.id)][2]:
                bot.send_message(call.message.chat.id, dialog.message("mail_activated"))
            else:
                bot.send_message(call.message.chat.id, dialog.message("mail_deactivated"))

        elif call.data == "settingPinning":
            joinedUsers[get_user_id(call.message.chat.id)][3] = not joinedUsers[get_user_id(call.message.chat.id)][3]
            pinned_message = " не"
            if joinedUsers[get_user_id(call.message.chat.id)][3]:
                pinned_message = ""

            bot.send_message(call.message.chat.id, f"Теперь я{pinned_message} буду закреплять рассылки")

        elif call.data == "settingNews":
            joinedUsers[get_user_id(call.message.chat.id)][5] = not joinedUsers[get_user_id(call.message.chat.id)][5]
            pinned_message = " не"
            if joinedUsers[get_user_id(call.message.chat.id)][5]:
                pinned_message = ""

            bot.send_message(call.message.chat.id, f"Теперь я{pinned_message} буду присылать тебе уведомления об обновлениях бота")

        elif call.data == "votingTrue":
            if not (call.message.chat.id in votingTrue or call.message.chat.id in votingFalse):
                votingTrue.append(call.message.chat.username)
                bot.send_message(
                    call.message.chat.id,
                    "Спасибо за твой отзыв!"
                )
            else:
                bot.send_message(
                    call.message.chat.id,
                    "Ты уже проголосовал!"
                )
        elif call.data == "votingFalse":
            if not (call.message.chat.id in votingTrue or call.message.chat.id in votingFalse):
                votingFalse.append(call.message.chat.username)
                bot.send_message(
                    call.message.chat.id,
                    "Спасибо за твой отзыв!"
                )
            else:
                bot.send_message(
                    call.message.chat.id,
                    "Ты уже проголосовал!"
                )

        else:
            if joinedUsers[get_user_id(call.message.chat.id)][1] != 0:
                if call.data == "openToday":
                    bot.send_message(
                        call.message.chat.id,
                        format_schedule(sp.for_group(weekday_, joinedUsers[get_user_id(call.message.chat.id)][1]),
                                        today.date()),
                        parse_mode="markdown"
                    )
                elif call.data == "openTomorrow":
                    bot.send_message(
                        call.message.chat.id,
                        format_schedule(
                            sp.for_group(weekday_ % 7 + 1, joinedUsers[get_user_id(call.message.chat.id)][1]),
                            tomorrowDate.date()),
                        parse_mode="markdown"
                    )
            else:
                bot.send_message(call.message.chat.id, dialog.message("unselected_group"))
    else:
        bot.send_message(call.message.chat.id, dialog.message("unregistered_user"))


@bot.message_handler(commands=['getvote'])
def get_vote(msg):
    if msg.chat.id in admins:
        bot.send_message(msg.chat.id, f"За: {len(votingTrue)}\n{votingTrue}\n\nПротив: {len(votingFalse)}\n{votingFalse}")
    else:
        bot.send_message(msg.chat.id, dialog.message("you_are_not_admin"))


@bot.message_handler(commands=['today'])
def send_today(msg):
    if users_have_user(msg.chat.id):
        if joinedUsers[get_user_id(msg.chat.id)][1] != 0:
            bot.send_message(
                msg.chat.id,
                format_schedule(sp.for_group(weekday_, joinedUsers[get_user_id(msg.chat.id)][1]), today.date()),
                parse_mode="markdown"
            )
        else:
            bot.send_message(msg.chat.id, dialog.message("unselected_group"))
    else:
        bot.send_message(msg.chat.id, dialog.message("unregistered_user"))


@bot.message_handler(commands=['tomorrow'])
def send_tomorrow(msg):
    if users_have_user(msg.chat.id):
        if joinedUsers[get_user_id(msg.chat.id)][1] != 0:
            bot.send_message(
                msg.chat.id,
                format_schedule(sp.for_group(weekday_ % 7 + 1, joinedUsers[get_user_id(msg.chat.id)][1]), tomorrowDate.date()),
                parse_mode="markdown"
            )
        else:
            bot.send_message(msg.chat.id, dialog.message("unselected_group"))
    else:
        bot.send_message(msg.chat.id, dialog.message("unregistered_user"))


# Функия, отправляющая всем пользователям расписание на указаную дату
def send_mail(data_weekday, date):
    for user in joinedUsers:
        if user[1] and user[2]:
            # FIXME: Handle users who blocked bot
            try:
                message = bot.send_message(user[0], format_schedule(sp.for_group(data_weekday, user[1]), date),
                                           parse_mode="markdown")
                if user[3]:
                    if user[4] != -1:
                        bot.unpin_chat_message(user[0], user[4])

                    bot.pin_chat_message(user[0], message.message_id)
                    user[4] = message.message_id
            except Exception:
                continue


def send_today_mail():
    sp.fetch_schedule(weekday_)
    if weekday_ != 7:
        send_mail(weekday_, today.date())


def send_tomorrow_mail():
    sp.fetch_schedule(weekday_ % 7 + 1)
    if weekday_ != 6:
        send_mail(weekday_ % 7 + 1, tomorrowDate.date())


# Backup
def backup():
    bot.send_message(926132680, get_ids_list(), parse_mode="markdown")


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
    schedule.every().days.at("13:00").do(send_tomorrow_mail)
    schedule.every().days.at("02:00").do(send_today_mail)

    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    sp.fetch_schedule(weekday_)
    sp.fetch_schedule(weekday_ % 7 + 1)

    thread = Thread(target=do_schedule)
    thread.start()
    bot.polling(non_stop=True)


if __name__ == "__main__":
    main()
