import asyncio
import logging
import time
from datetime import timedelta

from aiogram.utils import exceptions

from src.data.chats import database
from src.utils.formatting import format_diffs, format_schedule
from src.utils.time import everyday_at, current_local_time, every
from src.bot.globals import bot, schedule


@everyday_at("16:00")
async def mail_task():
    # TODO: Mail message welcome
    tomorrow = current_local_time() + timedelta(days=2)

    if tomorrow.weekday() == 6:
        return

    logging.info(f"Ready to send everyday mailing")
    start_time = time.time()

    await schedule.sync_day(tomorrow.weekday())

    tasks = []
    for chat_id in database.joinedChats:
        chat_data = database.get_chat_data(chat_id)
        if chat_data["mail"]:
            tasks.append(asyncio.ensure_future(
                bot.send_message(chat_id, format_schedule(schedule.for_group(chat_data["group"], tomorrow.weekday()),
                                                          tomorrow.strftime("%d.%m.%Y")))
            ))

    success_count = 0
    for result in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(result, exceptions.TelegramAPIError):
            continue
        success_count += 1

    end_time = time.time()
    logging.info(f"Done in {end_time - start_time}s. Sent to {success_count}/{len(database.joinedChats)} users")

    global diff_task
    diff_task = asyncio.create_task(check_diff_task())


@every(timedelta(minutes=1))
async def check_diff_task():
    diffs = await schedule.sync_day(current_local_time().weekday())
    now = current_local_time()
    tasks = []
    for chat_id in database.joinedChats:
        chat_data = database.get_chat_data(chat_id)
        if chat_data["group"] in diffs and chat_data["mail"]:
            tasks.append(asyncio.ensure_future(
                bot.send_message(chat_id, format_diffs())
            ))

    await asyncio.gather(*tasks, return_exceptions=True)


@everyday_at("9:00")
async def stop_diff_task():
    global diff_task
    if diff_task:
        diff_task.cancel()
        diff_task = None


@everyday_at("00:00")
async def fetch_task():
    logging.info(f"Ready to start everyday sync")
    start_time = time.time()

    await schedule.sync_day(current_local_time().weekday())
    await schedule.sync_day((current_local_time() + timedelta(days=1)).weekday())

    end_time = time.time()
    logging.info(f"Done in {end_time - start_time}s")
