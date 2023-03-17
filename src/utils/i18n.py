import json
import os


class I18nProvider:
    def __init__(self):
        self.messages = {}
        self.current_lang = "ru"

    def string(self, key, **kwargs):
        class Default(dict):
            def __missing__(self, __key):
                return "{" + __key + "}"

        return self.messages[self.current_lang][key].format_map(Default(**kwargs))

    def use_lang(self, lang):
        if lang not in self.messages:
            raise ValueError(f"Language {lang} does not exists or not loaded")

        self.current_lang = lang
        return self

    def load_lang(self, lang):
        path = f"../assets/{lang}.json"
        if not os.path.exists(path):
            raise ValueError(f"Localization file for \"{lang}\" language not found")

        with open(path, encoding="utf-8") as file:
            self.messages[lang] = json.loads(file.read())


i18n = I18nProvider()
