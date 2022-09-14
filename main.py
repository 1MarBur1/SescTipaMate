import logging
import zoneinfo
from zoneinfo import ZoneInfo
from datetime import datetime
import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, executor, types

from dialog import Dialog
from format_data import ScheduleProvider, format_schedule

TEST_BOT_TOKEN = "5445774855:AAEuTHh7w5Byc1Pi2yxMupXE3xkc1o7e5J0"
bot = Bot(token=TEST_BOT_TOKEN)
dispatcher = Dispatcher(bot)
dialog = Dialog("ru")
sp = ScheduleProvider()
today = None

admins = [926132680, 423052299]
joinedChats = {}

defaultButtons = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton(dialog.message("menu_today"), callback_data="openToday")
button2 = types.InlineKeyboardButton(dialog.message("menu_tomorrow"), callback_data="openTomorrow")
button_dnevnik = types.InlineKeyboardButton(dialog.message("menu_lycreg"), url='https://lycreg.urfu.ru/')
defaultButtons.add(button1)
defaultButtons.add(button2)
defaultButtons.add(button_dnevnik)


def is_group(chat_id):
    return chat_id < 0


def get_time():
    return datetime.now(ZoneInfo("Asia/Yekaterinburg"))


def get_ids_list():
    ids_list = dialog.message("accounts_amount", amount=len(joinedChats))
    ids_list += "```\n"
    for chat in joinedChats:
        ids_list += "\n"
        ids_list += str(chat).replace("[", "").replace("]", "").replace(" ", "")
    ids_list += "```"

    return ids_list


@dispatcher.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in joinedChats:
        joinedChats[chat_id] = [0, True, False, -1, True]
        await bot.send_message(chat_id, dialog.message("welcome", name=message.chat.first_name), parse_mode="markdown")
    else:
        await bot.send_message(chat_id, dialog.message(
            "group_already_registered" if is_group(chat_id) else "user_already_registered"
        ))


@dispatcher.message_handler(commands=["help"])
async def send_help(message: types.Message):
    await message.reply(dialog.message("help"))


@dispatcher.message_handler(commands=["menu"])
async def open_menu(message: types.Message):
    await bot.send_message(message.chat.id,  dialog.message("menu_welcome", name=message.from_user.first_name),
                           reply_markup=defaultButtons)


@dispatcher.message_handler(commands=["audiences"])
async def send_audiences(message: types.Message):
    with open("assets/images/audiences.png", mode="rb") as image:
        await bot.send_photo(message.chat.id, image)


@dispatcher.message_handler(commands=["today"])
async def send_today(message: types.Message):
    chat_id = message.chat.id
    if chat_id in joinedChats:
        if joinedChats[chat_id][1] != 0:
            await bot.send_message(
                chat_id,
                format_schedule(sp.for_group(get_time().weekday(), joinedChats[chat_id][1]), get_time().date()),
                parse_mode="markdown"
            )
        else:
            await bot.send_message(chat_id, dialog.message("unselected_group"))
    else:
        await bot.send_message(chat_id, dialog.message("unregistered_chat"))


@dispatcher.message_handler(commands=["tomorrow"])
async def send_tomorrow(message: types.Message):
    ...


def backup():
    bot.send_message(926132680, get_ids_list(), parse_mode="markdown")


def scheduler():
    # aioschedule.every().hour.do(backup)
    aioschedule.every().days.at("13:00").do(...)
    aioschedule.every().days.at("02:00").do(...)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sp.fetch_schedule(get_time().weekday())

    executor.start_polling(dispatcher, skip_updates=False)
