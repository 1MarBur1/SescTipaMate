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

    @classmethod
    async def set_group(cls, query: CallbackQuery, button: Button, manager: DialogManager):
        await cls.group_state.set()
        await manager.switch_to(cls.group_state)

    @classmethod
    async def on_group_done(cls, query: CallbackQuery, button: Button, manager: DialogManager):
        await cls.main_state.set()
        await manager.switch_to(cls.main_state)

    @classmethod
    async def toggle_mail(cls, event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        ...

    @classmethod
    async def toggle_pinning(cls, event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        ...

    @classmethod
    async def toggle_news(cls, event: ChatEvent, checkbox: ManagedCheckboxAdapter, manager: DialogManager):
        ...

    @classmethod
    async def on_done(cls, query: CallbackQuery, button: Button, manager: DialogManager):
        await manager.done()
        await query.message.delete()

    @classmethod
    def create_main_window(cls, chat_id):
        # TODO: check chat_id exists
        chat_data = database.get_chat_data(chat_id)
        return Window(
            Const("*Настройки*\nЗдесь можно изменить конфигурацию бота"),
            Button(Const(f"Класс: {chat_data[1]}"), id="settings_group", on_click=cls.set_group),
            *(
                Checkbox(
                    Const(f"{i18n.string(i[0])} ✅"),
                    Const(f"{i18n.string(i[0])} 🚫"),
                    id=i[0],
                    on_state_changed=i[1],
                    default=True
                ) for i in (
                    ("settings_mail", cls.toggle_mail),
                    ("settings_pinning", cls.toggle_pinning),
                    ("settings_news", cls.toggle_news)
                )
            ),
            Button(Const("Готово ↩"), id="done", on_click=cls.on_done),
            state=cls.main_state,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    @classmethod
    def create_group_window(cls):
        return Window(
            Const(f"*Настройки → Класс*\n*Текущий класс*: {None}\n\nДля выбора класса отправь его в формате '12Я'\n⚠ _Старый класс заменится на новый_"),
            Button(Const("Готово ↩"), id="group_done", on_click=cls.on_group_done),
            state=cls.group_state,
            parse_mode=ParseMode.MARKDOWN_V2
        )
