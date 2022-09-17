import json


class StringI18n:
    def __init__(self, lang):
        with open(f"{lang}.json", encoding="utf-8") as file:
            self.__messages = json.loads(file.read())

    def string(self, key, **kwargs):
        return self.__messages[key].format(**kwargs)


i18n = StringI18n("ru")


def init_i18n():
    global i18n
    i18n = StringI18n("ru")
