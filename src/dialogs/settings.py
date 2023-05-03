from typing import Dict, List, Any

from aiogram.dispatcher.filters.state import State
from aiogram.types import CallbackQuery
from aiogram_dialog import Window, DialogManager, Dialog
from aiogram_dialog.widgets.kbd import *
from aiogram_dialog.widgets.text import Const, Format

from src.data.chats import database
from src.data.schedule import group_name_by_id
from src.dialogs.state import MutableStatesGroup
from src.utils.i18n import i18n


# TODO:
#   1) close settings before message will become uneditable after 48 hours
#   2) store message ids in database in order not to lose control after restart
class SettingsStates(MutableStatesGroup):
    main_state = State()
    section_states: Dict[Any, State] = {}
    select_states: Dict[Any, State] = {}


class Section:
    def __init__(self, name, *items):
        self.name = f"{name}"
        self.children = items

    def create_state(self):
        state = SettingsStates.register(State(self.name))
        SettingsStates.section_states[self.name] = state

        return state

    def build(self, windows: List[Window], parent: State, path: str):
        path = f"{path}.{self.name}"

        state = self.create_state()

        async def open_window(query: CallbackQuery, button: Button, manager: DialogManager):
            await manager.switch_to(SettingsStates.section_states[self.name])

        async def close_window(query: CallbackQuery, button: Button, manager: DialogManager):
            await manager.dialog().switch_to(parent)

        window = Window(
            Const(i18n.string(f"{path}.header")),
            *[item.build(windows, state, path) for item in self.children],
            Button(
                Const(i18n.string("settings.done")),
                on_click=close_window,
                id=self.name + "return"
            ),
            state=state
        )

        windows.append(window)

        return Button(
            Const(i18n.string(path)),
            on_click=open_window,
            id=self.name
        )


class Select:
    def __init__(self, name, options):
        self.name = name
        self.options = options

    def build(self, windows: List[Window], parent: State, path: str):
        path = f"{path}.{self.name}"

        state = SettingsStates.register(State(self.name))
        SettingsStates.select_states[self.name] = state

        async def open_window(query: CallbackQuery, button: Button, manager: DialogManager):
            await manager.switch_to(SettingsStates.select_states[self.name])

        async def close_window(query: CallbackQuery, button: Button, manager: DialogManager):
            await manager.dialog().switch_to(parent)

        window = Window(
            Format(i18n.string(f"{path}.header")),

            Button(
                Const(i18n.string("settings.done")),
                on_click=close_window,
                id=self.name + "return"
            ),
            state=state
        )

        windows.append(window)

        return Button(
            Format(i18n.string(path)),
            on_click=open_window,
            id=self.name
        )


class Toggle:
    def __init__(self, name, callback=None):
        self.name = name
        self.callback = callback

    def build(self, windows: List[Window], parent: State, path: str):
        path = f"{path}.{self.name}"

        return Checkbox(
            Const(i18n.string(f"{path}.enabled")),
            Const(i18n.string(f"{path}.disabled")),
            id=path,
            on_state_changed=self.callback
        )


async def on_dialog_start(start_data, manager: DialogManager):
    chat_id = manager.event.chat.id
    chat_data = database.get_chat_data(chat_id)

    checkboxes = {"settings.general.news": chat_data["news"],
                  "settings.mail.state": chat_data["mail"],
                  "settings.mail.pin": chat_data["pin"]}
    for key in checkboxes:
        await manager.dialog().find(key).set_checked(manager.event, checkboxes[key])

    dialog_data = manager.current_context().dialog_data
    dialog_data["group"] = group_name_by_id(chat_data["group"])
    dialog_data["lang"] = "ru"


async def on_dialog_end(query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.done()


async def getter(**kwargs):
    dialog_data = kwargs["dialog_manager"].current_context().dialog_data
    return {"group": dialog_data["group"], "lang": dialog_data["lang"]}


def settings_dialog(*items):
    windows = []

    main_window = Window(
        Const(i18n.string("settings.header")),
        *[item.build(windows, SettingsStates.main_state, "settings") for item in items],
        Button(
            Const(i18n.string("settings.done")),
            on_click=on_dialog_end,
            id="rickastley"
        ),
        state=SettingsStates.main_state
    )

    dialog = Dialog(main_window, *windows, getter=getter)
    dialog.on_start = on_dialog_start

    return dialog
