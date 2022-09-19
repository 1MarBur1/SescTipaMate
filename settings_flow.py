from aiogram import types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery, ParseMode, ContentType
from aiogram_dialog import Window, DialogManager, ChatEvent, ShowMode
from aiogram_dialog.manager.protocols import ManagedDialogAdapterProto
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import *
from aiogram_dialog.widgets.text import Const, Format

from stringi18n import i18n
from database import database
from format_data import groups


class SettingsStateFlow(StatesGroup):
    main_state = State()
    group_state = State()

    @staticmethod
    async def on_start(start_data, dialog_manager: DialogManager):
        chat_id = dialog_manager.event.chat.id
        chat_data = database.get_chat_data(chat_id)
        for i in ("mail", "pin", "news"):
            await dialog_manager.dialog().find(f"settings_{i}").set_checked(dialog_manager.event, chat_data[i])
        start_data = {"group": chat_data["group"]}
        print(start_data["group"])

    @staticmethod
    async def set_group(query: CallbackQuery, button: Button, dialog_manager: DialogManager):
        await SettingsStateFlow.group_state.set()
        await dialog_manager.switch_to(SettingsStateFlow.group_state)

    @staticmethod
    async def on_group_done(query: CallbackQuery, button: Button, dialog_manager: DialogManager):
        await SettingsStateFlow.main_state.set()
        await dialog_manager.switch_to(SettingsStateFlow.main_state)

    @staticmethod
    async def toggle(option, event: ChatEvent, checkbox: ManagedCheckboxAdapter, dialog_manager: DialogManager):
        chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
        database.set_chat_data(chat_id, {option: checkbox.is_checked()})

    @staticmethod
    async def on_done(query: CallbackQuery, button: Button, dialog_manager: DialogManager):
        await query.message.delete()
        await dialog_manager.done()
        await dialog_manager.data["state"].finish()

    @staticmethod
    async def group_getter(**kwargs):
        # event = kwargs["dialog_manager"].event
        # chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
        # return {"group": groups[database.get_chat_data(chat_id)["group"]]}
        return {"group": kwargs["dialog_manager"].current_context().start_data["group"]}

    @staticmethod
    async def on_group_send(message: types.Message, dialog: ManagedDialogAdapterProto, dialog_manager: DialogManager):
        received_group = message.text.strip()
        if received_group in groups.values():
            dialog_manager.current_context().start_data["group"] = received_group
            dialog_manager.show_mode = ShowMode.EDIT
            await message.answer("Класс установлен")
        else:
            await message.answer("Неизвестный класс")

    main_window = Window(
        Const("*Настройки*\nЗдесь можно изменить конфигурацию бота"),
        Button(Format("Класс: {group}"), id="settings_group", on_click=set_group),
        *(
            Checkbox(
                Const(i18n.string(f"settings_{i}") + "✅"),
                Const(i18n.string(f"settings_{i}") + "🚫"),
                id=f"settings_{i}",
                on_state_changed=lambda e, c, m, i=i: SettingsStateFlow.toggle(i, e, c, m),
            ) for i in ("mail", "pin", "news")
        ),
        Button(Const("Готово ↩"), id="done", on_click=on_done),
        state=main_state,
        getter=group_getter,
        parse_mode=ParseMode.MARKDOWN_V2
    )

    group_window = Window(
        Format("*Настройки → Класс*\n*Текущий класс*: {group}\n\nДля выбора класса отправь его в формате '12Я'\n⚠ _Старый класс заменится на новый_"),
        Button(Const("Готово ↩"), id="group_done", on_click=on_group_done),
        MessageInput(on_group_send, content_types=[ContentType.TEXT]),
        state=group_state,
        getter=group_getter,
        parse_mode=ParseMode.MARKDOWN_V2
    )
