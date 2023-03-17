from aiogram import Dispatcher
from aiogram_dialog import DialogRegistry

from src.bot.globals import SUPPORTED_LANGUAGES
from src.dialogs.settings import settings_dialog, Section, Toggle, Select


def init_dialogs(dispatcher: Dispatcher):
    dialog_registry = DialogRegistry(dispatcher)

    dialog_registry.register(settings_dialog(
        Section(
            "general",
            Select("lang", options=SUPPORTED_LANGUAGES),
            Toggle("news")
        ),
        Section(
            "mail",
            Toggle(""),
            Toggle("pin"),
            Select("group", options=[])
        )
    ))
