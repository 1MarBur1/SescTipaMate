from typing import Dict

from aiogram.dispatcher.filters.state import State
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Window, DialogManager, ChatEvent, ShowMode, Dialog
from aiogram_dialog.manager.protocols import ManagedDialogAdapterProto
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import *
from aiogram_dialog.widgets.text import Const, Format

from src.data.chats import database
from src.data.schedule import group_name_by_id, id_by_group_name, group_name_exists
from src.dialogs.state import ComposableStatesGroup
from src.utils.i18n import i18n


# TODO:
#   1) close settings before message will become uneditable after 48 hours
#   2) store message ids in database in order not to lose control after restart
class SettingsStates(ComposableStatesGroup):
    main_state = State()
    section_states = {}
    select_states = {}


async def on_start(start_data, dialog_manager: DialogManager):
    chat_id = dialog_manager.event.chat.id
    chat_data = database.get_chat_data(chat_id)
    for i in ("mail", "pin", "news"):
        await dialog_manager.dialog().find(f"settings_{i}").set_checked(dialog_manager.event, chat_data[i])
    dialog_manager.current_context().dialog_data["group"] = group_name_by_id(chat_data["group"])


async def set_group(query: CallbackQuery, button: Button, dialog_manager: DialogManager):
    dialog_manager.current_context().dialog_data["last_query"] = None
    await SettingsStates.group_state.set()
    await dialog_manager.switch_to(SettingsStates.group_state)


async def delete_last_query(last_query):
    if last_query:
        await last_query[1].delete()
        await last_query[0].delete()


async def on_group_send(message: Message, dialog: ManagedDialogAdapterProto, dialog_manager: DialogManager):
    dialog_manager.show_mode = ShowMode.EDIT
    dialog_data = dialog_manager.current_context().dialog_data
    received_group = message.text.strip().upper()

    await delete_last_query(dialog_data["last_query"])
    if group_name_exists(received_group):
        if dialog_data["group"] == received_group:
            answer = await message.answer(i18n.string("settings.group.already_set"))
        else:
            database.set_chat_data(message.chat.id, {"group": id_by_group_name(received_group)})

            prev_group = dialog_data["group"]
            dialog_data["group"] = received_group
            answer = await message.answer(
                i18n.string("settings.group.set", before=prev_group, after=received_group)
            )
    else:
        answer = await message.answer(i18n.string("settings.group.unknown"))
    dialog_data["last_query"] = [message, answer]


async def on_group_done(query: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await delete_last_query(dialog_manager.current_context().dialog_data["last_query"])
    await SettingsStates.main_state.set()
    await dialog_manager.switch_to(SettingsStates.main_state)


async def toggle(option, event: ChatEvent, checkbox: ManagedCheckboxAdapter, dialog_manager: DialogManager):
    chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
    database.set_chat_data(chat_id, {option: checkbox.is_checked()})


async def on_done(query: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await query.message.delete()
    await dialog_manager.done()
    await dialog_manager.data["state"].finish()


async def group_getter(**kwargs):
    return {"group": kwargs["dialog_manager"].current_context().dialog_data["group"]}


class Section(Keyboard):
    def __init__(self, name, *items):
        super().__init__()

        self.name = name
        self.items = items

        state = SettingsStates.register(State())
        SettingsStates.section_states[name] = state

        self.window = Window(*items, state=state)
        self.button = Button(
            Const(f"Section {name}"),
            id="",
            on_click=...
        )

    async def _render_keyboard(self, data: Dict, manager: DialogManager):
        return await self.button.render_keyboard(data, manager)


class Toggle(Checkbox):
    def __init__(self, name, callback=None):
        super().__init__(
            Const(f"Toggle {name} ✅"),
            Const(f"Toggle {name} 🚫"),
            id="",
            on_state_changed=...
        )
        self.name = name


class Select:
    def __init__(self, name, options, callback=None):
        self.name = name

        state = SettingsStates.register(State())
        SettingsStates.select_states[name] = state

        self.button = Button(
            Const(f"Select {name}"),
            id="",
            on_click=...
        )

        self.window = Window(
            Const(f"Select {name}"),
            state=state
        )

    async def _render_keyboard(self, data: Dict, manager: DialogManager):
        return await self.button.render_keyboard(data, manager)


def settings_dialog(*items):
    main_window = Window(
        Const(i18n.string("settings.header")),
        Button(Format(i18n.string("settings.group")), id="settings_group", on_click=set_group),
        *(
            Checkbox(
                Const(i18n.string(f"settings_{i}") + "✅"),
                Const(i18n.string(f"settings_{i}") + "🚫"),
                id=f"settings_{i}",
                on_state_changed=lambda e, c, m, i=i: toggle(i, e, c, m),
            ) for i in ("mail", "pin", "news")
        ),
        Button(Const(i18n.string("settings.done")), id="done", on_click=on_done),
        state=SettingsStates.main_state,
        getter=group_getter,
    )

    group_window = Window(
        Format(i18n.string("settings.group.header")),
        Button(Const(i18n.string("settings.done")), id="group_done", on_click=on_group_done),
        MessageInput(on_group_send, content_types=[ContentType.TEXT]),
        state=SettingsStates.group_state,
        getter=group_getter,
    )

    main_window = Window(
        *(item.render() for item in items),
        state=SettingsStates.main_state
    )

    dialog = Dialog(main_window, group_window)
    dialog.on_start = on_start

    return dialog
