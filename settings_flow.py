from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery, ParseMode
from aiogram_dialog import Window, DialogManager, ChatEvent
from aiogram_dialog.widgets.kbd import *
from aiogram_dialog.widgets.text import Const

from stringi18n import i18n
from database import database


class SettingsStateFlow(StatesGroup):
    main_state = State()
    group_state = State()

    @staticmethod
    async def on_start(start_data, dialog_manager: DialogManager):
        chat_id = dialog_manager.event.chat.id
        chat_data = database.get_chat_data(chat_id)
        for i in ("mail", "pin", "news"):
            await dialog_manager.dialog().find(f"settings_{i}").set_checked(dialog_manager.event, chat_data[i])

    @staticmethod
    async def set_group(query: CallbackQuery, button: Button, manager: DialogManager):
        await SettingsStateFlow.group_state.set()
        await manager.switch_to(SettingsStateFlow.group_state)

    @staticmethod
    async def on_group_done(query: CallbackQuery, button: Button, manager: DialogManager):
        await SettingsStateFlow.main_state.set()
        await manager.switch_to(SettingsStateFlow.main_state)

    @staticmethod
    async def toggle_mail(event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
        database.set_chat_data(chat_id, {"mail": checkbox.is_checked()})

    @staticmethod
    async def toggle_pinning(event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
        database.set_chat_data(chat_id, {"pin": checkbox.is_checked()})

    @staticmethod
    async def toggle_news(event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
        database.set_chat_data(chat_id, {"news": checkbox.is_checked()})

    @staticmethod
    async def on_done(query: CallbackQuery, button: Button, manager: DialogManager):
        await manager.done()
        await query.message.delete()

    main_window = Window(
        Const("*Настройки*\nЗдесь можно изменить конфигурацию бота"),
        Button(Const("Класс: {group}"), id="settings_group", on_click=set_group),
        *(
            Checkbox(
                Const(f"{i18n.string(i[0])} ✅"),
                Const(f"{i18n.string(i[0])} 🚫"),
                id=i[0],
                on_state_changed=i[1],
            ) for i in (
                ("settings_mail", toggle_mail),
                ("settings_pin", toggle_pinning),
                ("settings_news", toggle_news)
            )
        ),
        Button(Const("Готово ↩"), id="done", on_click=on_done),
        state=main_state,
        parse_mode=ParseMode.MARKDOWN_V2
    )

    group_window = Window(
        Const(f"*Настройки → Класс*\n*Текущий класс*: {None}\n\nДля выбора класса отправь его в формате '12Я'\n⚠ _Старый класс заменится на новый_"),
        Button(Const("Готово ↩"), id="group_done", on_click=on_group_done),
        state=group_state,
        parse_mode=ParseMode.MARKDOWN_V2
    )
