import asyncio
import logging
from asyncio import Task
from datetime import timedelta

from aiogram.utils import exceptions

from src.data.chats import database
from src.utils.formatting import format_diffs, format_schedule
from src.utils.time import everyday, current_local_time, every
from src.bot.globals import bot, schedule


diff_task: Task

# TODO: Weekday and strftime we are checking diff for. Let's create `Day` data class
diff_day = ()


@everyday("16:00")
async def mail_task():
    tomorrow = current_local_time() + timedelta(days=1)

    if tomorrow.weekday() == 6:
        return

    logging.debug("Ready to send everyday mailing...")

    await schedule.sync_day(tomorrow.weekday())

    tasks = []
    for chat_id in database.joined_chats:
        chat_data = database.get_chat_data(chat_id)
        if chat_data["mail"] and chat_data["group"] != 0:
            tasks.append(asyncio.ensure_future(
                bot.send_message(chat_id, format_schedule(schedule.for_group(chat_data["group"], tomorrow.weekday()),
                                                          tomorrow.strftime("%d.%m.%Y")))
            ))

    success_count = 0
    for result in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(result, exceptions.TelegramAPIError):
            continue
        success_count += 1

    logging.debug(f"Mailing done. Sent to {success_count}/{len(database.joined_chats)} users")

    global diff_task, diff_day
    diff_task = asyncio.get_event_loop().create_task(check_diff_task())
    diff_day = (tomorrow.weekday(), tomorrow.strftime("%d.%m.%Y"))

    logging.debug("Checking for diffs started...")


@every(timedelta(minutes=5))
async def check_diff_task():
    diffs_added, diffs_removed = await schedule.sync_day(diff_day[0])
    tasks = []
    for chat_id in database.joined_chats:
        chat_data = database.get_chat_data(chat_id)
        group = chat_data["group"]
        if (diffs_added.for_group(group) or diffs_removed.for_group(group)) and chat_data["mail"]:
            diffs = format_diffs(
                schedule.for_group(group, diff_day[0]),
                diffs_added.for_group(group),
                diffs_removed.for_group(group),
                diff_day[1]
            )
            tasks.append(asyncio.ensure_future(bot.send_message(chat_id, diffs)))

    await asyncio.gather(*tasks, return_exceptions=True)


@everyday("9:00")
async def stop_diff_task():
    global diff_task, diff_day
    if diff_task:
        diff_task.cancel()
        diff_task = None
        diff_day = None

    logging.debug("Checking for diffs finished!")


@everyday("00:00")
async def fetch_task():
    logging.debug("Ready to start everyday syncing...")

    await schedule.sync_day(current_local_time().weekday())
    await schedule.sync_day((current_local_time() + timedelta(days=1)).weekday())

    logging.debug("Syncing done")
