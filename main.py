import asyncio
import logging
import os
import sys
from datetime import timedelta
import time

import aiohttp
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode, Message
from aiogram.utils import exceptions
from aiogram_dialog import DialogManager, StartMode
from dotenv import load_dotenv

from database import database
from dialogs import init_dialogs
from format_data import ScheduleProvider, format_schedule
from settings_flow import SettingsStates
from i18n_provider import i18n
from time_utils import current_local_time, everyday_at

load_dotenv()

TEST_TOKEN = "5445774855:AAEuTHh7w5Byc1Pi2yxMupXE3xkc1o7e5J0"
AUTH_TOKEN = None
if "testing" not in sys.argv:
    AUTH_TOKEN = os.getenv("AUTH_TOKEN")
PASTEBIN_AUTH_TOKEN = os.getenv("PASTEBIN_AUTH_TOKEN")

bot = Bot(token=AUTH_TOKEN if AUTH_TOKEN is not None else TEST_TOKEN, parse_mode=ParseMode.HTML)

# TODO: Redis storage
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)
sp = ScheduleProvider()

admins = [926132680, 423052299]


def is_group(chat_id):
    return chat_id < 0


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
    await dialog_manager.start(SettingsStates.main_state, mode=StartMode.RESET_STACK)
    await message.delete()


@dispatcher.message_handler(commands=["menu"])
async def open_menu(message: Message):
    # TODO: create menu with aiogram_dialog

    # defaultButtons = types.InlineKeyboardMarkup()
    # button1 = types.InlineKeyboardButton(i18n.string("menu_today"), callback_data="openToday")
    # button2 = types.InlineKeyboardButton(i18n.string("menu_tomorrow"), callback_data="openTomorrow")
    # button_dnevnik = types.InlineKeyboardButton(i18n.string("menu_lycreg"), url="https://lycreg.urfu.ru/")
    # defaultButtons.add(button1)
    # defaultButtons.add(button2)
    # defaultButtons.add(button_dnevnik)

    # await bot.send_message(message.chat.id, i18n.string("menu_welcome", name=message.from_user.first_name),
    #                        reply_markup=defaultButtons)
    await message.reply("Nothing here yet...")


@dispatcher.message_handler(commands=["audiences"])
async def send_audiences(message: Message):
    with open("assets/audiences.png", mode="rb") as image:
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


@dispatcher.message_handler(commands=["announcement"])
async def send_announcement(message: Message):
    if message.chat.id in admins:
        for chat_id in database.joinedChats:
            chat_data = database.get_chat_data(chat_id)
            if chat_data["mail"]:
                try:
                    await bot.send_message(chat_id, message.text[13:])
                except exceptions.TelegramAPIError:
                    pass
        logging.info("Announcement sent")


@everyday_at("17:07")
async def send_mail_task():
    # TODO:
    #   1) Additional mailing in case of schedule changes
    #   2) Mail message welcome
    tomorrow = current_local_time() + timedelta(days=1)

    if tomorrow.weekday() == 6:
        return

    logging.info(f"Ready to send everyday mailing")
    start_time = time.time()

    await sp.fetch_schedule(tomorrow.weekday())

    success_count = 0
    for chat_id in database.joinedChats:
        chat_data = database.get_chat_data(chat_id)
        if chat_data["mail"]:
            try:
                await bot.send_message(
                    chat_id,
                    format_schedule(sp.for_group(tomorrow.weekday(), chat_data["group"]),
                                    tomorrow.strftime("%d.%m.%Y"))
                )
                success_count += 1
            except exceptions.TelegramAPIError:
                # TODO: Properly handle users which cause exceptions.
                #       For example move they down in the list or even delete from mailing.
                pass

    end_time = time.time()
    logging.info(f"Done in {end_time - start_time}s. Sent to {success_count}/{len(database.joinedChats)} users")


@everyday_at("00:00")
async def everyday_fetch_task():
    logging.info(f"Ready to start everyday sync")
    start_time = time.time()

    await sp.fetch_schedule(current_local_time().weekday())
    await sp.fetch_schedule((current_local_time() + timedelta(days=1)).weekday())

    end_time = time.time()
    logging.info(f"Done in {end_time - start_time}s")


@dispatcher.message_handler(commands=["admin"])
async def send_admin_log(message: Message):
    if message.chat.id in admins:
        await message.reply(await backup())
    else:
        with open("assets/rickroll.gif", mode="rb") as rickroll:
            await message.reply_animation(rickroll)


async def backup():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        request_data = {
            "api_dev_key": PASTEBIN_AUTH_TOKEN,
            "api_option": "paste",
            "api_paste_code": get_ids_list(),
            "api_paste_private": "0",
        }
        async with session.post("https://pastebin.com/api/api_post.php", data=request_data) as response:
            return await response.text()


async def on_bot_start(_):
    logging.info("Starting bot...")

    i18n.load_lang("ru")
    init_dialogs(dispatcher)

    # asyncio.get_event_loop().create_task(send_mail_task())
    asyncio.get_event_loop().create_task(everyday_fetch_task())

    await sp.fetch_schedule(current_local_time().weekday())
    await sp.fetch_schedule((current_local_time() + timedelta(days=1)).weekday())


async def on_bot_destroy(_):
    logging.info("Destroying bot...")

    message = await backup()
    await bot.send_message(926132680, message)
    await bot.send_message(423052299, message)


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s][%(name)s]: %(message)s",
                        datefmt="%d.%m.%y %H:%M:%S")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    executor.start_polling(dispatcher, skip_updates=False, on_startup=on_bot_start, on_shutdown=on_bot_destroy)


if __name__ == "__main__":
    main()
