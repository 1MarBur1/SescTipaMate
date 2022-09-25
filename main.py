import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode, Message
from aiogram.utils import exceptions
from aiogram_dialog import Dialog, DialogRegistry, DialogManager, StartMode

from database import database
from format_data import ScheduleProvider, format_schedule
from settings_flow import SettingsStateFlow
from stringi18n import i18n


TEST_BOT_TOKEN = "5445774855:AAEuTHh7w5Byc1Pi2yxMupXE3xkc1o7e5J0"
bot = Bot(token=TEST_BOT_TOKEN, parse_mode=ParseMode.HTML)

# TODO: Redis storage
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)
sp = ScheduleProvider()

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


def current_local_time():
    return datetime.now(tz=ZoneInfo("Asia/Yekaterinburg"))


def get_ids_list():
    ids_list = i18n.string("accounts_amount", amount=len(database.joinedChats))
    ids_list += "```"
    for chat_id in database.joinedChats:
        chat_data = database.get_chat_data(chat_id)
        ids_list += "\n"
        ids_list += ",".join(map(str, [chat_id, chat_data["group"], chat_data["mail"], chat_data["pin"],
                                       chat_data["pinned_message"], chat_data["news"]]))
    ids_list += "```"

    return ids_list


@dispatcher.message_handler(commands=["start"])
async def send_welcome(message: Message):
    chat_id = message.chat.id
    if not database.has_chat(chat_id):
        database.set_chat_data(chat_id, {"group": 0, "mail": True, "pin": False, "pinned_message": -1, "news": True})
        await message.reply(i18n.string("welcome", name=message.chat.first_name))
    else:
        await message.reply(i18n.string(
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
    # TODO: create menu with aiogram_dialog
    # await bot.send_message(message.chat.id, i18n.string("menu_welcome", name=message.from_user.first_name),
    #                        reply_markup=defaultButtons)
    await message.reply("Nothing here yet...")


@dispatcher.message_handler(commands=["audiences"])
async def send_audiences(message: Message):
    with open("assets/images/audiences.png", mode="rb") as image:
        await message.reply_photo(image)


async def send_schedule_for_day(message: Message, date):
    chat_id = message.chat.id
    if database.has_chat(chat_id):
        chat_data = database.get_chat_data(chat_id)
        if chat_data["group"] != 0:
            await message.reply(
                format_schedule(sp.for_group(date.weekday(), chat_data["group"]), date.strftime("%d.%m.%Y")))
        else:
            await message.reply(i18n.string("unselected_group"))
    else:
        await message.reply(i18n.string("unregistered_chat"))


@dispatcher.message_handler(commands=["today"])
async def send_today(message: Message):
    await send_schedule_for_day(message, current_local_time())


@dispatcher.message_handler(commands=["tomorrow"])
async def send_tomorrow(message: Message):
    await send_schedule_for_day(message, current_local_time() + timedelta(days=1))


async def send_mail():
    # TODO:
    #   1) Additional mailing in case of schedule changes
    #   2) Fine time scheduling, not just magic calculations
    #   3) Mail message welcome
    while True:
        now = current_local_time()
        delay = (64800 - (now.hour * 3600 + now.minute * 60 + now.second)) % 86400
        tomorrow = (current_local_time() + timedelta(days=1))
        await asyncio.sleep(delay)
        await sp.fetch_schedule(tomorrow.weekday())
        for chat_id in database.joinedChats:
            chat_data = database.get_chat_data(chat_id)
            try:
                await bot.send_message(
                    chat_id,
                    format_schedule(sp.for_group(tomorrow.weekday(), chat_data["group"]), tomorrow.strftime("%d.%m.%Y"))
                )
            except exceptions.TelegramAPIError:
                # TODO: Properly handle users which cause exceptions.
                #       For example move they down in the list or even delete from mailing.
                pass


@dispatcher.message_handler(commands=["admin"])
async def send_admin_log(message: Message):
    await message.reply(await backup())


async def backup():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        request_data = {
            "api_dev_key": "Hef-B8ICM1nbTI4JTkwid4JbYPmY327E",
            "api_option": "paste",
            "api_paste_code": get_ids_list(),
            "api_paste_private": "0",
        }
        async with session.post("https://pastebin.com/api/api_post.php", data=request_data) as response:
            return await response.text()


async def on_bot_start(_):
    asyncio.get_event_loop().create_task(send_mail())
    await sp.fetch_schedule(current_local_time().weekday())
    await sp.fetch_schedule((current_local_time() + timedelta(days=1)).weekday())


async def on_bot_destroy(_):
    message = await backup()
    await bot.send_message(926132680, message)
    await bot.send_message(423052299, message)


def main():
    logging.basicConfig(level=logging.INFO)
    # init_i18n()

    dialog_registry = DialogRegistry(dispatcher)
    dialog = Dialog(SettingsStateFlow.main_window, SettingsStateFlow.group_window)
    dialog.on_start = SettingsStateFlow.on_start
    dialog_registry.register(dialog)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    executor.start_polling(dispatcher, skip_updates=False, on_startup=on_bot_start, on_shutdown=on_bot_destroy)


if __name__ == "__main__":
    main()
