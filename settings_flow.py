from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_dialog import Window, DialogManager, ChatEvent
from aiogram_dialog.widgets.kbd import *
from aiogram_dialog.widgets.text import Const

from stringi18n import i18n


class SettingsStateFlow(StatesGroup):
    main = State()
    group = State()

    @staticmethod
    async def set_group(query: CallbackQuery, button: Button, manager: DialogManager):
        await SettingsStateFlow.group.set()
        await manager.switch_to(SettingsStateFlow.group)

    @staticmethod
    async def on_group_done(query: CallbackQuery, button: Button, manager: DialogManager):
        await SettingsStateFlow.main.set()
        await manager.switch_to(SettingsStateFlow.main)

    @staticmethod
    async def toggle_mail(event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        ...

    @staticmethod
    async def toggle_pinning(event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        ...

    @staticmethod
    async def toggle_news(event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        ...

    @staticmethod
    async def on_done(query: CallbackQuery, button: Button, manager: DialogManager):
        await manager.done()
        await query.message.delete()

    main_window = Window(
        Const(i18n.string("settings_welcome")),
        Button(Const(f"Класс: {None}"), id="settings_group", on_click=set_group),
        *(
            Checkbox(
                Const(f"{i18n.string(i[0])} ✅"),
                Const(f"{i18n.string(i[0])} 🚫"),
                id=i[0],
                on_state_changed=i[1],
            ) for i in (
                ("settings_mail", toggle_mail),
                ("settings_pinning", toggle_pinning),
                ("settings_news", toggle_news)
            )
        ),
        Button(Const("Готово ↩️"), id="done", on_click=on_done),
        state=main,
    )

    group_window = Window(
        Const(i18n.string("settings_help")),
        Button(Const("Готово ↩️"), id="group_done", on_click=on_group_done),
        state=group
    )
