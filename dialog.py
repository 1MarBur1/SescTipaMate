import json


class Dialog:
    def __init__(self, lang):
        with open(f"{lang}.json", encoding="utf-8") as file:
            self.__messages = json.loads(file.read())

    def message(self, key, **kwargs):
        return self.__messages[key].format(**kwargs)
