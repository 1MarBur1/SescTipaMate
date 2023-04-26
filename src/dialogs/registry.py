from aiogram import Dispatcher
from aiogram_dialog import DialogRegistry

from src.dialogs.settings import settings_dialog, Section, Toggle, Select


def init_dialogs(dispatcher: Dispatcher):
    dialog_registry = DialogRegistry(dispatcher)

    from src.bot.globals import SUPPORTED_LANGUAGES
    from src.data.schedule import GROUPS_INVERSE

    dialog_registry.register(settings_dialog(
        Section(
            "general",
            Select("lang", options=SUPPORTED_LANGUAGES),
            Toggle("news")
        ),
        Section(
            "mail",
            Toggle("Test"),
            Toggle("pin"),
            Select("group", options=GROUPS_INVERSE.keys())
        )
    ))
