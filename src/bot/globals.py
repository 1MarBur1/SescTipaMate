import asyncio
import logging
import os
import sys
from datetime import timedelta

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram.utils import executor

from src.data.chats import database
from src.data.schedule import ScheduleProvider
from src.dialogs.registry import init_dialogs
from src.utils.i18n import i18n
from src.utils.time import current_local_time


# TODO: put admins to .env
admins = [
    926132680,
    423052299
]

bot = Bot(
    token=os.getenv("TEST_TOKEN" if "testing" in sys.argv else "PROD_TOKEN"),
    parse_mode=ParseMode.HTML
)

storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)
schedule = ScheduleProvider()

PASTEBIN_AUTH_TOKEN = os.getenv("PASTEBIN_AUTH_TOKEN")


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

    from src.bot.tasks import mail_task, fetch_task
    asyncio.get_event_loop().create_task(mail_task())
    asyncio.get_event_loop().create_task(fetch_task())

    await schedule.sync_day(current_local_time().weekday())
    await schedule.sync_day((current_local_time() + timedelta(days=1)).weekday())


async def on_bot_destroy(_):
    logging.info("Destroying bot...")

    message = await backup()
    await bot.send_message(926132680, message)
    await bot.send_message(423052299, message)


def on_uncaught_exception(exc_type, value, traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        return sys.__excepthook__(exc_type, value, traceback)
    logging.critical("Unhandled exception", exc_info=(exc_type, value, traceback))


def launch_bot():
    sys.excepthook = on_uncaught_exception
    executor.start_polling(dispatcher, skip_updates=False, on_startup=on_bot_start, on_shutdown=on_bot_destroy)
