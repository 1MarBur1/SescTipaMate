class ChatDataStorage:
    def __init__(self):
        with open("ids.txt") as file:
            self.joinedChats = {int(i[0]): [int(i[1]), i[2] == "True", i[3] == "True", int(i[4]), i[5] == "True"]
                                for i in [line.split(",") for line in file.readlines()]}

    def has_chat(self, chat_id):
        return chat_id in self.joinedChats

    def get_chat_data(self, chat_id):
        return self.joinedChats.get(chat_id, [])

    def set_chat_data(self, chat_id, data):
        self.joinedChats[chat_id] = data


database = ChatDataStorage()
