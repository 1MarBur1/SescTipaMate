import asyncio
import logging
from asyncio import Task
from datetime import timedelta

from aiogram.utils import exceptions

from src.data.chats import database
from src.data.schedule import Lesson
from src.utils.formatting import format_diffs, format_schedule
from src.utils.time import everyday_at, current_local_time, every
from src.bot.globals import bot, schedule


diff_task: Task

# FIXME: Weekday and strftime we are checking diff for. Need to create `Day` data class
diff_day = ()


@everyday_at("16:00")
async def mail_task():
    # TODO: Mail message welcome
    tomorrow = current_local_time() + timedelta(days=1)

    if tomorrow.weekday() == 6:
        return

    logging.info("Ready to send everyday mailing...")

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

    logging.info(f"Mailing done. Sent to {success_count}/{len(database.joinedChats)} users")

    global diff_task, diff_day
    diff_task = asyncio.get_event_loop().create_task(check_diff_task())
    diff_day = (tomorrow.weekday(), tomorrow.strftime("%d.%m.%Y"))

    logging.info("Checking for diffs started...")

    schedule.week[tomorrow.weekday()].add(Lesson("Math", "310", 32, -1, "Dingol", 1, is_diff=True))
    schedule.week[tomorrow.weekday()].sync_hash[32] = ""


@every(timedelta(minutes=1))
async def check_diff_task():
    diffs_added, diffs_removed = await schedule.sync_day(diff_day[0])
    tasks = []
    for chat_id in database.joinedChats:
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


@everyday_at("9:00")
async def stop_diff_task():
    global diff_task, diff_day
    if diff_task:
        diff_task.cancel()
        diff_task = None
        diff_day = None

    logging.info("Checking for diffs finished!")


@everyday_at("00:00")
async def fetch_task():
    logging.info("Ready to start everyday syncing...")

    await schedule.sync_day(current_local_time().weekday())
    await schedule.sync_day((current_local_time() + timedelta(days=1)).weekday())

    logging.info("Syncing done")
