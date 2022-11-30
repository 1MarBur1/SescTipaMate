import json


class I18nProvider:
    def __init__(self):
        self.messages = {}

        # FIXME: nested "with" context won't work
        self.current_lang = "ru"  # <-- only language yet
        self.lang_context = False

    def __enter__(self):
        self.lang_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__reset_lang()
        self.lang_context = False

    def string(self, key, **kwargs):
        if self.current_lang is None:
            raise ValueError("Language does not exists or not specified")
        lang = self.current_lang

        if not self.lang_context:
            self.__reset_lang()

        class Default(dict):
            def __missing__(self, __key):
                return "{" + __key + "}"

        return self.messages[lang][key].format_map(Default(**kwargs))

    def using_lang(self, lang):
        self.current_lang = lang
        return self

    def __reset_lang(self):
        self.current_lang = "ru"

    def load_lang(self, lang):
        with open(f"../assets/{lang}.json", encoding="utf-8") as file:
            self.messages[lang] = json.loads(file.read())


i18n = I18nProvider()
