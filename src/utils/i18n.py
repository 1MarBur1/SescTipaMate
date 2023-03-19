import json
import logging
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
        path = f"assets/{lang}.json"
        if not os.path.exists(path):
            raise ValueError(f"Localization file for \"{lang}\" language not found")

        with open(path, encoding="utf-8") as file:
            lang_data = json.loads(file.read())

        lang_msg = self.messages[lang] = {}
        stack = [iter(lang_data.items())]
        namespace = []

        while stack:
            try:
                key, value = next(stack[-1])
            except StopIteration:
                stack.pop()
                if len(namespace) > 0:
                    namespace.pop()
                continue

            # TODO: support list as a collection of localized strings for one key
            match value:
                case str():
                    # Value with empty key belongs to upper namespace, so we don't extend it in such case
                    lang_msg[".".join(namespace + [key] if key else [])] = value
                case dict():
                    if not key:
                        logging.warning("Empty key used with dict")
                    stack.append(iter(value.items()))
                    namespace.append(key)


i18n = I18nProvider()
