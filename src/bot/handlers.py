import logging
from datetime import timedelta

from aiogram.types import Message
from aiogram.utils import exceptions
from aiogram_dialog import DialogManager, StartMode

from src.data.chats import database
from src.dialogs.settings import SettingsStates
from src.utils.formatting import format_schedule
from src.utils.i18n import i18n
from src.utils.time import current_local_time

from src.bot.globals import dispatcher, schedule, bot, backup, admins


@dispatcher.message_handler(commands=["start"])
async def send_welcome(message: Message):
    chat_id = message.chat.id
    if not database.has_chat(chat_id):
        database.set_chat_data(chat_id, {"group": 0, "mail": True, "pin": False, "pinned_message": -1, "news": True})
        await message.reply(i18n.string("welcome", name=message.chat.first_name))
    else:
        await message.reply(i18n.string(
            "group_already_registered" if chat_id < 0 else "user_already_registered"
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
    await message.reply("Nothing here yet...")


@dispatcher.message_handler(commands=["auditories"])
async def send_audiences(message: Message):
    with open("../assets/auditories.png", mode="rb") as image:
        await message.reply_photo(image)


async def send_schedule_for_day(message: Message, date):
    chat_id = message.chat.id
    if database.has_chat(chat_id):
        chat_data = database.get_chat_data(chat_id)

        if len(message.text.split(' ')) == 1:
            group_id = chat_data["group"]
        else:
            group_id = message.text.split(' ')[1]

        if group_id != 0:
            await message.reply(
                format_schedule(schedule.for_group(group_id, date.weekday()), date.strftime("%d.%m.%Y")))
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


@dispatcher.message_handler(commands=["admin"])
async def send_admin_log(message: Message):
    if message.chat.id in admins:
        await message.reply(await backup())
    else:
        with open("../assets/rickroll.gif", mode="rb") as rickroll:
            await message.reply_animation(rickroll)
