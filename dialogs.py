from aiogram import Dispatcher
from aiogram_dialog import DialogRegistry

dialog_registry = None
dialogs = []


def register_dialog(func):
    dialogs.append(func)
    return func


def init_dialogs(dispatcher: Dispatcher):
    global dialog_registry
    dialog_registry = DialogRegistry(dispatcher)

    for dialog_factory in dialogs:
        dialog_registry.register(dialog_factory())
