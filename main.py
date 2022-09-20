import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode, Message
from aiogram_dialog import Dialog, DialogRegistry, DialogManager, StartMode

from database import database
from format_data import ScheduleProvider, format_schedule
from settings_flow import SettingsStateFlow
from stringi18n import i18n


TEST_BOT_TOKEN = "5445774855:AAEuTHh7w5Byc1Pi2yxMupXE3xkc1o7e5J0"
bot = Bot(token=TEST_BOT_TOKEN)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)
dialog_registry = DialogRegistry(dispatcher)
sp = ScheduleProvider()
today = None

admins = [926132680, 423052299]

defaultButtons = types.InlineKeyboardMarkup()
button1 = types.InlineKeyboardButton(i18n.string("menu_today"), callback_data="openToday")
button2 = types.InlineKeyboardButton(i18n.string("menu_tomorrow"), callback_data="openTomorrow")
button_dnevnik = types.InlineKeyboardButton(i18n.string("menu_lycreg"), url='https://lycreg.urfu.ru/')
defaultButtons.add(button1)
defaultButtons.add(button2)
defaultButtons.add(button_dnevnik)


def is_group(chat_id):
    return chat_id < 0


def get_time():
    return datetime.now(ZoneInfo("Asia/Yekaterinburg"))


def get_ids_list():
    ids_list = i18n.string("accounts_amount", amount=len(database.joinedChats))
    ids_list += "```\n"
    for chat in database.joinedChats:
        ids_list += "\n"
        ids_list += str(chat).replace("[", "").replace("]", "").replace(" ", "")
    ids_list += "```"

    return ids_list


@dispatcher.message_handler(commands=["start"])
async def send_welcome(message: Message):
    chat_id = message.chat.id
    if not database.has_chat(chat_id):
        database.set_chat_data(chat_id, {"group": 0, "mail": True, "pin": False, "pinned_message": -1, "news": True})
        await bot.send_message(chat_id, i18n.string("welcome", name=message.chat.first_name), parse_mode="markdown")
    else:
        await bot.send_message(chat_id, i18n.string(
            "group_already_registered" if is_group(chat_id) else "user_already_registered"
        ))


@dispatcher.message_handler(commands=["help"])
async def send_help(message: Message):
    await message.reply(i18n.string("help"))


@dispatcher.message_handler(commands=["settings"])
async def manage_settings(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(SettingsStateFlow.main_state, mode=StartMode.RESET_STACK)
    await message.delete()


@dispatcher.message_handler(commands=["menu"])
async def open_menu(message: Message):
    await bot.send_message(message.chat.id, i18n.string("menu_welcome", name=message.from_user.first_name),
                           reply_markup=defaultButtons)


@dispatcher.message_handler(commands=["audiences"])
async def send_audiences(message: Message):
    with open("assets/images/audiences.png", mode="rb") as image:
        await bot.send_photo(message.chat.id, image)


@dispatcher.message_handler(commands=["today"])
async def send_today(message: Message):
    chat_id = message.chat.id
    if database.has_chat(chat_id):
        chat_data = database.get_chat_data(chat_id)
        if chat_data["group"] != 0:
            await bot.send_message(
                chat_id,
                format_schedule(sp.for_group(get_time().weekday(), chat_data["group"]), get_time().date()),
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await bot.send_message(chat_id, i18n.string("unselected_group"))
    else:
        await bot.send_message(chat_id, i18n.string("unregistered_chat"))


@dispatcher.message_handler(commands=["tomorrow"])
async def send_tomorrow(message: Message):
    ...


def backup():
    bot.send_message(926132680, get_ids_list(), parse_mode="markdown")


def scheduler():
    # aioschedule.every().hour.do(backup)
    aioschedule.every().days.at("13:00").do(...)
    aioschedule.every().days.at("02:00").do(...)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # init_i18n()
    # sp.fetch_schedule(get_time().weekday())

    dialog = Dialog(SettingsStateFlow.main_window, SettingsStateFlow.group_window)
    dialog.on_start = SettingsStateFlow.on_start
    dialog_registry.register(dialog)

    executor.start_polling(dispatcher, skip_updates=False)
